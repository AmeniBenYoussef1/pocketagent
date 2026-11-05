"""Tests for greedy confidence, the Predictor and the Agent (tiny models, CPU)."""

import pytest
import torch
import yaml

from src.agent.agent import Agent
from src.agent.dispatcher import Dispatcher
from src.agent.predictor import Prediction, Predictor
from src.agent.tools import MockBackend
from src.data.vocab import EOS_ID, PAD_ID, SOS_ID, build_vocabs
from src.inference.greedy import greedy_decode
from src.training.train import build_model


def cfg(model_type, lang_tag=True):
    return {"data": {"locales": ["en-US", "fr-FR", "ar-SA"], "lang_tag": lang_tag, "max_src_len": 32},
            "model": {"type": model_type, "emb_dim": 8, "hidden_dim": 16, "num_layers": 1,
                      "dropout": 0.0, "attn_dim": 8}}


@pytest.mark.parametrize("model_type", ["lstm", "attn", "copy"])
def test_confidence_is_geometric_mean_of_chosen_token_probs(rows, model_type):
    torch.manual_seed(0)
    src_vocab, tgt_vocab = build_vocabs(rows, 1)
    model = build_model(cfg(model_type), len(src_vocab), len(tgt_vocab)).eval()
    src, lens = torch.tensor([[4, 5, 6]]), torch.tensor([3])
    kwargs = {"src_ext": torch.tensor([[7, 8, len(tgt_vocab)]]), "n_oov": 1} if model_type == "copy" else {}
    ids, conf = greedy_decode(model, src, lens, max_len=6, return_confidence=True, **kwargs)
    _, conf_min = greedy_decode(model, src, lens, max_len=6, return_confidence=True, confidence="min", **kwargs)

    # recompute by stepping through the decoded tokens
    state, y, logps = model.start(src, lens, **kwargs), torch.tensor([SOS_ID]), []
    for tok in ids[0].tolist():
        if tok == PAD_ID:
            break
        scores, state = model.step(y, state)
        logps.append(torch.log_softmax(scores, -1)[0, tok].item())
        if tok == EOS_ID:
            break
        y = torch.tensor([tok])
    assert 0 < conf.item() <= 1
    assert conf.item() == pytest.approx(torch.tensor(logps).mean().exp().item(), rel=1e-5)
    assert conf_min.item() == pytest.approx(torch.tensor(logps).min().exp().item(), rel=1e-5)
    assert conf_min.item() <= conf.item()


def make_run(tmp_path, rows, model_type="copy", lang_tag=True):
    torch.manual_seed(0)
    src_vocab, tgt_vocab = build_vocabs(rows, 1)
    c = cfg(model_type, lang_tag)
    build = build_model(c, len(src_vocab), len(tgt_vocab))
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(c), encoding="utf-8")
    src_vocab.save(tmp_path / "vocab_src.json")
    tgt_vocab.save(tmp_path / "vocab_tgt.json")
    torch.save(build.state_dict(), tmp_path / "model.pt")
    return tmp_path


@pytest.mark.parametrize("model_type", ["lstm", "copy"])
def test_predictor_from_run(tmp_path, rows, model_type):
    pred = Predictor.from_run(make_run(tmp_path, rows, model_type), device="cpu")
    out = pred.predict(["wake me up at five am", "réveille-moi à cinq heures"], ["en-US", "fr-FR"])
    assert len(out) == 2 and all(isinstance(p.call, str) and 0 < p.confidence <= 1 for p in out)


def test_predictor_source_tokens(tmp_path, rows):
    pred = Predictor.from_run(make_run(tmp_path, rows), device="cpu")
    assert pred.source_tokens("wake me up", "fr-FR") == ["<fr>", "wake", "me", "up"]
    with pytest.raises(ValueError):
        pred.source_tokens("hola", "es-ES")


class FakePredictor:
    def __init__(self, call, confidence):
        self.out = Prediction(call, confidence)

    def predict(self, utterances, locales):
        return [self.out for _ in utterances]


def test_agent_runs_confident_call():
    agent = Agent(FakePredictor('alarm_set(time="five am")', 0.95), Dispatcher(MockBackend()))
    r = agent.handle("wake me up at five am")
    assert r.status == "executed" and r.call == 'alarm_set(time="five am")' and r.confidence == 0.95
    assert agent.dispatcher.backend.alarms[0]["time"] == "05:00"


def test_agent_asks_when_confidence_is_low():
    agent = Agent(FakePredictor('alarm_set(time="five am")', 0.2), Dispatcher(MockBackend(), confidence_threshold=0.5))
    r = agent.handle("wake me up at five am")
    assert r.status == "needs_confirmation" and agent.dispatcher.backend.alarms == []
    assert agent.handle("wake me up at five am", confirmed=True).status == "executed"


def test_agent_rejects_malformed_prediction():
    agent = Agent(FakePredictor('alarm_set(time="five am"', 0.99), Dispatcher(MockBackend()))
    r = agent.handle("wake me up at five am")
    assert r.status == "rejected" and agent.dispatcher.backend == MockBackend()


def test_calibrate_same_call_ignores_order_and_rejects_malformed():
    from src.agent.calibrate import same_call
    gold = 'alarm_set(time="five am", date="friday")'
    assert same_call('alarm_set(date="friday", time="five am")', gold)
    assert not same_call('alarm_set(time="six am", date="friday")', gold)
    assert not same_call('alarm_set(time="five am"', gold)


def test_auroc_and_threshold_table():
    from src.agent.calibrate import THRESHOLDS, auroc, threshold_table
    scored = [(0.99, True), (0.97, True), (0.6, False), (0.4, False)]
    assert auroc(scored) == 1.0
    assert auroc([(0.9, False), (0.1, True)]) == 0.0
    table = {r["threshold"]: r for r in threshold_table(scored)}
    assert len(table) == len(THRESHOLDS)
    assert table[0.0] == {"threshold": 0.0, "coverage": 1.0, "accuracy_kept": 0.5, "accuracy_asked": None}
    assert table[0.95] == {"threshold": 0.95, "coverage": 0.5, "accuracy_kept": 1.0, "accuracy_asked": 0.0}
