"""Source and target vocabularies, fitted on the train split only.

Ids 0-3 are always <PAD> <UNK> <SOS> <EOS>. The source vocabulary then holds the
three language tags, the target vocabulary the call syntax ( ) = " , plus every
intent and slot name seen in train, whatever their frequency. Other tokens are
kept if they appear at least min_freq times, ordered by frequency then
alphabetically so ids are reproducible.

Report vocabulary sizes and dev <UNK> rates:
    python -m src.data.vocab --report
"""

import argparse
import json
from collections import Counter
from pathlib import Path

from src.data.converter import escape, tokenize

PAD, UNK, SOS, EOS = "<PAD>", "<UNK>", "<SOS>", "<EOS>"
SPECIALS = [PAD, UNK, SOS, EOS]
PAD_ID, UNK_ID, SOS_ID, EOS_ID = 0, 1, 2, 3
LANG_TAGS = {"en-US": "<en>", "fr-FR": "<fr>", "ar-SA": "<ar>"}
SYNTAX_TOKENS = ["(", ")", "=", '"', ","]


class Vocab:
    """Token <-> id mapping. Unknown tokens map to <UNK>."""

    def __init__(self, itos: list[str]):
        if itos[:4] != SPECIALS:
            raise ValueError("vocabulary must start with <PAD> <UNK> <SOS> <EOS>")
        self.itos = list(itos)
        self.stoi = {tok: i for i, tok in enumerate(self.itos)}
        if len(self.stoi) != len(self.itos):
            raise ValueError("duplicate tokens in vocabulary")

    @classmethod
    def build(cls, counts: Counter, min_freq: int, reserved: list[str]) -> "Vocab":
        """Specials, then reserved tokens (always kept), then tokens with count >= min_freq."""
        reserved = list(dict.fromkeys(reserved))
        kept = set(SPECIALS) | set(reserved)
        frequent = [t for t, c in counts.items() if c >= min_freq and t not in kept]
        frequent.sort(key=lambda t: (-counts[t], t))
        return cls(SPECIALS + reserved + frequent)

    def __len__(self) -> int:
        return len(self.itos)

    def __contains__(self, token: str) -> bool:
        return token in self.stoi

    def encode(self, tokens: list[str]) -> list[int]:
        return [self.stoi.get(t, UNK_ID) for t in tokens]

    def decode(self, ids: list[int]) -> list[str]:
        """Ids to tokens, skipping <PAD>/<SOS> and stopping at <EOS>."""
        tokens = []
        for i in ids:
            if i == EOS_ID:
                break
            if i not in (PAD_ID, SOS_ID):
                tokens.append(self.itos[i])
        return tokens

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps({"itos": self.itos}, ensure_ascii=False, indent=0), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Vocab":
        return cls(json.loads(Path(path).read_text(encoding="utf-8"))["itos"])


def build_vocabs(train_rows: list[dict], min_freq: int = 2) -> tuple[Vocab, Vocab]:
    """Fit (source, target) vocabularies on converted train rows.

    Pass the rows of one locale for a per-locale model, or of all locales for the joint one.
    """
    src_counts = Counter(t for row in train_rows for t in row["src_tokens"])
    tgt_counts = Counter(t for row in train_rows for t in row["target_tokens"])
    intents = sorted({row["intent"] for row in train_rows})
    slot_names = sorted({name for row in train_rows for name, _ in row["slots"]})

    src_vocab = Vocab.build(src_counts, min_freq, reserved=list(LANG_TAGS.values()))
    tgt_vocab = Vocab.build(tgt_counts, min_freq, reserved=SYNTAX_TOKENS + intents + slot_names)
    return src_vocab, tgt_vocab


def value_tokens(row: dict) -> list[str]:
    """Target tokens that come from slot values (the only target tokens that can be <UNK>)."""
    return [t for _, value in row["slots"] for t in tokenize(escape(value))]


def unk_rate(vocab: Vocab, token_lists: list[list[str]]) -> float:
    """Percentage of tokens not in the vocabulary."""
    total = sum(len(toks) for toks in token_lists)
    unk = sum(t not in vocab for toks in token_lists for t in toks)
    return 100 * unk / total if total else 0.0


def report(data_dir: Path, locales: list[str], min_freq: int) -> None:
    """Print vocabulary sizes and dev <UNK> rates, per locale and joint."""
    from src.data.dataset import MAX_TGT_LEN, load_split  # here to avoid a circular import

    train = {loc: load_split(data_dir, [loc], "train") for loc in locales}
    dev = {loc: load_split(data_dir, [loc], "dev") for loc in locales}
    test = {loc: load_split(data_dir, [loc], "test") for loc in locales}

    print(f"min_freq = {min_freq}, source <UNK> rate on utterance tokens, "
          f"target <UNK> rate on slot value tokens (dev)\n")
    print(f"{'vocab':<7} {'locale':<7} {'src size':>8} {'tgt size':>8} {'src unk':>8} {'tgt unk':>8}")
    setups = [(loc, [loc]) for loc in locales] + [("joint", locales)]
    for name, locs in setups:
        src_vocab, tgt_vocab = build_vocabs([r for loc in locs for r in train[loc]], min_freq)
        for loc in locs:
            src_unk = unk_rate(src_vocab, [r["src_tokens"] for r in dev[loc]])
            tgt_unk = unk_rate(tgt_vocab, [value_tokens(r) for r in dev[loc]])
            print(f"{name:<7} {loc:<7} {len(src_vocab):>8} {len(tgt_vocab):>8} "
                  f"{src_unk:>7.1f}% {tgt_unk:>7.1f}%")

    print(f"\ntarget length with <SOS>/<EOS> (train examples above {MAX_TGT_LEN} are dropped)")
    print(f"{'locale':<7} {'train max':>9} {'dropped':>7} {'dev max':>7} {'test max':>8}")
    for loc in locales:
        tlen = {split: [len(r["target_tokens"]) + 2 for r in rows[loc]]
                for split, rows in [("train", train), ("dev", dev), ("test", test)]}
        dropped = sum(n > MAX_TGT_LEN for n in tlen["train"])
        print(f"{loc:<7} {max(tlen['train']):>9} {dropped:>7} {max(tlen['dev']):>7} {max(tlen['test']):>8}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", action="store_true", help="print sizes and dev <UNK> rates")
    parser.add_argument("--data-dir", type=Path, default=Path("data/massive"))
    parser.add_argument("--locales", nargs="+", default=list(LANG_TAGS))
    parser.add_argument("--min-freq", type=int, default=2)
    args = parser.parse_args()
    if args.report:
        report(args.data_dir, args.locales, args.min_freq)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
