# PocketAgent web app

React + Vite + TypeScript + Tailwind, talking to the FastAPI app in `app/api/`. Design notes in [DESIGN.md](DESIGN.md).

## Run everything

From the repo root, with the Python requirements installed and Node.js 20+:

```bash
python -m app.serve          # builds app/web the first time, then http://localhost:8000
python -m app.serve --cpu    # same, never uses the GPU
```

The first run needs `npm` to install and build the web app (about a minute). After that the build is reused until a file in `app/web/src` changes; `--rebuild` forces it.

The models load on first use from `experiments/<run>/model.pt` (E0 `e0_lstm`, E1 `e1_attn`, E2 `e2_copy`). Checkpoints are not in Git, so train them first or copy them in. B0 needs the raw data in `data/massive/`.

## Develop

Two terminals:

```bash
uvicorn app.api.main:app --reload        # API on :8000
cd app/web && npm run dev                # web app on :5173, /api proxied to :8000
```

## Settings

Defaults are in [configs/agent.yaml](../../configs/agent.yaml): E2 with beam 3, mean confidence, threshold 0.98 (chosen on dev). Environment variables override them:

| variable | |
|---|---|
| `POCKETAGENT_DEVICE` | `auto` (default), `cpu` or `cuda` |
| `POCKETAGENT_THRESHOLD` | below this confidence the agent asks first |
| `POCKETAGENT_CONFIDENCE` | `mean` or `min` token probability |
| `POCKETAGENT_HOME_CITY` | weather place when the command has none |
| `POCKETAGENT_OFFLINE` | `1` turns off the live forecast (Open-Meteo) |
