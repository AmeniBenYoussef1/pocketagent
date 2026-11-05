"""Tests for the FastAPI app with a fake model hub (no model loaded, no network)."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from src.agent.dispatcher import Dispatcher
from src.agent.tools import MockBackend

CALLS = {
    "wake me up at five am": ('alarm_set(time="five am")', 0.97),
    "email john about the party": ('email_sendemail(person="john", event_name="party")', 0.95),
    "maybe set an alarm": ('alarm_set(time="five am")', 0.30),
    "set an alarm": ("alarm_set()", 0.9),
    "broken": ('alarm_set(time="five am"', None),
}


class FakeHub:
    def available(self):
        return [{"id": "e2", "short": "E2", "name": "Copy", "ready": True, "decodings": ["greedy", "beam3"]}]

    def parse(self, utterance, locale, model, decoding):
        call, conf = CALLS[utterance]
        return {"model": model, "decoding": decoding, "call": call, "confidence": conf, "latency_ms": 1.0,
                "tokens": None, "attention": None}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(FakeHub(), Dispatcher(MockBackend(), confidence_threshold=0.5),
                                 exp_dir=tmp_path, serve_web=False))


def run(client, utterance, **extra):
    parsed = client.post("/api/parse", json={"utterance": utterance}).json()
    return client.post("/api/execute", json={"call": parsed["call"], "confidence": parsed["confidence"], **extra}).json()


def test_health_models_tools(client):
    assert client.get("/api/health").json()["status"] == "ok"
    models = client.get("/api/models").json()
    assert models["models"] == FakeHub().available() and models["threshold"] == 0.5
    assert models["default"] == {"model": "e2", "decoding": "beam3"}
    tools = client.get("/api/tools").json()
    assert set(tools) == {"alarm_set", "weather_query", "calendar_set", "play_music", "email_sendemail"}
    assert tools["email_sendemail"]["sensitive"] is True


def test_parse_runs_nothing_and_checks_model(client):
    r = client.post("/api/parse", json={"utterance": "wake me up at five am", "model": "e2", "decoding": "beam3"}).json()
    assert r["call"] == 'alarm_set(time="five am")' and r["decoding"] == "beam3"
    assert client.post("/api/parse", json={"utterance": "x", "model": "gpt"}).status_code == 404


def test_execute_alarm(client):
    r = run(client, "wake me up at five am")
    assert r["status"] == "executed" and r["result"]["time"] == "05:00" and r["call"] == 'alarm_set(time="five am")'


def test_low_confidence_then_confirm(client):
    assert run(client, "maybe set an alarm")["status"] == "needs_confirmation"
    assert run(client, "maybe set an alarm", confirmed=True)["status"] == "executed"


def test_follow_up_question_is_filled(client):
    r = run(client, "set an alarm")
    assert r["status"] == "needs_input" and r["missing"] == ["time"]
    r = client.post("/api/execute", json={"call": "alarm_set()", "confidence": 0.9, "fill": {"time": "seven am"}}).json()
    assert r["status"] == "executed" and r["result"]["time"] == "07:00"


def test_malformed_call_is_rejected(client):
    assert run(client, "broken")["status"] == "rejected"


def test_email_draft_confirm_and_cancel(client):
    r = run(client, "email john about the party", confirmed=True)  # confirmed never sends
    assert r["status"] == "needs_confirmation" and r["result"]["sent"] is False
    sent = client.post("/api/execute", json={"draft_id": r["result"]["id"], "action": "confirm"}).json()
    assert sent["result"]["sent"] is True
    assert client.post("/api/execute", json={"draft_id": r["result"]["id"], "action": "confirm"}).status_code == 404
    r2 = run(client, "email john about the party")
    cancelled = client.post("/api/execute", json={"draft_id": r2["result"]["id"], "action": "cancel"}).json()
    assert cancelled["result"]["cancelled"] is True


def test_bad_requests(client):
    assert client.post("/api/parse", json={"utterance": "hola", "locale": "es-ES"}).status_code == 422
    assert client.post("/api/execute", json={}).status_code == 422
    assert client.post("/api/execute", json={"call": "x()", "draft_id": 1}).status_code == 422
    assert client.post("/api/execute", json={"draft_id": 1}).status_code == 422  # no action


def test_results_endpoint_reads_experiments(client):
    r = client.get("/api/results").json()
    assert r["runs"] == [] and r["calibration"] is None


def test_settings_come_from_agent_config(monkeypatch):
    from app.api.main import settings
    monkeypatch.delenv("POCKETAGENT_THRESHOLD", raising=False)
    cfg = settings()
    assert (cfg["model"], cfg["decoding"], cfg["confidence"], cfg["threshold"]) == ("e2", "beam3", "mean", 0.98)
    monkeypatch.setenv("POCKETAGENT_THRESHOLD", "0.9")
    assert settings()["threshold"] == 0.9
