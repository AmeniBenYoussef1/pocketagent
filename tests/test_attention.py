"""Unit tests for the BiLSTM encoder, Bahdanau attention and AttnSeq2Seq (tiny sizes)."""

import pytest
import torch

from src.data.vocab import PAD_ID, SOS_ID
from src.inference.greedy import greedy_decode
from src.models.attention import BahdanauAttention
from src.models.attention_seq2seq import AttnSeq2Seq
from src.models.encoder import Encoder

V_SRC, V_TGT, E, H, L, A = 20, 12, 8, 16, 2, 10
DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


def batch(*seqs, device="cpu"):
    T = max(len(s) for s in seqs)
    src = torch.tensor([s + [PAD_ID] * (T - len(s)) for s in seqs], device=device)
    return src, torch.tensor([len(s) for s in seqs])


def tiny_model(device="cpu"):
    torch.manual_seed(0)
    return AttnSeq2Seq(V_SRC, V_TGT, E, H, L, dropout=0.3, attn_dim=A).to(device).eval()


def test_bilstm_encoder_shapes_and_padding():
    torch.manual_seed(0)
    enc = Encoder(V_SRC, E, H, L, bidirectional=True).eval()
    out, (h, c) = enc(*batch([4, 5, 6, 7], [8, 9]))
    assert enc.out_dim == 2 * H
    assert out.shape == (2, 4, 2 * H) and h.shape == (2 * L, 2, H)
    assert torch.all(out[1, 2:] == 0)
    # backward direction starts at the last real token, so padding changes nothing
    alone, (h_alone, _) = enc(*batch([8, 9]))
    assert torch.allclose(out[1, :2], alone[0], atol=1e-6)
    assert torch.allclose(h[:, 1], h_alone[:, 0], atol=1e-6)


def test_attention_weights_and_context():
    torch.manual_seed(0)
    attn = BahdanauAttention(2 * H, H, A)
    enc_out = torch.randn(2, 5, 2 * H)
    mask = torch.tensor([[True] * 5, [True, True, True, False, False]])
    context, weights = attn(torch.randn(2, H), attn.project_keys(enc_out), enc_out, mask)
    assert context.shape == (2, 2 * H) and weights.shape == (2, 5)
    assert torch.allclose(weights.sum(-1), torch.ones(2))
    assert torch.all(weights[1, 3:] == 0)
    assert torch.allclose(context[1], (weights[1, :, None] * enc_out[1]).sum(0), atol=1e-6)


def test_masked_positions_do_not_affect_context():
    torch.manual_seed(0)
    attn = BahdanauAttention(2 * H, H, A)
    enc_out, query = torch.randn(1, 4, 2 * H), torch.randn(1, H)
    mask = torch.tensor([[True, True, False, False]])
    a, _ = attn(query, attn.project_keys(enc_out), enc_out, mask)
    enc_out2 = enc_out.clone()
    enc_out2[0, 2:] = 100.0
    b, _ = attn(query, attn.project_keys(enc_out2), enc_out2, mask)
    assert torch.allclose(a, b, atol=1e-6)


def test_forward_shapes_and_attention_rows():
    model = tiny_model()
    src, lens = batch([4, 5, 6, 7], [8, 9])
    tgt_in = torch.tensor([[SOS_ID, 5, 6], [SOS_ID, 7, PAD_ID]])
    logits, attn = model(src, lens, tgt_in, return_attn=True)
    assert logits.shape == (2, 3, V_TGT)
    assert attn.shape == (2, 3, 4)
    assert torch.allclose(attn.sum(-1), torch.ones(2, 3), atol=1e-6)
    assert torch.all(attn[1, :, 2:] == 0)


def test_source_padding_does_not_change_logits():
    model = tiny_model()
    tgt_in = torch.tensor([[SOS_ID, 5, 6]])
    alone = model(*batch([8, 9]), tgt_in)
    src, lens = batch([4, 5, 6, 7, 10], [8, 9])
    padded = model(src, lens, torch.cat([tgt_in, tgt_in]))
    assert torch.allclose(padded[1], alone[0], atol=1e-5)


def test_first_greedy_token_matches_forward():
    model = tiny_model()
    src, lens = batch([4, 5, 6], [8, 9])
    logits = model(src, lens, torch.full((2, 1), SOS_ID))
    out = greedy_decode(model, src, lens, max_len=1)
    assert torch.equal(out[:, 0], logits[:, 0].argmax(-1))


@pytest.mark.parametrize("device", DEVICES)
def test_greedy_runs_on_device(device):
    model = tiny_model(device)
    out = greedy_decode(model, *batch([4, 5, 6], [8, 9], device=device), max_len=5)
    assert out.shape[0] == 2 and out.shape[1] <= 5 and out.device.type == device


def test_gradients_reach_attention_bridge_and_encoder():
    model = tiny_model().train()
    src, lens = batch([4, 5, 6], [8, 9])
    model(src, lens, torch.tensor([[SOS_ID, 5], [SOS_ID, 6]])).sum().backward()
    for p in [model.decoder.attention.W_enc.weight, model.decoder.attention.v.weight,
              model.bridge_h.weight, model.encoder.embedding.weight]:
        assert p.grad is not None and p.grad.abs().sum() > 0
