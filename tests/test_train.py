"""Smoke tests for src/training/train.py: the 5 fixture rows, tiny models, CPU."""

import pytest
import torch
from torch import nn

from src.data.converter import parse_call
from src.data.dataset import MassiveDataset, make_loader
from src.data.vocab import PAD_ID, build_vocabs
from src.training.train import build_model, eval_loss, predict, train_epoch


def cfg(model_type):
    return {"model": {"type": model_type, "emb_dim": 8, "hidden_dim": 16, "num_layers": 1,
                      "dropout": 0.0, "attn_dim": 8}}


@pytest.mark.parametrize("model_type", ["lstm", "attn", "copy"])
def test_loss_goes_down_and_predict_runs(rows, model_type):
    torch.manual_seed(0)
    src_vocab, tgt_vocab = build_vocabs(rows, min_freq=1)
    ds = MassiveDataset(rows, src_vocab, tgt_vocab, lang_tag=True)
    loader = make_loader(ds, batch_size=2, shuffle=True, seed=0)
    model = build_model(cfg(model_type), len(src_vocab), len(tgt_vocab))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_ID, reduction="sum")
    device = torch.device("cpu")

    first = eval_loss(model, loader, loss_fn, device, tgt_vocab)
    for _ in range(20):
        train_epoch(model, loader, optimizer, loss_fn, device, 1.0, tgt_vocab)
    assert eval_loss(model, loader, loss_fn, device, tgt_vocab) < first / 2

    for beam_size in (1, 3):
        preds = predict(model, make_loader(ds, 5, shuffle=False), tgt_vocab, device, max_len=12, beam_size=beam_size)
        assert [p["id"] for p in preds] == [r["id"] for r in rows]
        assert all(isinstance(p["pred"], str) for p in preds)


def test_copy_model_produces_values_missing_from_target_vocab(rows):
    # target min_freq 3 keeps no value words, so a model without copy can only write <UNK>.
    # The copy model must write real source words instead. Exact alignment is not checked
    # here: at this tiny size the attention tanh saturates and ties two adjacent value
    # words (e.g. "am am"). The real-size check is configs/e2_overfit100.yaml (100% EM).
    torch.manual_seed(0)
    src_vocab, _ = build_vocabs(rows, min_freq=1)
    _, tgt_vocab = build_vocabs(rows, min_freq=3)
    assert "five" not in tgt_vocab and "am" not in tgt_vocab
    ds = MassiveDataset(rows, src_vocab, tgt_vocab, lang_tag=True)
    loader = make_loader(ds, batch_size=5, shuffle=True, seed=0)
    model = build_model(cfg("copy"), len(src_vocab), len(tgt_vocab))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.02)
    loss_fn = nn.CrossEntropyLoss(ignore_index=PAD_ID, reduction="sum")
    for _ in range(150):
        train_epoch(model, loader, optimizer, loss_fn, torch.device("cpu"), 1.0, tgt_vocab)
    preds = predict(model, make_loader(ds, 5, shuffle=False), tgt_vocab, torch.device("cpu"), max_len=16)

    for p, row in zip(preds, rows):
        intent, slots = parse_call(p["pred"])
        assert intent == row["intent"] and [n for n, _ in slots] == [n for n, _ in row["slots"]]
        for _, value in slots:
            words = value.split()
            assert "<UNK>" not in words
            assert all(w in row["src_tokens"] and w not in tgt_vocab for w in words)


def test_plot_curves_writes_png_without_touching_pyplot_backend(tmp_path):
    import matplotlib

    from src.training.train import plot_curves
    backend = matplotlib.get_backend()
    history = [{"epoch": e, "train_loss": 1 / e, "eval_loss": 1.2 / e, "eval_em": e / 10} for e in (1, 2, 3)]
    plot_curves(history, tmp_path / "curves.png")
    assert (tmp_path / "curves.png").stat().st_size > 1000
    assert matplotlib.get_backend() == backend
