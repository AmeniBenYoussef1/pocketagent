"""Train a seq2seq model from a YAML config.

    python -m src.training.train --config configs/e0_lstm.yaml

Each epoch: teacher-forced training, dev loss, greedy decoding of dev and dev
exact match. The best epoch on dev EM is kept (early stopping on dev only, the
test split is never read). Outputs go to experiments/<name>/:

    config.yaml, vocab_src.json, vocab_tgt.json, model.pt (git-ignored),
    history.json (losses, dev EM, seconds per epoch), curves.png,
    predictions_<split>.jsonl.gz, metrics.json, samples.md

With data.overfit_n set, the model trains on that many random train examples
and is evaluated on the same examples (split "train"), to check it can learn.
"""

import argparse
import json
import random
import shutil
import time
from pathlib import Path

import numpy as np
import torch
import yaml
from matplotlib.figure import Figure
from torch import nn

from src.data.dataset import MAX_GEN_LEN, MassiveDataset, load_split, make_loader
from src.data.vocab import PAD_ID, build_vocabs
from src.inference.beam import beam_search
from src.inference.greedy import greedy_decode, ids_to_calls
from src.models.seq2seq import Seq2Seq
from src.training.evaluate import evaluate_run, format_table, write_jsonl
from src.training.metrics import build_schema, compute_metrics


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def get_device(name: str) -> torch.device:
    if name == "auto":
        name = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.device(name)


def build_model(cfg: dict, n_src: int, n_tgt: int) -> nn.Module:
    m = cfg["model"]
    if m["type"] == "lstm":
        return Seq2Seq(n_src, n_tgt, m["emb_dim"], m["hidden_dim"], m["num_layers"], m["dropout"])
    if m["type"] in ("attn", "copy"):
        from src.models.attention_seq2seq import AttnSeq2Seq
        from src.models.copy import CopySeq2Seq
        cls = AttnSeq2Seq if m["type"] == "attn" else CopySeq2Seq
        return cls(n_src, n_tgt, m["emb_dim"], m["hidden_dim"], m["num_layers"],
                   m["dropout"], m.get("attn_dim", m["hidden_dim"]))
    raise ValueError(f"unknown model type {m['type']!r}")


def forward_batch(model, batch: dict, device, tgt_vocab) -> tuple[torch.Tensor, torch.Tensor]:
    """Teacher-forced scores and the tokens they must predict.

    returns scores (B, T_tgt - 1, V') and tgt_out (B, T_tgt - 1), where V' = V_tgt,
    or V_tgt + n_oov for the copy model (its targets use extended ids).
    """
    src = batch["src"].to(device)  # (B, T_src)
    if getattr(model, "uses_copy", False):
        from src.models.copy import extend_batch
        ext = extend_batch(batch, tgt_vocab)
        tgt = ext["tgt_ext"].to(device)  # (B, T_tgt)
        scores = model(src, batch["src_lens"], tgt[:, :-1], ext["src_ext"].to(device), ext["n_oov"])
    else:
        tgt = batch["tgt"].to(device)  # (B, T_tgt)
        scores = model(src, batch["src_lens"], tgt[:, :-1])  # input <SOS> y1 .. yn
    return scores, tgt[:, 1:]  # target y1 .. yn <EOS>, shifted by one


def train_epoch(model, loader, optimizer, loss_fn, device, clip: float, tgt_vocab) -> float:
    """One pass over the train loader. Returns the mean loss per target token."""
    model.train()
    total, n_tokens = 0.0, 0
    for batch in loader:
        logits, tgt_out = forward_batch(model, batch, device, tgt_vocab)  # (B, T-1, V'), (B, T-1)
        loss_sum = loss_fn(logits.reshape(-1, logits.size(-1)), tgt_out.reshape(-1))
        n = int((tgt_out != PAD_ID).sum())

        optimizer.zero_grad()
        (loss_sum / n).backward()
        nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        total += loss_sum.item()
        n_tokens += n
    return total / n_tokens


@torch.no_grad()
def eval_loss(model, loader, loss_fn, device, tgt_vocab) -> float:
    """Teacher-forced loss per target token, dropout off."""
    model.eval()
    total, n_tokens = 0.0, 0
    for batch in loader:
        logits, tgt_out = forward_batch(model, batch, device, tgt_vocab)
        total += loss_fn(logits.reshape(-1, logits.size(-1)), tgt_out.reshape(-1)).item()
        n_tokens += int((tgt_out != PAD_ID).sum())
    return total / n_tokens


@torch.no_grad()
def predict(model, loader, tgt_vocab, device, max_len: int = MAX_GEN_LEN, beam_size: int = 1,
            alpha: float = 0.6) -> list[dict]:
    """Decode every batch (greedy, or beam search if beam_size > 1, with length penalty alpha).

    One row per example with id, locale, utt, gold, pred.
    """
    model.eval()
    rows = []
    for batch in loader:
        kwargs, oovs = {}, None
        if getattr(model, "uses_copy", False):
            from src.models.copy import extend_batch
            ext = extend_batch(batch, tgt_vocab)
            kwargs, oovs = {"src_ext": ext["src_ext"].to(device), "n_oov": ext["n_oov"]}, ext["oovs"]
        src = batch["src"].to(device)
        if beam_size > 1:
            ids = beam_search(model, src, batch["src_lens"], beam_size, max_len, alpha, **kwargs)
        else:
            ids = greedy_decode(model, src, batch["src_lens"], max_len, **kwargs)
        for i, pred in enumerate(ids_to_calls(ids, tgt_vocab, oovs)):
            rows.append({"id": batch["id"][i], "locale": batch["locale"][i], "utt": batch["utt"][i],
                         "gold": batch["call"][i], "pred": pred})
    return rows


def plot_curves(history: list[dict], path: Path) -> None:
    # Figure instead of pyplot: no backend needed, and importing this module
    # doesn't change the plotting backend of a notebook
    epochs = [h["epoch"] for h in history]
    fig = Figure(figsize=(11, 4))
    ax1, ax2 = fig.subplots(1, 2)
    ax1.plot(epochs, [h["train_loss"] for h in history], label="train")
    ax1.plot(epochs, [h["eval_loss"] for h in history], label="eval")
    ax1.set(xlabel="epoch", ylabel="loss per token", title="Loss")
    ax1.legend()
    ax2.plot(epochs, [100 * h["eval_em"] for h in history])
    ax2.set(xlabel="epoch", ylabel="exact match (%)", title="Eval exact match (greedy)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)


def write_samples(path: Path, preds: list[dict], n_hits: int = 5, n_misses: int = 10) -> None:
    lines = ["# Samples", ""]
    for loc in dict.fromkeys(p["locale"] for p in preds):
        rows = [p for p in preds if p["locale"] == loc]
        for title, keep, n in [("hits", True, n_hits), ("misses", False, n_misses)]:
            chosen = [p for p in rows if (p["pred"] == p["gold"]) == keep][:n]
            lines += [f"## {loc} {title}", "", "| utterance | gold | pred |", "|---|---|---|"]
            lines += [f"| {p['utt']} | `{p['gold']}` | `{p['pred']}` |" for p in chosen]
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    data_cfg, train_cfg = cfg["data"], cfg["train"]

    run_dir = Path("experiments") / cfg["name"]
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(args.config, run_dir / "config.yaml")
    set_seed(cfg["seed"])
    device = get_device(cfg.get("device", "auto"))

    all_train = load_split(data_cfg["data_dir"], data_cfg["locales"], "train")
    src_vocab, tgt_vocab = build_vocabs(all_train, data_cfg["min_freq"])
    src_vocab.save(run_dir / "vocab_src.json")
    tgt_vocab.save(run_dir / "vocab_tgt.json")

    if data_cfg.get("overfit_n"):
        train_rows = random.Random(cfg["seed"]).sample(all_train, data_cfg["overfit_n"])
        eval_rows, eval_split = train_rows, "train"
    else:
        train_rows = all_train
        eval_rows, eval_split = load_split(data_cfg["data_dir"], data_cfg["locales"], "dev"), "dev"

    ds_args = dict(max_src_len=data_cfg["max_src_len"], max_tgt_len=data_cfg["max_tgt_len"],
                   lang_tag=data_cfg["lang_tag"])
    train_ds = MassiveDataset(train_rows, src_vocab, tgt_vocab, drop_long_targets=True, **ds_args)
    eval_ds = MassiveDataset(eval_rows, src_vocab, tgt_vocab, **ds_args)
    train_loader = make_loader(train_ds, train_cfg["batch_size"], shuffle=True, seed=cfg["seed"])
    eval_loader = make_loader(eval_ds, train_cfg["eval_batch_size"], shuffle=False)
    schema = build_schema(all_train)

    model = build_model(cfg, len(src_vocab), len(tgt_vocab)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=train_cfg["lr"])
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_ID, reduction="sum")  # on log-probs (copy model) this is exactly the NLL
    n_params = sum(p.numel() for p in model.parameters())
    gpu = torch.cuda.get_device_name(device) if device.type == "cuda" else None
    print(f"{cfg['name']}: {n_params / 1e6:.2f}M params on {device} {gpu or ''}")
    print(f"train {len(train_ds)} (dropped {train_ds.n_dropped} long targets), eval {len(eval_ds)} ({eval_split})")

    history, best_em, best_epoch, bad_epochs = [], -1.0, 0, 0
    patience = train_cfg.get("patience")
    for epoch in range(1, train_cfg["epochs"] + 1):
        t0 = time.perf_counter()
        train_loss = train_epoch(model, train_loader, optimizer, loss_fn, device, train_cfg["clip"], tgt_vocab)
        train_time = time.perf_counter() - t0
        t1 = time.perf_counter()
        ev_loss = eval_loss(model, eval_loader, loss_fn, device, tgt_vocab)
        preds = predict(model, eval_loader, tgt_vocab, device)
        em = compute_metrics([p["pred"] for p in preds], [p["gold"] for p in preds], schema)["exact_match"]
        eval_time = time.perf_counter() - t1
        history.append({"epoch": epoch, "train_loss": train_loss, "eval_loss": ev_loss, "eval_em": em,
                        "train_seconds": round(train_time, 2), "eval_seconds": round(eval_time, 2)})
        print(f"epoch {epoch:3d}  train {train_loss:.4f}  eval {ev_loss:.4f}  EM {100 * em:5.1f}%  "
              f"({train_time:.1f}s train, {eval_time:.1f}s eval)", flush=True)

        if em > best_em:
            best_em, best_epoch, bad_epochs = em, epoch, 0
            torch.save(model.state_dict(), run_dir / "model.pt")
        else:
            bad_epochs += 1
            if patience and bad_epochs >= patience:
                print(f"early stop: no dev EM gain for {patience} epochs")
                break

    info = {"device": str(device), "gpu": gpu, "n_params": n_params, "best_epoch": best_epoch,
            "best_eval_em": best_em, "eval_split": eval_split, "epochs": history}
    (run_dir / "history.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    plot_curves(history, run_dir / "curves.png")

    model.load_state_dict(torch.load(run_dir / "model.pt", map_location=device))
    preds = predict(model, eval_loader, tgt_vocab, device)
    write_jsonl(run_dir / f"predictions_{eval_split}.jsonl.gz", preds)
    write_samples(run_dir / "samples.md", preds)
    out = evaluate_run(run_dir, data_cfg["data_dir"], eval_split)
    print(f"\nbest epoch {best_epoch} ({eval_split})")
    print(format_table(out["results"]))


if __name__ == "__main__":
    main()
