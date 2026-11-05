"""B0: retrieval baseline.

For each utterance, find the most similar train utterance of the same locale
(TF-IDF, cosine similarity) and return its call as is. Values are therefore
copied from another utterance, so B0 mostly measures how far intent and call
shape can go without generation.

    python -m src.baselines.retrieval --config configs/b0_retrieval.yaml

Each variant in the config is saved as its own run in experiments/<name>/<variant>/,
and summary.json names the best variant on dev.
"""

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data.converter import tokenize
from src.data.dataset import load_split
from src.training.evaluate import HEADLINE, evaluate_run, format_seen_unseen, format_table, write_jsonl


class TfidfRetriever:
    """Nearest train utterance by TF-IDF cosine similarity."""

    def __init__(self, analyzer: str, ngram_range: tuple[int, int], sublinear_tf: bool = True):
        kwargs = {"tokenizer": tokenize, "token_pattern": None} if analyzer == "word" else {}
        self.vectorizer = TfidfVectorizer(
            analyzer=analyzer, ngram_range=tuple(ngram_range), sublinear_tf=sublinear_tf, **kwargs)

    def fit(self, utts: list[str]) -> "TfidfRetriever":
        self.train_matrix = self.vectorizer.fit_transform(utts)  # (N_train, V), rows L2-normalized
        return self

    def nearest(self, utts: list[str], batch_size: int = 512) -> tuple[np.ndarray, np.ndarray]:
        """Index and similarity of the nearest train utterance. Ties go to the lowest index."""
        query = self.vectorizer.transform(utts)  # (N, V)
        idx, sim = [], []
        for start in range(0, query.shape[0], batch_size):
            sims = (query[start:start + batch_size] @ self.train_matrix.T).toarray()  # (b, N_train)
            best = sims.argmax(axis=1)  # first max, so lowest index on ties
            idx.append(best)
            sim.append(sims[np.arange(len(best)), best])
        return np.concatenate(idx), np.concatenate(sim)


def predict(train_rows: list[dict], eval_rows: list[dict], variant: dict, sublinear_tf: bool) -> list[dict]:
    """One retriever per locale. Returns one prediction row per eval row."""
    preds = []
    for loc in dict.fromkeys(r["locale"] for r in eval_rows):
        train = [r for r in train_rows if r["locale"] == loc]
        evals = [r for r in eval_rows if r["locale"] == loc]
        retriever = TfidfRetriever(variant["analyzer"], variant["ngram_range"], sublinear_tf)
        retriever.fit([r["utt"] for r in train])
        idx, sim = retriever.nearest([r["utt"] for r in evals])
        for row, i, s in zip(evals, idx, sim):
            near = train[i]
            preds.append({
                "id": row["id"], "locale": loc, "utt": row["utt"],
                "gold": row["call"], "pred": near["call"],
                "nearest_id": near["id"], "nearest_utt": near["utt"], "similarity": round(float(s), 4),
            })
    return preds


def write_samples(path: Path, preds: list[dict], n: int = 10) -> None:
    """First n hits and n misses per locale, as markdown tables."""
    lines = ["# B0 samples (dev)", ""]
    for loc in dict.fromkeys(p["locale"] for p in preds):
        rows = [p for p in preds if p["locale"] == loc]
        for title, keep in [("hits", True), ("misses", False)]:
            chosen = [p for p in rows if (p["pred"] == p["gold"]) == keep][:n]
            lines += [f"## {loc} {title}", "", "| utterance | gold | pred | nearest train utterance | sim |",
                      "|---|---|---|---|---|"]
            lines += [f"| {p['utt']} | `{p['gold']}` | `{p['pred']}` | {p['nearest_utt']} | {p['similarity']:.2f} |"
                      for p in chosen]
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))

    out_dir = Path("experiments") / cfg["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(args.config, out_dir / "config.yaml")

    train = load_split(cfg["data_dir"], cfg["locales"], "train")
    evals = load_split(cfg["data_dir"], cfg["locales"], cfg["split"])

    summary = {"split": cfg["split"], "select_by": cfg["select_by"], "variants": {}}
    for name, variant in cfg["variants"].items():
        run_dir = out_dir / name
        run_dir.mkdir(exist_ok=True)
        preds = predict(train, evals, variant, cfg["sublinear_tf"])
        write_jsonl(run_dir / f"predictions_{cfg['split']}.jsonl.gz", preds)
        write_samples(run_dir / "samples.md", preds)
        out = evaluate_run(run_dir, cfg["data_dir"], cfg["split"])
        summary["variants"][name] = {
            loc: {**{k: r[k] for k in HEADLINE}, **out["seen_unseen"][loc]}
            for loc, r in out["results"].items()
        }
        print(f"\n{name}: {variant}")
        print(format_table(out["results"]))
        print(format_seen_unseen(out["seen_unseen"]))

    best = max(summary["variants"], key=lambda v: summary["variants"][v]["overall"][cfg["select_by"]])
    summary["best"] = best
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(f"\nbest on {cfg['split']} by {cfg['select_by']}: {best}")


if __name__ == "__main__":
    main()
