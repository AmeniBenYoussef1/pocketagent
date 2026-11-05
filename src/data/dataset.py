"""MASSIVE Dataset and DataLoader for the encoder-decoder.

One item:
    src_tokens  [<fr>] + utterance tokens, truncated to max_src_len (kept for the copy mechanism)
    src_ids     ids of src_tokens, same length and positions
    tgt_ids     <SOS> + call tokens + <EOS>

A batch is padded with <PAD> (id 0):
    src       (B, T_src)
    src_lens  (B,)
    tgt       (B, T_tgt)   training uses tgt[:, :-1] as decoder input and tgt[:, 1:] as output
"""

import json
from pathlib import Path

import torch
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset

from src.data.converter import convert_row
from src.data.vocab import EOS, LANG_TAGS, PAD_ID, SOS, Vocab

MAX_SRC_LEN = 32
MAX_TGT_LEN = 40  # p99.9 of train targets is 37-38
MAX_GEN_LEN = 48  # decoder limit at inference, above MAX_TGT_LEN so long dev/test calls are not cut


def load_split(data_dir: Path, locales: list[str], split: str) -> list[dict]:
    """Read data/massive/<locale>/<split>.jsonl for each locale and convert every row."""
    rows = []
    for loc in locales:
        with (Path(data_dir) / loc / f"{split}.jsonl").open(encoding="utf-8") as f:
            rows += [convert_row(json.loads(line)) for line in f]
    return rows


class MassiveDataset(Dataset):
    """Converted MASSIVE rows encoded with the source and target vocabularies.

    drop_long_targets: skip examples whose target is longer than max_tgt_len.
    Use it for train only; dev and test are never filtered.
    """

    def __init__(
        self,
        rows: list[dict],
        src_vocab: Vocab,
        tgt_vocab: Vocab,
        max_src_len: int = MAX_SRC_LEN,
        max_tgt_len: int = MAX_TGT_LEN,
        lang_tag: bool = False,
        drop_long_targets: bool = False,
    ):
        self.items = []
        self.n_dropped = 0
        for row in rows:
            tgt_tokens = [SOS] + row["target_tokens"] + [EOS]
            if drop_long_targets and len(tgt_tokens) > max_tgt_len:
                self.n_dropped += 1
                continue
            src_tokens = ([LANG_TAGS[row["locale"]]] if lang_tag else []) + row["src_tokens"]
            src_tokens = src_tokens[:max_src_len]
            self.items.append({
                "id": row["id"],
                "locale": row["locale"],
                "utt": row["utt"],
                "call": row["call"],
                "src_tokens": src_tokens,
                "src_ids": torch.tensor(src_vocab.encode(src_tokens), dtype=torch.long),  # (T_src,)
                "tgt_ids": torch.tensor(tgt_vocab.encode(tgt_tokens), dtype=torch.long),  # (T_tgt,)
            })

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, i: int) -> dict:
        return self.items[i]


def collate(batch: list[dict]) -> dict:
    """Pad a list of items into batch tensors (both vocabularies use <PAD> = 0)."""
    src = pad_sequence([b["src_ids"] for b in batch], batch_first=True, padding_value=PAD_ID)  # (B, T_src)
    tgt = pad_sequence([b["tgt_ids"] for b in batch], batch_first=True, padding_value=PAD_ID)  # (B, T_tgt)
    src_lens = torch.tensor([len(b["src_ids"]) for b in batch], dtype=torch.long)  # (B,)
    return {
        "src": src,
        "src_lens": src_lens,
        "tgt": tgt,
        "src_tokens": [b["src_tokens"] for b in batch],
        "id": [b["id"] for b in batch],
        "locale": [b["locale"] for b in batch],
        "utt": [b["utt"] for b in batch],
        "call": [b["call"] for b in batch],
    }


def make_loader(dataset: MassiveDataset, batch_size: int, shuffle: bool, seed: int = 0) -> DataLoader:
    """DataLoader with a seeded generator so the shuffle order is reproducible."""
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle,
                      collate_fn=collate, generator=generator)
