"""Unit tests for src/models/ (tiny sizes, CPU, eval mode so dropout is off)."""

import pytest
import torch

from src.data.vocab import PAD_ID, SOS_ID
from src.models.decoder import Decoder
from src.models.encoder import Encoder

V, E, H, L = 20, 8, 16, 2
V_TGT = 12


@pytest.fixture
def encoder():
    torch.manual_seed(0)
    return Encoder(V, E, H, num_layers=L, dropout=0.3).eval()


def batch(*seqs):
    """Pad id lists into (B, T) plus lengths (B,)."""
    T = max(len(s) for s in seqs)
    src = torch.tensor([s + [PAD_ID] * (T - len(s)) for s in seqs])
    return src, torch.tensor([len(s) for s in seqs])


def test_shapes(encoder):
    src, lens = batch([4, 5, 6, 7], [8, 9])
    outputs, (h, c) = encoder(src, lens)
    assert outputs.shape == (2, 4, H)
    assert h.shape == c.shape == (L, 2, H)


def test_padded_positions_are_zero(encoder):
    src, lens = batch([4, 5, 6, 7], [8, 9])
    outputs, _ = encoder(src, lens)
    assert torch.all(outputs[1, 2:] == 0)


def test_padding_does_not_change_the_result(encoder):
    alone_out, (alone_h, alone_c) = encoder(*batch([8, 9]))
    out, (h, c) = encoder(*batch([4, 5, 6, 7, 10, 11], [8, 9]))
    assert torch.allclose(h[:, 1], alone_h[:, 0], atol=1e-6)
    assert torch.allclose(c[:, 1], alone_c[:, 0], atol=1e-6)
    assert torch.allclose(out[1, :2], alone_out[0], atol=1e-6)


def test_final_state_is_last_real_token(encoder):
    out, (h, _) = encoder(*batch([4, 5, 6, 7], [8, 9]))
    # top layer h equals the output at position len - 1, not at the last padded position
    assert torch.allclose(h[-1, 0], out[0, 3], atol=1e-6)
    assert torch.allclose(h[-1, 1], out[1, 1], atol=1e-6)


def test_batch_order_is_kept(encoder):
    _, (h_ab, _) = encoder(*batch([8, 9], [4, 5, 6, 7]))
    _, (h_ba, _) = encoder(*batch([4, 5, 6, 7], [8, 9]))
    assert torch.allclose(h_ab[:, 0], h_ba[:, 1], atol=1e-6)


def test_gradients_flow(encoder):
    encoder.train()
    out, (h, c) = encoder(*batch([4, 5, 6], [8, 9]))
    (h.sum() + c.sum()).backward()
    assert encoder.embedding.weight.grad is not None
    assert torch.all(encoder.embedding.weight.grad[PAD_ID] == 0)  # padding_idx gets no update


@pytest.fixture
def decoder():
    torch.manual_seed(1)
    return Decoder(V_TGT, E, H, num_layers=L, dropout=0.3).eval()


def random_state(B):
    torch.manual_seed(2)
    return torch.randn(L, B, H), torch.randn(L, B, H)


def test_decoder_shapes(decoder):
    tgt_in = torch.tensor([[SOS_ID, 5, 6, 7], [SOS_ID, 8, PAD_ID, PAD_ID]])
    logits, (h, c) = decoder(tgt_in, random_state(2))
    assert logits.shape == (2, 4, V_TGT)
    assert h.shape == c.shape == (L, 2, H)


def test_step_by_step_equals_teacher_forcing(decoder):
    tgt_in = torch.tensor([[SOS_ID, 5, 6, 7], [SOS_ID, 8, 9, 10]])
    full, _ = decoder(tgt_in, random_state(2))
    state, steps = random_state(2), []
    for t in range(tgt_in.size(1)):
        logits, state = decoder.step(tgt_in[:, t], state)
        assert logits.shape == (2, V_TGT)
        steps.append(logits)
    assert torch.allclose(torch.stack(steps, dim=1), full, atol=1e-5)


def test_end_padding_does_not_change_real_positions(decoder):
    short, _ = decoder(torch.tensor([[SOS_ID, 5]]), random_state(1))
    padded, _ = decoder(torch.tensor([[SOS_ID, 5, PAD_ID, PAD_ID]]), random_state(1))
    assert torch.allclose(padded[:, :2], short, atol=1e-6)


def test_initial_state_matters(decoder):
    tgt_in = torch.tensor([[SOS_ID, 5]])
    a, _ = decoder(tgt_in, random_state(1))
    zeros = (torch.zeros(L, 1, H), torch.zeros(L, 1, H))
    b, _ = decoder(tgt_in, zeros)
    assert not torch.allclose(a, b)


def test_gradient_reaches_encoder_through_state(encoder, decoder):
    encoder.train()
    decoder.train()
    _, state = encoder(*batch([4, 5, 6], [8, 9]))
    logits, _ = decoder(torch.tensor([[SOS_ID, 5], [SOS_ID, 6]]), state)
    logits.sum().backward()
    assert encoder.embedding.weight.grad[4].abs().sum() > 0
