"""Re-decode a trained run with greedy or beam search and score it.

    python -m src.inference.decode_run --run experiments/e2_copy --beam 5

Loads config, vocabularies and model.pt of the run, decodes the dev split and
saves predictions + metrics in experiments/<run>_beam<k>/ (or _greedy), so the
original run is untouched. Choose beam size and alpha on dev; --split test is only
for the final evaluation of an already chosen setup.
"""

import argparse
import json
import time
from pathlib import Path

import torch
import yaml

from src.data.dataset import MAX_GEN_LEN, MassiveDataset, load_split, make_loader
from src.data.vocab import Vocab
from src.training.evaluate import evaluate_run, format_seen_unseen, format_table, write_jsonl
from src.training.train import build_model, get_device, predict


def decode_run(run_dir: Path, beam_size: int, alpha: float = 0.6, split: str = "dev",
               limit: int | None = None, device_name: str = "auto", out_dir: Path | None = None) -> Path:
    """Decode run_dir's best model and write a new run folder (out_dir, or <run>_beam<k>). Returns its path."""
    run_dir = Path(run_dir)
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    data_cfg = cfg["data"]
    device = get_device(device_name)
    src_vocab, tgt_vocab = Vocab.load(run_dir / "vocab_src.json"), Vocab.load(run_dir / "vocab_tgt.json")
    model = build_model(cfg, len(src_vocab), len(tgt_vocab)).to(device)
    model.load_state_dict(torch.load(run_dir / "model.pt", map_location=device))

    rows = load_split(data_cfg["data_dir"], data_cfg["locales"], split)
    if limit:
        rows = rows[:limit]
    ds = MassiveDataset(rows, src_vocab, tgt_vocab, max_src_len=data_cfg["max_src_len"],
                        max_tgt_len=data_cfg["max_tgt_len"], lang_tag=data_cfg["lang_tag"])
    # beam search multiplies the batch by beam_size
    loader = make_loader(ds, max(1, cfg["train"]["eval_batch_size"] // beam_size), shuffle=False)

    t0 = time.perf_counter()
    preds = predict(model, loader, tgt_vocab, device, MAX_GEN_LEN, beam_size=beam_size, alpha=alpha)
    seconds = time.perf_counter() - t0

    out_dir = Path(out_dir) if out_dir else run_dir.parent / f"{run_dir.name}_{'greedy' if beam_size == 1 else f'beam{beam_size}'}"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / f"predictions_{split}.jsonl.gz", preds)
    info = {"source_run": str(run_dir), "beam_size": beam_size, "alpha": alpha, "split": split,
            "n": len(preds), "decode_seconds": round(seconds, 1), "device": str(device)}
    (out_dir / "decode.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    if limit is None:
        out = evaluate_run(out_dir, data_cfg["data_dir"], split)
        print(f"{out_dir} ({split}), {seconds:.1f}s on {device}")
        print(format_table(out["results"]))
        print(format_seen_unseen(out["seen_unseen"]))
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--beam", type=int, default=5, help="1 = greedy")
    parser.add_argument("--alpha", type=float, default=0.6, help="length penalty: score / length ** alpha")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--limit", type=int, default=None, help="decode only the first N rows (quick check)")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", type=Path, default=None, help="output folder (default <run>_beam<k>)")
    args = parser.parse_args()
    decode_run(args.run, args.beam, args.alpha, args.split, args.limit, args.device, args.out)


if __name__ == "__main__":
    main()
