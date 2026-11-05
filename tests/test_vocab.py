"""Unit tests for src/data/vocab.py."""

from collections import Counter

import pytest

from src.data.vocab import (
    EOS_ID, PAD_ID, SOS_ID, SPECIALS, SYNTAX_TOKENS, UNK_ID, Vocab, build_vocabs, unk_rate, value_tokens,
)


def test_special_ids_are_fixed(rows):
    for vocab in build_vocabs(rows, min_freq=2):
        assert vocab.itos[:4] == SPECIALS
        assert (vocab.stoi["<PAD>"], vocab.stoi["<UNK>"], vocab.stoi["<SOS>"], vocab.stoi["<EOS>"]) == (
            PAD_ID, UNK_ID, SOS_ID, EOS_ID)


def test_min_freq_cutoff():
    vocab = Vocab.build(Counter({"a": 3, "b": 2, "c": 1}), min_freq=2, reserved=[])
    assert "a" in vocab and "b" in vocab and "c" not in vocab


def test_order_is_frequency_then_alphabetical():
    vocab = Vocab.build(Counter({"z": 5, "b": 2, "a": 2}), min_freq=1, reserved=["<en>"])
    assert vocab.itos[4:] == ["<en>", "z", "a", "b"]


def test_language_tags_in_source_vocab(rows):
    src_vocab, tgt_vocab = build_vocabs(rows, min_freq=2)
    assert src_vocab.itos[4:7] == ["<en>", "<fr>", "<ar>"]
    assert "<en>" not in tgt_vocab


def test_intents_slots_syntax_always_in_target(rows):
    _, tgt_vocab = build_vocabs(rows, min_freq=100)
    for tok in SYNTAX_TOKENS + ["alarm_set", "alarm_query", "time"]:
        assert tok in tgt_vocab
    # value words below min_freq are not
    assert "five" not in tgt_vocab


def test_frequent_value_word_in_target(rows):
    _, tgt_vocab = build_vocabs(rows, min_freq=2)
    assert "am" in tgt_vocab  # "five am" and "six am"
    assert "five" not in tgt_vocab


def test_unknown_maps_to_unk(rows):
    src_vocab, _ = build_vocabs(rows, min_freq=2)
    assert src_vocab.encode(["wake", "zzz"]) == [src_vocab.stoi["wake"], UNK_ID]


def test_decode_skips_pad_sos_and_stops_at_eos(rows):
    _, tgt_vocab = build_vocabs(rows, min_freq=1)
    ids = [SOS_ID] + tgt_vocab.encode(["alarm_query", "(", ")"]) + [EOS_ID, PAD_ID, tgt_vocab.stoi["time"]]
    assert tgt_vocab.decode(ids) == ["alarm_query", "(", ")"]


def test_encode_decode_round_trip_arabic(rows):
    src_vocab, _ = build_vocabs(rows, min_freq=1)
    tokens = rows[4]["src_tokens"]
    assert src_vocab.decode(src_vocab.encode(tokens)) == tokens


def test_save_load(rows, tmp_path):
    src_vocab, _ = build_vocabs(rows, min_freq=1)
    src_vocab.save(tmp_path / "src_vocab.json")
    assert Vocab.load(tmp_path / "src_vocab.json").itos == src_vocab.itos


def test_bad_vocab_raises():
    with pytest.raises(ValueError):
        Vocab(["a", "b"])
    with pytest.raises(ValueError):
        Vocab(SPECIALS + ["a", "a"])


def test_unk_rate_and_value_tokens(rows):
    assert value_tokens(rows[0]) == ["five", "am"]
    assert value_tokens(rows[2]) == []
    vocab = Vocab.build(Counter({"am": 1}), min_freq=1, reserved=[])
    assert unk_rate(vocab, [["five", "am"]]) == 50.0
    assert unk_rate(vocab, []) == 0.0
