"""Unit tests for src/data/dataset.py."""

import torch

from src.data.dataset import MassiveDataset, collate, make_loader
from src.data.vocab import EOS_ID, PAD_ID, SOS_ID, build_vocabs


def make(rows, **kwargs):
    src_vocab, tgt_vocab = build_vocabs(rows, min_freq=1)
    return MassiveDataset(rows, src_vocab, tgt_vocab, **kwargs), src_vocab, tgt_vocab


def test_item_ids_match_tokens(rows):
    ds, src_vocab, tgt_vocab = make(rows)
    item = ds[0]
    assert item["src_tokens"] == ["wake", "me", "up", "at", "five", "am"]
    assert src_vocab.decode(item["src_ids"].tolist()) == item["src_tokens"]
    assert item["tgt_ids"][0] == SOS_ID and item["tgt_ids"][-1] == EOS_ID
    assert tgt_vocab.decode(item["tgt_ids"].tolist()) == rows[0]["target_tokens"]


def test_lang_tag_prepended_and_aligned(rows):
    ds, src_vocab, _ = make(rows, lang_tag=True)
    assert [ds[i]["src_tokens"][0] for i in range(len(ds))] == ["<en>", "<en>", "<en>", "<fr>", "<ar>"]
    # raw tokens and ids stay aligned position by position (needed for copy)
    for item in ds:
        assert len(item["src_tokens"]) == len(item["src_ids"])
        assert item["src_ids"][0] == src_vocab.stoi[item["src_tokens"][0]]


def test_source_truncation(rows):
    ds, _, _ = make(rows, max_src_len=3, lang_tag=True)
    assert ds[0]["src_tokens"] == ["<en>", "wake", "me"]
    assert len(ds[0]["src_ids"]) == 3


def test_drop_long_targets_only_when_asked(rows):
    # alarm_set targets are 11 tokens with <SOS>/<EOS>, alarm_query is 5
    ds, _, _ = make(rows, max_tgt_len=6, drop_long_targets=True)
    assert len(ds) == 1 and ds.n_dropped == 4
    ds, _, _ = make(rows, max_tgt_len=6)
    assert len(ds) == 5 and ds.n_dropped == 0
    assert max(len(item["tgt_ids"]) for item in ds) == 11  # not truncated either


def test_collate_shapes_and_padding(rows):
    ds, _, _ = make(rows)
    batch = collate([ds[0], ds[2], ds[4]])
    assert batch["src"].shape == (3, 6)
    assert batch["src_lens"].tolist() == [6, 5, 3]
    assert batch["tgt"].shape == (3, 11)
    assert batch["src"][2, 3:].tolist() == [PAD_ID] * 3
    assert batch["tgt"][1, 5:].tolist() == [PAD_ID] * 6
    assert batch["src_tokens"][2] == ["صحيني", "تسعة", "الصباح"]
    assert batch["call"][1] == "alarm_query()"
    assert batch["src"].dtype == torch.long


def test_loader_shuffle_is_reproducible(rows):
    ds, _, _ = make(rows)
    order = lambda: [i for b in make_loader(ds, batch_size=2, shuffle=True, seed=7) for i in b["id"]]
    assert order() == order()
    assert sorted(order()) == sorted(r["id"] for r in rows)
