"""Score a run's predictions and write metrics.json.

    python -m src.training.evaluate --run experiments/<run_name>

Reads <run>/predictions_<split>.jsonl.gz (or .jsonl), one row per example with at
least id, locale, gold, pred, and writes <run>/metrics.json with overall and
per-locale results. The schema and n_train come from the train split.

Seen vs unseen: an example is "seen" if its utterance appears verbatim in the
train split of the same locale. EM, intent accuracy and slot F1 are reported on
both subsets.
"""

import argparse
import gzip
import io
import json
from pathlib import Path

from src.data.dataset import load_split
from src.training.metrics import build_schema, compute_metrics, evaluate_by_locale, train_intent_counts

HEADLINE = ["exact_match", "exact_match_strict", "intent_accuracy", "slot_f1",
            "valid_call_rate", "macro_intent_f1", "macro_exact_match", "macro_slot_f1"]
SUBSET_KEYS = ["exact_match", "intent_accuracy", "slot_f1"]


def _open(path: Path, mode: str):
    path = Path(path)
    if path.suffix == ".gz":
        # mtime=0 so the same predictions always give the same bytes
        return io.TextIOWrapper(gzip.GzipFile(path, mode + "b", mtime=0), encoding="utf-8", newline="\n")
    return path.open(mode, encoding="utf-8", newline="\n")


def read_jsonl(path: Path) -> list[dict]:
    with _open(path, "r") as f:
        return [json.loads(line) for line in f]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with _open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def predictions_path(run_dir: Path, split: str) -> Path:
    """predictions_<split>.jsonl.gz if it exists, else predictions_<split>.jsonl."""
    gz = Path(run_dir) / f"predictions_{split}.jsonl.gz"
    return gz if gz.exists() else Path(run_dir) / f"predictions_{split}.jsonl"


def subset_scores(preds: list[dict], schema: dict) -> dict:
    """EM, intent accuracy and slot F1 on a subset (None if it is empty)."""
    if not preds:
        return {"n": 0, **{k: None for k in SUBSET_KEYS}}
    r = compute_metrics([p["pred"] for p in preds], [p["gold"] for p in preds], schema)
    return {"n": r["n"], **{k: r[k] for k in SUBSET_KEYS}}


def seen_unseen(preds: list[dict], seen: list[bool], schema: dict) -> dict:
    """Subset scores overall and per locale."""
    groups = {"overall": list(range(len(preds)))}
    for loc in dict.fromkeys(p["locale"] for p in preds):
        groups[loc] = [i for i, p in enumerate(preds) if p["locale"] == loc]
    return {
        name: {
            "seen": subset_scores([preds[i] for i in idx if seen[i]], schema),
            "unseen": subset_scores([preds[i] for i in idx if not seen[i]], schema),
        }
        for name, idx in groups.items()
    }


def evaluate_run(run_dir: Path, data_dir: Path, split: str = "dev") -> dict:
    """Compute metrics for a run's predictions and save metrics.json."""
    preds = read_jsonl(predictions_path(run_dir, split))
    locales = list(dict.fromkeys(p["locale"] for p in preds))
    train = {loc: load_split(data_dir, [loc], "train") for loc in locales}
    schema = build_schema([r for rows in train.values() for r in rows])
    n_train = {loc: train_intent_counts(rows) for loc, rows in train.items()}

    # utterances come from the data, not the predictions file
    utt = {(r["locale"], r["id"]): r["utt"] for r in load_split(data_dir, locales, split)}
    train_utts = {loc: {r["utt"] for r in rows} for loc, rows in train.items()}
    seen = [utt[(p["locale"], p["id"])] in train_utts[p["locale"]] for p in preds]

    results = evaluate_by_locale(
        [p["pred"] for p in preds], [p["gold"] for p in preds],
        [p["locale"] for p in preds], schema, n_train)
    out = {"split": split, "results": results, "seen_unseen": seen_unseen(preds, seen, schema)}
    (Path(run_dir) / "metrics.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def _pct(x: float | None) -> str:
    return f"{'-':>10}" if x is None else f"{100 * x:>9.1f}%"


def format_table(results: dict) -> str:
    """Headline metrics as percentages, one row per locale."""
    short = ["EM", "EM strict", "intent", "slot F1", "valid", "mF1 int", "mEM", "mF1 slot"]
    lines = [f"{'':<8}" + "".join(f"{s:>10}" for s in short)]
    for name, r in results.items():
        lines.append(f"{name:<8}" + "".join(_pct(r[k]) for k in HEADLINE))
    return "\n".join(lines)


def format_seen_unseen(su: dict) -> str:
    """EM / intent / slot F1 on seen and unseen utterances, one row per locale."""
    lines = [f"{'':<8}{'n seen':>8}{'EM':>10}{'intent':>10}{'slot F1':>10}"
             f"{'n unseen':>10}{'EM':>10}{'intent':>10}{'slot F1':>10}"]
    for name, parts in su.items():
        s, u = parts["seen"], parts["unseen"]
        lines.append(f"{name:<8}{s['n']:>8}" + "".join(_pct(s[k]) for k in SUBSET_KEYS)
                     + f"{u['n']:>10}" + "".join(_pct(u[k]) for k in SUBSET_KEYS))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--split", default="dev")
    parser.add_argument("--data-dir", type=Path, default=Path("data/massive"))
    args = parser.parse_args()
    out = evaluate_run(args.run, args.data_dir, args.split)
    print(f"{args.run} ({args.split})")
    print(format_table(out["results"]))
    print("\nseen = utterance appears verbatim in train (same locale)")
    print(format_seen_unseen(out["seen_unseen"]))


if __name__ == "__main__":
    main()
