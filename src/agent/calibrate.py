"""How good is the confidence score? Coverage and accuracy per threshold, on dev.

    python -m src.agent.calibrate --run experiments/e2_copy

Two scores are compared: "mean" (geometric mean of the chosen token probabilities)
and "min" (probability of the least likely token). For each threshold t:
coverage = share of dev calls with confidence >= t (the agent runs them without
asking), accuracy = exact match among those calls, and among the ones it asks about.
Also reports AUROC: how well the score ranks right calls above wrong ones.
Saved to <run>/calibration.json. Pick the threshold on dev only.
"""

import argparse
import json
from pathlib import Path

from sklearn.metrics import roc_auc_score

from src.agent.predictor import Predictor
from src.data.dataset import load_split
from src.training.metrics import safe_parse

THRESHOLDS = [0.0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 0.99]
KINDS = ("mean", "min")


def same_call(pred: str, gold: str) -> bool:
    """Exact match as in metrics: same intent and same multiset of arguments."""
    p, g = safe_parse(pred), safe_parse(gold)
    return p is not None and p[0] == g[0] and sorted(p[1]) == sorted(g[1])


def auroc(scored: list[tuple[float, bool]]) -> float:
    """Probability that a random right call has a higher score than a random wrong one (ties count half)."""
    labels = [ok for _, ok in scored]
    if all(labels) or not any(labels):
        return float("nan")
    return float(roc_auc_score(labels, [c for c, _ in scored]))


def threshold_table(scored: list[tuple[float, bool]]) -> list[dict]:
    table = []
    for t in THRESHOLDS:
        kept = [ok for conf, ok in scored if conf >= t]
        asked = [ok for conf, ok in scored if conf < t]
        table.append({"threshold": t, "coverage": len(kept) / len(scored),
                      "accuracy_kept": sum(kept) / len(kept) if kept else None,
                      "accuracy_asked": sum(asked) / len(asked) if asked else None})
    return table


def calibrate(run_dir: Path, limit: int | None = None, batch_size: int = 256, device: str = "auto") -> dict:
    """{kind: {"auroc": float, "table": [...]}} for kind in KINDS."""
    out = {}
    for kind in KINDS:
        predictor = Predictor.from_run(run_dir, device, confidence=kind)
        data = predictor.cfg["data"]
        rows = load_split(data["data_dir"], data["locales"], "dev")[:limit]
        scored = []
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i + batch_size]
            preds = predictor.predict([r["utt"] for r in chunk], [r["locale"] for r in chunk])
            scored += [(p.confidence, same_call(p.call, r["call"])) for p, r in zip(preds, chunk)]
        out[kind] = {"auroc": auroc(scored), "table": threshold_table(scored)}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    result = calibrate(args.run, args.limit, device=args.device)
    if args.limit is None:
        (args.run / "calibration.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    f = lambda x: f"{100 * x:6.1f}%" if x is not None else "      -"
    print("AUROC  " + "   ".join(f"{k}: {result[k]['auroc']:.3f}" for k in KINDS))
    print(f"{'':>9} " + " | ".join(f"{k + ': coverage, EM kept, EM asked':^30}" for k in KINDS))
    for i, t in enumerate(THRESHOLDS):
        cells = [result[k]["table"][i] for k in KINDS]
        print(f"{t:>9} " + " | ".join(f"{f(c['coverage'])} {f(c['accuracy_kept'])} {f(c['accuracy_asked'])}  "
                                     for c in cells))


if __name__ == "__main__":
    main()
