"""Unit tests for src/models/seq2seq.py and src/inference/greedy.py (tiny model)."""

import pytest
import torch

from src.data.vocab import EOS_ID, PAD_ID, SOS_ID, SPECIALS, Vocab
from src.inference.greedy import greedy_decode, ids_to_calls
from src.models.seq2seq import Seq2Seq

V_SRC, V_TGT = 20, 12
DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


def tiny_model(device="cpu"):
    torch.manual_seed(0)
    return Seq2Seq(V_SRC, V_TGT, emb_dim=8, hidden_dim=16, num_layers=2, dropout=0.3).to(device).eval()


def batch(device="cpu"):
    src = torch.tensor([[4, 5, 6, 7], [8, 9, PAD_ID, PAD_ID]], device=device)
    return src, torch.tensor([4, 2])


def test_forward_shape():
    model = tiny_model()
    src, lens = batch()
    tgt_in = torch.tensor([[SOS_ID, 5, 6], [SOS_ID, 7, PAD_ID]])
    assert model(src, lens, tgt_in).shape == (2, 3, V_TGT)


@pytest.mark.parametrize("device", DEVICES)
def test_greedy_shape_and_device(device):
    model = tiny_model(device)
    out = greedy_decode(model, *batch(device), max_len=7)
    assert out.shape[0] == 2 and 1 <= out.shape[1] <= 7
    assert out.device.type == device


def test_first_token_is_argmax_of_forward():
    model = tiny_model()
    src, lens = batch()
    logits = model(src, lens, torch.full((2, 1), SOS_ID))  # (B, 1, V_tgt)
    out = greedy_decode(model, src, lens, max_len=1)
    assert torch.equal(out[:, 0], logits[:, 0].argmax(-1))


def test_stops_at_once_when_eos_is_always_best():
    model = tiny_model()
    with torch.no_grad():
        model.decoder.out.bias[EOS_ID] = 1e4
    out = greedy_decode(model, *batch(), max_len=10)
    assert out.tolist() == [[EOS_ID], [EOS_ID]]


def test_stops_at_max_len_without_eos():
    model = tiny_model()
    with torch.no_grad():
        model.decoder.out.bias[5] = 1e4
    out = greedy_decode(model, *batch(), max_len=6)
    assert out.shape == (2, 6) and torch.all(out == 5)


def test_finished_rows_get_padding(monkeypatch):
    model = tiny_model()
    # scripted outputs: row 0 ends at step 1, row 1 at step 2
    script = iter([[EOS_ID, 5], [6, EOS_ID], [7, 7]])

    def fake_step(y, state):
        logits = torch.zeros(2, V_TGT)
        logits[torch.arange(2), torch.tensor(next(script))] = 1.0
        return logits, state

    monkeypatch.setattr(model, "step", fake_step)
    out = greedy_decode(model, *batch(), max_len=10)
    assert out.tolist() == [[EOS_ID, PAD_ID], [5, EOS_ID]]  # stopped after step 2, row 0's 6 masked


def test_ids_to_calls():
    vocab = Vocab(SPECIALS + ["alarm_set", "alarm_query", "(", ")", "time", "=", '"', "five", "am"])
    rows = [["alarm_set", "(", "time", "=", '"', "five", "am", '"', ")"], ["alarm_query", "(", ")"]]
    ids = [vocab.encode(r) + [EOS_ID] for r in rows]
    ids[1] += [PAD_ID] * (len(ids[0]) - len(ids[1]))
    assert ids_to_calls(torch.tensor(ids), vocab) == ['alarm_set(time="five am")', "alarm_query()"]
