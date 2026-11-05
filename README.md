# PocketAgent

PocketAgent turns short commands in English, French and Arabic into function calls, then checks them and runs a tool: "wake me up at five am this week" becomes `alarm_set(time="five am", date="this week")`. The model is an LSTM encoder-decoder with Bahdanau attention and a copy mechanism, built from PyTorch layers and trained from scratch on Amazon MASSIVE (no pretrained model or embeddings). One joint model covers the three languages and reaches 57.6% exact match on the test split, against 34.7% for a retrieval baseline. An agent layer validates every call, asks when an argument is missing or the model is unsure, and keeps e-mails as drafts until they are confirmed. Master AIDA course project (Dauphine-PSL Tunis).

<!-- demo GIF: not recorded yet, see docs/README.md. Once docs/demo.gif exists, remove this comment around the next line.
![Demo of the web app](docs/demo.gif)
-->

## Results

Dev split, 6,099 commands (2,033 per language). Exact match (EM) counts a call as right only if the function and every argument match; argument order is ignored.

| model | EM | EM en-US | EM fr-FR | EM ar-SA | intent acc. | slot F1 |
|---|---|---|---|---|---|---|
| B0 retrieval (TF-IDF, nearest train command) | 35.2% | 40.4% | 33.1% | 32.2% | 69.6% | 44.1% |
| E0 LSTM encoder-decoder | 44.4% | 47.9% | 45.3% | 40.0% | 80.6% | 47.9% |
| E1 + BiLSTM, Bahdanau attention | 45.8% | 50.3% | 46.1% | 40.9% | 80.6% | 52.1% |
| E2 + copy (pointer-generator) | 57.6% | 64.1% | 57.6% | 51.2% | 80.5% | 70.1% |
| E2 + beam 3 | **58.2%** | **64.5%** | **58.2%** | **51.8%** | 80.8% | 70.7% |

Test split, 8,922 commands, evaluated once with the model and settings fixed on dev ([experiments/final_test/](experiments/final_test/)):

| model | EM | EM en-US | EM fr-FR | EM ar-SA | intent acc. | slot F1 | valid calls | macro EM |
|---|---|---|---|---|---|---|---|---|
| B0 retrieval | 34.7% | 38.2% | 34.8% | 31.1% | 68.4% | 42.4% | 100% | 37.8% |
| E2 + beam 3 (final) | **57.6%** | **62.7%** | **57.7%** | **52.4%** | **79.4%** | **69.3%** | 100% | **58.2%** |

On the 8,514 test commands that don't appear in the training data, the final model gets 56.3% EM (B0: 32.5%).

## Findings

- Copying fixes the values. Without it, a value word missing from the target vocabulary can only come out as `<UNK>`: that alone made 6.7% of E1's dev calls wrong. E2 brings it to 0, completely wrong values drop from 3.6% to 0.6% of dev, and slot F1 goes from 52.1% to 70.1%. The cost is a few repeated copies such as `"the ucl ucl"` (0.4% of dev).
- One joint model beats one model per language. Trained on a single language (E7, same setup, beam 3), E2 loses 1.4 points of dev EM in English, 1.6 in French and 2.1 in Arabic, while needing three models instead of one. Arabic gains most from sharing.
- Wrong intent is now the main error: 20.6% of test calls, 24.7% of Arabic dev calls. None of the decoder changes (attention, copy, beam) touch it.
- Beam search adds 0.6 point of dev EM. Beams of 3, 5 and 10 give the same score, so the app uses 3.
- Confidence threshold: the agent runs a call on its own when the geometric mean of its token probabilities is at least 0.98. On dev that means acting alone on 55.8% of commands, 81.2% of them exactly right, and asking on the other 44.2%, where only 27.9% would have been right. Lower thresholds ask less but are wrong more often (0.95: 71.5% alone, 72.2% right). The mean and the minimum token probability rank calls about equally well (AUROC 0.844 and 0.848).

More detail: [notebooks/02_error_analysis.ipynb](notebooks/02_error_analysis.ipynb) and [report/data_stats.md](report/data_stats.md).

## How it works

```
 "<en> wake me up at five am"
              |
   encoder    BiLSTM, one vector per word
              |
   attention  weights the input words at each output step
   + copy     p_gen: write a vocabulary word, or copy the attended input word
              |
   decoder    LSTM, one token at a time, beam 3
              |
 alarm_set(time="five am")                      <- end of the neural model
              |
   validator  known tool? required arguments? confidence >= 0.98?
              normalizes times and dates ("five am" -> 05:00)
              |
   tool       alarm, weather, calendar, music, e-mail (always a draft first)
```

## Install

Python 3.10+ (tested with 3.13).

```bash
# GPU: install the CUDA build of PyTorch first (check the CUDA version your driver supports with nvidia-smi)
pip install torch --index-url https://download.pytorch.org/whl/cu132
# CPU only: skip the line above, the next one installs the CPU build
pip install -r requirements.txt

python -m src.data.download_massive      # MASSIVE en-US, fr-FR, ar-SA into data/massive/
```

The web app also needs Node.js 20+ (npm).

## Run

Train and evaluate (one YAML per experiment in `configs/`, results in `experiments/<name>/`):

```bash
python -m src.training.train --config configs/e2_copy.yaml
python -m src.inference.decode_run --run experiments/e2_copy --beam 3
python -m src.training.evaluate --run experiments/e2_copy
pytest
```

Checkpoints (`model.pt`) are not in Git; train the runs you want to use first.

Web app and API, on http://localhost:8000:

```bash
python -m app.serve          # builds the web app the first time, uses the GPU if there is one
python -m app.serve --cpu    # CPU only
```

Settings (threshold, model, decoding) are in [configs/agent.yaml](configs/agent.yaml). More in [app/web/README.md](app/web/README.md).

## Repository

```
configs/        one YAML per experiment, agent.yaml for the app
data/           download instructions (raw data is not committed)
notebooks/      01_dataset_audit.ipynb, 02_error_analysis.ipynb
src/data/       converter, vocabulary, Dataset/DataLoader
src/models/     encoder, decoder, attention, copy, seq2seq wrappers
src/training/   train.py, evaluate.py, metrics.py, errors.py
src/baselines/  B0 retrieval
src/inference/  greedy and beam search, decode_run.py
src/agent/      parser, normalizer, validator, dispatcher, tools, predictor
app/api/        FastAPI (/api/parse, /api/execute, /api/models, /api/results, ...)
app/web/        React + Vite + TypeScript + Tailwind web app
tests/          pytest unit tests
experiments/    one folder per run: config, metrics, curves, predictions, samples
report/         specification and report material
docs/           images for this README (demo.gif)
```

## Dataset and licence

Amazon MASSIVE, locales en-US, fr-FR and ar-SA, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The raw dataset is downloaded by the script above and not stored in this repo. The experiment outputs in `experiments/` (predictions, samples) and the notebook outputs do contain MASSIVE utterances and their annotations, shared under the same CC BY 4.0 licence.

```bibtex
@inproceedings{fitzgerald2023massive,
  title     = {{MASSIVE}: A 1{M}-Example Multilingual Natural Language Understanding Dataset with 51 Typologically-Diverse Languages},
  author    = {FitzGerald, Jack and Hench, Christopher and Peris, Charith and Mackie, Scott and Rottmann, Kay and Sanchez, Ana and Nash, Aaron and Urbach, Liam and Kakarala, Vishesh and Singh, Richa and Ranganath, Swetha and Crist, Laurie and Britan, Misha and Leeuwis, Wouter and Tur, Gokhan and Natarajan, Prem},
  booktitle = {Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2023}
}
```

The code is released under the [MIT licence](LICENSE).
