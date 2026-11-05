"""Unit tests for src/inference/beam.py."""

import pytest
import torch

from src.data.vocab import EOS_ID, PAD_ID, SOS_ID
from src.inference.beam import beam_search
from src.inference.greedy import greedy_decode
from src.models.attention_seq2seq import AttnSeq2Seq
from src.models.copy import CopySeq2Seq
from src.models.seq2seq import Seq2Seq

V_SRC, V_TGT = 20, 12
A, B, X, Y = 4, 5, 6, 7  # token ids of the toy model


class ToyModel(torch.nn.Module):
    """Next-token probabilities depend only on the previous token.

    SOS -> A 0.6, B 0.4;  A -> X 0.5, Y 0.5;  B, X, Y -> EOS.
    Greedy: A X EOS (p = 0.3). Best sequence: B EOS (p = 0.4).
    """

    table = {SOS_ID: {A: 0.6, B: 0.4}, A: {X: 0.5, Y: 0.5}}

    def start(self, src, src_lens):
        return torch.zeros(src.size(0))

    def step(self, y, state):
        probs = torch.full((y.size(0), 8), 1e-9)
        for i, prev in enumerate(y.tolist()):
            for tok, p in self.table.get(prev, {EOS_ID: 1.0}).items():
                probs[i, tok] = p
        return torch.log(probs), state

    @staticmethod
    def reorder_state(state, index):
        return state[index]


def src_batch():
    return torch.tensor([[4, 5, 6], [7, 8, PAD_ID]]), torch.tensor([3, 2])


def test_beam_finds_better_sequence_than_greedy():
    src, lens = torch.zeros(1, 1, dtype=torch.long), torch.tensor([1])
    model = ToyModel()
    assert greedy_decode(model, src, lens).tolist() == [[A, X, EOS_ID]]
    assert beam_search(model, src, lens, beam_size=2, alpha=0.0).tolist() == [[B, EOS_ID, PAD_ID]]


def models():
    torch.manual_seed(0)
    return [Seq2Seq(V_SRC, V_TGT, 8, 16, 2, 0.3).eval(),
            AttnSeq2Seq(V_SRC, V_TGT, 8, 16, 2, 0.3, 10).eval()]


@pytest.mark.parametrize("model", models(), ids=["lstm", "attn"])
def test_beam_size_one_equals_greedy(model):
    src, lens = src_batch()
    greedy = greedy_decode(model, src, lens, max_len=8)
    beam = beam_search(model, src, lens, beam_size=1, max_len=8, alpha=0.0)
    assert torch.equal(beam[:, :greedy.size(1)], greedy)


def sequence_logprob(model, src, lens, ids):
    """Sum of log-probs of a decoded row (up to <EOS>) under the model."""
    total, state = 0.0, model.start(src, lens)
    y = torch.tensor([SOS_ID])
    for tok in ids:
        logits, state = model.step(y, state)
        total += torch.log_softmax(logits, -1)[0, tok].item()
        if tok == EOS_ID:
            break
        y = torch.tensor([tok])
    return total


@pytest.mark.parametrize("model", models(), ids=["lstm", "attn"])
def test_beam_score_at_least_greedy(model):
    src, lens = torch.tensor([[4, 5, 6]]), torch.tensor([3])
    greedy = greedy_decode(model, src, lens, max_len=8)[0].tolist()
    beam = beam_search(model, src, lens, beam_size=4, max_len=8, alpha=0.0)[0].tolist()
    assert sequence_logprob(model, src, lens, beam) >= sequence_logprob(model, src, lens, greedy) - 1e-5


def test_padding_after_eos_and_shape():
    model = models()[1]
    with torch.no_grad():
        model.decoder.out.bias[EOS_ID] = 1e4
    out = beam_search(model, *src_batch(), beam_size=3, max_len=6)
    # the best beam ends at step 1; other beams may run longer, so the batch can have
    # extra columns, which must be <PAD>
    assert out.size(0) == 2 and torch.all(out[:, 0] == EOS_ID)
    assert torch.all(out[:, 1:] == PAD_ID)


def test_beam_with_copy_model():
    torch.manual_seed(0)
    model = CopySeq2Seq(V_SRC, V_TGT, 8, 16, 2, 0.3, 10).eval()
    src, lens = src_batch()
    src_ext = torch.tensor([[4, 12, 13], [5, 12, PAD_ID]])  # ids 12, 13 are per-row OOV words
    greedy = greedy_decode(model, src, lens, max_len=6, src_ext=src_ext, n_oov=2)
    beam = beam_search(model, src, lens, beam_size=1, max_len=6, alpha=0.0, src_ext=src_ext, n_oov=2)
    assert torch.equal(beam[:, :greedy.size(1)], greedy)
    assert beam_search(model, src, lens, beam_size=3, max_len=6, src_ext=src_ext, n_oov=2).max() < V_TGT + 2


def test_length_penalty_can_prefer_longer_call():
    # raw log-prob prefers the short B EOS (0.4 vs 0.3); a strong length penalty flips it
    src, lens = torch.zeros(1, 1, dtype=torch.long), torch.tensor([1])
    assert beam_search(ToyModel(), src, lens, beam_size=2, alpha=0.0)[0, :2].tolist() == [B, EOS_ID]
    assert beam_search(ToyModel(), src, lens, beam_size=2, alpha=2.0)[0, 0].item() == A
