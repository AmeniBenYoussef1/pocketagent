"""Tests for what the web app reads: the results builder, replay (token probs, attention, p_gen),
the model hub, the weather client and the extra tools."""

import gzip
import json
import math

import pytest
import torch

from app.api.hub import ModelHub
from app.api.results import build_results
from src.agent.dispatcher import Dispatcher
from src.agent.explain import replay
from src.agent.predictor import Predictor
from src.agent.tools import MockBackend, weather_query
from src.agent import weather
from tests.test_predictor import make_run


def write_run(exp, run, split="dev", preds=None, history=False):
    d = exp / run
    d.mkdir(parents=True)
    scores = {"exact_match": 0.5, "exact_match_strict": 0.5, "intent_accuracy": 0.8, "slot_f1": 0.6,
              "valid_call_rate": 1.0, "macro_exact_match": 0.4}
    part = {"n": 1, "exact_match": 1.0, "intent_accuracy": 1.0, "slot_f1": 1.0}
    (d / "metrics.json").write_text(json.dumps({"split": split, "results": {"overall": scores, "en-US": scores},
                                                "seen_unseen": {"overall": {"seen": part, "unseen": part}}}))
    with gzip.open(d / f"predictions_{split}.jsonl.gz", "wt", encoding="utf-8") as f:
        for p in preds or []:
            f.write(json.dumps(p) + "\n")
    if history:
        (d / "history.json").write_text(json.dumps({"epochs": [
            {"epoch": 1, "train_loss": 1.0, "eval_loss": 1.1, "eval_em": 0.2, "train_seconds": 40.0}]}))


def test_build_results(tmp_path):
    preds = [{"id": "1", "locale": "en-US", "gold": 'alarm_set(time="five am")', "pred": 'alarm_set(time="five am")'},
             {"id": "2", "locale": "en-US", "gold": 'alarm_set(time="five am")', "pred": "alarm_query()"}]
    write_run(tmp_path, "e0_lstm", preds=preds, history=True)
    write_run(tmp_path, "e1_attn", split="train", preds=preds)  # overfit-style run: left out
    r = build_results(tmp_path)
    assert [run["id"] for run in r["runs"]] == ["e0_lstm"]
    run = r["runs"][0]
    assert run["label"] == "E0" and run["group"] == "ladder" and run["metrics"]["overall"]["em"] == 0.5
    assert run["errors"]["wrong intent"] == 0.5 and run["history"][0]["dev_em"] == 0.2
    assert build_results(tmp_path) is r  # cached until a file changes


@pytest.mark.parametrize("model_type", ["lstm", "attn", "copy"])
def test_replay(tmp_path, rows, model_type):
    predictor = Predictor.from_run(make_run(tmp_path, rows, model_type), device="cpu")
    call = predictor.predict(["wake me up at five am"], ["en-US"])[0]
    info = replay(predictor, "wake me up at five am", "en-US", 'alarm_set(time="five am")')
    assert info["src_tokens"] == ["<en>", "wake", "me", "up", "at", "five", "am"]
    assert info["tgt_tokens"][-1] == "<EOS>" and len(info["token_probs"]) == len(info["tgt_tokens"])
    assert all(0 < p <= 1 for p in info["token_probs"])
    assert info["confidence"] == pytest.approx(math.exp(sum(map(math.log, info["token_probs"])) / len(info["token_probs"])))
    assert (info["attention"] is None) == (model_type == "lstm")
    assert (info["p_gen"] is not None) == (model_type == "copy")
    if info["attention"]:
        assert torch.allclose(torch.tensor(info["attention"]).sum(-1), torch.ones(len(info["tgt_tokens"])), atol=1e-5)
    assert replay(predictor, "wake me up", "en-US", 'alarm_set(time="five am"') is None
    # replaying the greedy call gives the greedy confidence
    greedy = replay(predictor, "wake me up at five am", "en-US", call.call)
    if greedy is not None:
        assert greedy["confidence"] == pytest.approx(call.confidence, rel=1e-4)


def test_hub_parse_with_a_trained_run(tmp_path, rows):
    exp = tmp_path / "exp"
    (exp / "e2_copy").mkdir(parents=True)
    make_run(exp / "e2_copy", rows, "copy")
    hub = ModelHub(exp, tmp_path / "no_data", device="cpu")
    assert {m["id"]: m["ready"] for m in hub.available()} == {"b0": False, "e0": False, "e1": False, "e2": True}
    for decoding in ("greedy", "beam3"):
        r = hub.parse("wake me up at five am", "en-US", "e2", decoding)
        assert r["decoding"] == decoding and isinstance(r["call"], str) and r["latency_ms"] >= 0
        if r["tokens"]:
            assert {t["source"] for t in r["tokens"]} <= {"copied", "generated"}
            assert len(r["attention"]["weights"]) == len(r["tokens"])


def test_open_meteo_picks_the_requested_day(monkeypatch):
    def fake_get(url, params, timeout):
        if url == weather.GEOCODE:
            return {"results": [{"name": "Paris", "country": "France", "latitude": 48.8, "longitude": 2.3}]}
        return {"daily": {"time": ["2026-11-05", "2026-11-06"], "weather_code": [0, 63],
                          "temperature_2m_max": [14.2, 11.0], "temperature_2m_min": [6.1, 5.0],
                          "precipitation_probability_max": [5, 80]}}
    monkeypatch.setattr(weather, "_get", fake_get)
    r = weather.open_meteo("paris", "2026-11-06")
    assert r == {"place": "Paris, France", "date": "2026-11-06", "condition": "rain", "temp_max_c": 11.0,
                 "temp_min_c": 5.0, "precipitation_chance": 80, "source": "Open-Meteo"}
    with pytest.raises(LookupError):
        weather.open_meteo("paris", "2027-01-01")


def test_weather_falls_back_when_the_provider_fails():
    def down(place, date, language):
        raise OSError("no network")
    backend = MockBackend(weather_provider=down, home_city="Tunis")
    r = weather_query(backend, date="2026-11-06")
    assert r["place"] == "Tunis" and r["source"] == "offline estimate" and "OSError" in r["note"]


def test_play_music_and_cancel_draft():
    d = Dispatcher(MockBackend())
    r = d.dispatch('play_music(music_genre="jazz")')
    assert r.status == "executed" and r.result["genre"] == "jazz" and d.backend.playing["shuffle"] is False
    draft = d.dispatch('email_sendemail(person="john")', confirmed=True)
    assert draft.status == "needs_confirmation" and d.backend.outbox == []
    assert d.cancel(draft.result["id"]).result["cancelled"] is True
    assert d.backend.drafts == [] and d.cancel(draft.result["id"]).status == "rejected"
