"""Unit tests for src/models/copy.py (pointer-generator, tiny sizes)."""

import torch

from src.data.vocab import PAD_ID, SOS_ID, SPECIALS, SYNTAX_TOKENS, UNK_ID, Vocab
from src.inference.greedy import greedy_decode, ids_to_calls
from src.models.copy import CopySeq2Seq, extend_batch

# target vocab without "five" and "paris": they can only be copied
TGT = Vocab(SPECIALS + SYNTAX_TOKENS + ["alarm_set", "weather_query", "time", "place_name", "am"])
V = len(TGT)
BATCH = {
    "src_tokens": [["<en>", "wake", "me", "at", "five", "am"], ["<en>", "weather", "in", "paris"]],
    "call": ['alarm_set(time="five am")', 'weather_query(place_name="paris")'],
}


def test_extend_batch_ids():
    ext = extend_batch(BATCH, TGT)
    assert ext["oovs"] == [["<en>", "wake", "me", "at", "five"], ["<en>", "weather", "in", "paris"]]
    assert ext["n_oov"] == 5
    assert ext["src_ext"][0].tolist() == [V, V + 1, V + 2, V + 3, V + 4, TGT.stoi["am"]]
    assert ext["src_ext"][1].tolist() == [V, V + 1, V + 2, V + 3, PAD_ID, PAD_ID]
    # "five" -> its extended id, "am" stays a normal id
    five_am = ext["tgt_ext"][0].tolist()
    assert five_am[0] == SOS_ID and V + 4 in five_am and TGT.stoi["am"] in five_am


def test_target_word_not_in_source_stays_unk():
    batch = {"src_tokens": [["set", "an", "alarm"]], "call": ['alarm_set(time="five am")']}
    tgt = extend_batch(batch, TGT)["tgt_ext"][0].tolist()
    assert UNK_ID in tgt  # "five" is neither in the vocab nor in this source


def tiny_model():
    torch.manual_seed(0)
    return CopySeq2Seq(30, V, emb_dim=8, hidden_dim=16, num_layers=2, dropout=0.3, attn_dim=10).eval()


def inputs():
    ext = extend_batch(BATCH, TGT)
    src = torch.tensor([[4, 5, 6, 7, 8, 9], [4, 10, 11, 12, PAD_ID, PAD_ID]])
    return src, torch.tensor([6, 4]), ext


def test_distribution_sums_to_one_over_extended_vocab():
    model = tiny_model()
    src, lens, ext = inputs()
    tgt_in = ext["tgt_ext"][:, :-1]
    log_probs, attn, p_gen = model(src, lens, tgt_in, ext["src_ext"], ext["n_oov"], return_attn=True)
    assert log_probs.shape == (2, tgt_in.size(1), V + ext["n_oov"])
    assert torch.allclose(log_probs.exp().sum(-1), torch.ones(2, tgt_in.size(1)), atol=1e-5)
    assert attn.shape == (2, tgt_in.size(1), 6) and p_gen.shape == (2, tgt_in.size(1))
    assert torch.all((p_gen > 0) & (p_gen < 1))


def test_pure_copy_puts_all_mass_on_source_words():
    model = tiny_model()
    with torch.no_grad():
        model.gen.bias.fill_(-1e4)  # p_gen = 0
    src, lens, ext = inputs()
    state = model.start(src, lens, ext["src_ext"], ext["n_oov"])
    log_probs, _ = model.step(torch.full((2,), SOS_ID), state)
    probs = log_probs.exp()
    in_src = torch.zeros_like(probs, dtype=torch.bool).scatter(1, ext["src_ext"], True)
    in_src[1, PAD_ID] = False  # padding positions have zero attention
    assert torch.allclose(probs[in_src.logical_not()].sum(), torch.tensor(0.0), atol=1e-5)


def test_pure_generation_equals_attention_model_softmax():
    model = tiny_model()
    with torch.no_grad():
        model.gen.bias.fill_(1e4)  # p_gen = 1
    src, lens, ext = inputs()
    state = model.start(src, lens, ext["src_ext"], ext["n_oov"])
    log_probs, _ = model.step(torch.full((2,), SOS_ID), state)
    logits, _ = super(CopySeq2Seq, model).step(torch.full((2,), SOS_ID), state[:5])
    assert torch.allclose(log_probs[:, :V].exp(), torch.softmax(logits, -1), atol=1e-5)
    assert torch.all(log_probs[:, V:].exp() < 1e-6)


def test_copied_oov_word_is_fed_back_and_decoded():
    model = tiny_model()
    with torch.no_grad():
        model.gen.bias.fill_(-1e4)
    src, lens, ext = inputs()
    ids = greedy_decode(model, src, lens, max_len=4, src_ext=ext["src_ext"], n_oov=ext["n_oov"])
    # pure copy: every predicted id is one of that row's own source ids, OOV ids included,
    # and feeding an id >= V back into the decoder works
    for row, src_ids in zip(ids.tolist(), ext["src_ext"].tolist()):
        assert set(row) <= set(src_ids)  # no <EOS> in the source, so it runs to max_len
    assert ids.max() >= V


def test_ids_to_calls_maps_extended_ids():
    row = [TGT.stoi[t] for t in ["alarm_set", "(", "time", "=", '"']] + [V + 4, TGT.stoi["am"]] + \
          [TGT.stoi[t] for t in ['"', ")", "<EOS>"]]
    oovs = [["<en>", "wake", "me", "at", "five"]]  # id V + 4 is "five"
    assert ids_to_calls(torch.tensor([row]), TGT, oovs) == ['alarm_set(time="five am")']


def test_gradients_reach_gen_and_attention():
    model = tiny_model().train()
    src, lens, ext = inputs()
    tgt = ext["tgt_ext"]
    log_probs = model(src, lens, tgt[:, :-1], ext["src_ext"], ext["n_oov"])
    loss = torch.nn.functional.nll_loss(log_probs.reshape(-1, log_probs.size(-1)), tgt[:, 1:].reshape(-1),
                                        ignore_index=PAD_ID)
    loss.backward()
    assert model.gen.weight.grad.abs().sum() > 0
    assert model.decoder.attention.v.weight.grad.abs().sum() > 0
