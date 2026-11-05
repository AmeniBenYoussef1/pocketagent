"""Everything the Results page shows, read from experiments/ (nothing hard-coded).

Cached until one of the files it reads changes.
"""

import json
from collections import Counter
from pathlib import Path

from src.training.errors import CATEGORIES, classify
from src.training.evaluate import predictions_path, read_jsonl

# run folder -> (label, group). The ladder is the order of the comparison chart.
RUNS = {
    "b0_retrieval/char": ("B0", "ladder"),
    "e0_lstm": ("E0", "ladder"),
    "e1_attn": ("E1", "ladder"),
    "e2_copy": ("E2", "ladder"),
    "e2_copy_beam3": ("E2 + beam 3", "ladder"),
    "e2_copy_beam5": ("E2 + beam 5", "decoding"),
    "e2_copy_beam10": ("E2 + beam 10", "decoding"),
    "e7_copy_en_beam3": ("E7 EN only + beam 3", "per_locale"),
    "e7_copy_fr_beam3": ("E7 FR only + beam 3", "per_locale"),
    "e7_copy_ar_beam3": ("E7 AR only + beam 3", "per_locale"),
}
METRICS = {"exact_match": "em", "exact_match_strict": "em_strict", "intent_accuracy": "intent",
           "slot_f1": "slot_f1", "valid_call_rate": "valid", "macro_exact_match": "macro_em"}
LOCALES = ["overall", "en-US", "fr-FR", "ar-SA"]
_cache: dict = {}


def _dev_runs(exp_dir: Path) -> list[str]:
    return [r for r in RUNS if (exp_dir / r / "metrics.json").exists()
            and json.loads((exp_dir / r / "metrics.json").read_text(encoding="utf-8"))["split"] == "dev"]


def _signature(exp_dir: Path, runs: list[str]) -> tuple:
    files = [exp_dir / r / "metrics.json" for r in runs] + [exp_dir / r / "history.json" for r in runs]
    files.append(exp_dir / "e2_copy" / "calibration.json")
    return tuple((str(f), f.stat().st_mtime) for f in files if f.exists())


def _history(exp_dir: Path, run: str) -> list[dict] | None:
    path = exp_dir / run / "history.json"
    if not path.exists():
        return None
    epochs = json.loads(path.read_text(encoding="utf-8"))["epochs"]
    return [{"epoch": e["epoch"], "train_loss": e["train_loss"], "dev_loss": e["eval_loss"],
             "dev_em": e["eval_em"], "train_seconds": e["train_seconds"]} for e in epochs]


def build_results(exp_dir: Path) -> dict:
    exp_dir = Path(exp_dir)
    runs = _dev_runs(exp_dir)
    sig = _signature(exp_dir, runs)
    if _cache.get("sig") == sig:
        return _cache["value"]

    out = {"locales": LOCALES, "error_categories": CATEGORIES[1:], "runs": []}
    for run in runs:
        label, group = RUNS[run]
        m = json.loads((exp_dir / run / "metrics.json").read_text(encoding="utf-8"))
        metrics = {loc: {short: r[k] for k, short in METRICS.items()} for loc, r in m["results"].items()}
        preds = read_jsonl(predictions_path(exp_dir / run, "dev"))
        counts = Counter(classify(p["pred"], p["gold"]) for p in preds)
        errors = {c: counts[c] / len(preds) for c in CATEGORIES[1:]}
        decode = exp_dir / run / "decode.json"
        out["runs"].append({
            "id": run, "label": label, "group": group, "metrics": metrics, "seen_unseen": m["seen_unseen"],
            "errors": errors, "history": _history(exp_dir, run),
            "decode": json.loads(decode.read_text(encoding="utf-8")) if decode.exists() else None,
        })
    calib = exp_dir / "e2_copy" / "calibration.json"
    out["calibration"] = json.loads(calib.read_text(encoding="utf-8")) if calib.exists() else None
    _cache.update(sig=sig, value=out)
    return out
