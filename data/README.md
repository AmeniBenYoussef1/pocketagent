# Data

PocketAgent uses **Amazon MASSIVE** (FitzGerald et al., 2022), licensed CC BY 4.0.
Raw data is **not** stored in Git. Download it with:

    python -m src.data.download_massive

This creates:

    data/massive/
        en-US/train.jsonl  dev.jsonl  test.jsonl
        fr-FR/train.jsonl  dev.jsonl  test.jsonl
        ar-SA/train.jsonl  dev.jsonl  test.jsonl

One JSON object per line:

    {"id": "17", "locale": "en-US", "split": "dev", "scenario": "iot",
     "intent": "iot_hue_lightdim", "utt": "dim the lights in the hall",
     "annot_utt": "dim the lights in the [house_place : hall]"}

## Source

- Hugging Face: `AmazonScience/massive`, auto-converted Parquet branch
  (`refs/convert/parquet`), pinned to a fixed commit in `src/data/download_massive.py`.
  The main branch only contains a loading script, which `datasets` >= 4.0 no longer runs.
- The Hugging Face split `validation` is renamed `dev`.

## Rules

- Vocabularies and tokenizers are fitted on `train` only.
- `test` is never used for tuning, early stopping or model selection.

## Citation

FitzGerald et al. (2022). *MASSIVE: A 1M-Example Multilingual Natural Language
Understanding Dataset with 51 Typologically-Diverse Languages.* arXiv:2204.08582.
