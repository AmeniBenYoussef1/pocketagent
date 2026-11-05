"""PocketAgent API, and the web app (app/web/dist) on the same port.

    python -m app.serve          (builds the web app if needed, then runs this)
    uvicorn app.api.main:app     (API only)

    GET  /api/health    status, device, confidence threshold
    GET  /api/tools     tools and their arguments
    GET  /api/models    models the app can use and their decodings
    POST /api/parse     utterance -> call, confidence, latency, tokens (p_gen), attention. Nothing runs.
    POST /api/execute   a call -> safety checks -> tool result (fill answers a follow-up question),
                        or {draft_id, action} to send or cancel an e-mail draft
    GET  /api/results   every dev result in experiments/ for the Results page

Defaults come from configs/agent.yaml (model, decoding, confidence score, threshold, home city).
Environment variables override them: POCKETAGENT_DEVICE (auto, cpu, cuda), POCKETAGENT_THRESHOLD,
POCKETAGENT_CONFIDENCE (mean or min), POCKETAGENT_HOME_CITY, POCKETAGENT_OFFLINE=1 (no live weather).
"""

import os
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from app.api.hub import MODELS, ModelHub
from app.api.results import build_results
from src.agent.dispatcher import Dispatcher
from src.agent.tools import MockBackend
from src.agent.validator import TOOLS

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "app" / "web" / "dist"
Locale = Literal["en-US", "fr-FR", "ar-SA"]


def settings() -> dict:
    """configs/agent.yaml, with environment variables on top."""
    import yaml
    cfg = yaml.safe_load((ROOT / "configs" / "agent.yaml").read_text(encoding="utf-8"))
    env = {"threshold": "POCKETAGENT_THRESHOLD", "confidence": "POCKETAGENT_CONFIDENCE",
           "home_city": "POCKETAGENT_HOME_CITY"}
    for key, var in env.items():
        if os.environ.get(var):
            cfg[key] = os.environ[var]
    cfg["threshold"] = float(cfg["threshold"])
    return cfg


class ParseRequest(BaseModel):
    utterance: str
    locale: Locale = "en-US"
    model: str = "e2"
    decoding: Literal["greedy", "beam3", "nearest"] = "greedy"


class ExecuteRequest(BaseModel):
    call: str | None = None
    locale: Locale = "en-US"
    confidence: float | None = None
    confirmed: bool = False
    fill: dict[str, str] | None = None
    draft_id: int | None = None
    action: Literal["confirm", "cancel"] | None = None

    @model_validator(mode="after")
    def one_input(self):
        if (self.call is None) == (self.draft_id is None):
            raise ValueError("give either call or draft_id")
        if self.draft_id is not None and self.action is None:
            raise ValueError("draft_id needs action: confirm or cancel")
        return self


def default_dispatcher(cfg: dict) -> Dispatcher:
    backend = MockBackend(home_city=cfg["home_city"])
    if os.environ.get("POCKETAGENT_OFFLINE") != "1":
        from src.agent.weather import open_meteo
        backend.weather_provider = open_meteo
    return Dispatcher(backend, confidence_threshold=cfg["threshold"])


def create_app(hub=None, dispatcher: Dispatcher | None = None, exp_dir: Path = ROOT / "experiments",
               serve_web: bool = True) -> FastAPI:
    """hub and dispatcher are injectable for tests; by default the real models load on first use."""
    app = FastAPI(title="PocketAgent", version="0.2")
    cfg = settings()
    hub = hub or ModelHub(exp_dir, ROOT / "data" / "massive", os.environ.get("POCKETAGENT_DEVICE", "auto"),
                          cfg["confidence"])
    dispatcher = dispatcher or default_dispatcher(cfg)
    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health():
        return {"status": "ok", "device": os.environ.get("POCKETAGENT_DEVICE", "auto"),
                "confidence_threshold": dispatcher.confidence_threshold}

    @api.get("/tools")
    def tools():
        return {name: {"required": list(s.required), "one_of": [list(g) for g in s.one_of],
                       "optional": list(s.optional), "sensitive": s.sensitive}
                for name, s in TOOLS.items()}

    @api.get("/models")
    def models():
        return {"models": hub.available(), "threshold": dispatcher.confidence_threshold,
                "default": {"model": cfg["model"], "decoding": cfg["decoding"]}}

    @api.post("/parse")
    def parse_utterance(req: ParseRequest):
        if req.model not in MODELS:
            raise HTTPException(404, f"unknown model {req.model}")
        try:
            return hub.parse(req.utterance, req.locale, req.model, req.decoding)
        except FileNotFoundError as e:
            raise HTTPException(503, f"model files missing: {e}") from e

    @api.post("/execute")
    def execute(req: ExecuteRequest):
        if req.draft_id is not None:
            action = dispatcher.confirm if req.action == "confirm" else dispatcher.cancel
            response = action(req.draft_id)
            if response.status == "rejected":
                raise HTTPException(404, response.message)
        else:
            response = dispatcher.dispatch(req.call, req.locale, req.confidence, req.confirmed, req.fill)
            response.call, response.confidence = req.call, req.confidence
        return asdict(response)

    @api.get("/results")
    def results():
        return build_results(exp_dir)

    app.include_router(api)

    if serve_web and WEB_DIST.exists():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def web(path: str):
            # client-side routes (/results, /how-it-works) all load index.html
            file = WEB_DIST / path
            return FileResponse(file if path and file.is_file() else WEB_DIST / "index.html")

    return app


app = create_app()
