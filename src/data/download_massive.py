"""Download Amazon MASSIVE (en-US, fr-FR, ar-SA) and save it as JSONL.

Usage:
    python -m src.data.download_massive
    python -m src.data.download_massive --locales en-US fr-FR --out data/massive

Source: the auto-converted Parquet branch of the Hugging Face dataset
`AmazonScience/massive`. The main branch only has a loading script, which recent
versions of `datasets` refuse to run, so we read the Parquet files directly.

Output: data/massive/<locale>/<split>.jsonl with splits train / dev / test.
"""

import argparse
import json
import os
from pathlib import Path

# Windows without Developer Mode cannot create symlinks; the HF cache still works,
# so we silence the (harmless) warning.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "AmazonScience/massive"
# Pinned commit of refs/convert/parquet, so every run downloads exactly the same data.
REVISION = "ed58ac423a2f4121720918bf5301577edce4ffd3"

DEFAULT_LOCALES = ["en-US", "fr-FR", "ar-SA"]
# Hugging Face split name -> our split name
SPLITS = {"train": "train", "validation": "dev", "test": "test"}

KEEP_COLUMNS = ["id", "locale", "scenario", "intent", "utt", "annot_utt"]


def label_names(table, column: str) -> list[str]:
    """Return the ClassLabel names stored in the Parquet metadata for `column`.

    In the Parquet files, `intent` and `scenario` are integers; the mapping
    integer -> name is stored in the Hugging Face schema metadata.
    """
    meta = json.loads(table.schema.metadata[b"huggingface"])
    return meta["info"]["features"][column]["names"]


def download_split(locale: str, hf_split: str, cache_dir: Path) -> list[dict]:
    """Download one (locale, split) Parquet file and return its rows as dicts."""
    path = hf_hub_download(
        repo_id=REPO_ID,
        filename=f"{locale}/{hf_split}/0000.parquet",
        repo_type="dataset",
        revision=REVISION,
        cache_dir=cache_dir,
    )
    table = pq.read_table(path)
    intents = label_names(table, "intent")
    scenarios = label_names(table, "scenario")

    rows = []
    for r in table.select(KEEP_COLUMNS).to_pylist():
        rows.append({
            "id": r["id"],
            "locale": r["locale"],
            "split": SPLITS[hf_split],
            "scenario": scenarios[r["scenario"]],
            "intent": intents[r["intent"]],
            "utt": r["utt"],
            "annot_utt": r["annot_utt"],
        })
    return rows


def write_jsonl(rows: list[dict], path: Path) -> None:
    """Write one JSON object per line (UTF-8, Arabic kept readable)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--locales", nargs="+", default=DEFAULT_LOCALES)
    parser.add_argument("--out", type=Path, default=Path("data/massive"))
    args = parser.parse_args()

    cache_dir = args.out.parent / ".cache"
    for locale in args.locales:
        for hf_split, split in SPLITS.items():
            rows = download_split(locale, hf_split, cache_dir)
            out_path = args.out / locale / f"{split}.jsonl"
            write_jsonl(rows, out_path)
            print(f"{locale:6s} {split:5s} {len(rows):6d} rows -> {out_path}")


if __name__ == "__main__":
    main()
