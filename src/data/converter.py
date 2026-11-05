"""Convert MASSIVE annotations into function calls.

    annot_utt:  wake me up at [time : five am] [date : this week]
    call:       alarm_set(time="five am", date="this week")
    tokens:     alarm_set ( time = " five am " , date = " this week " )

The function name is the intent, arguments are the slots in order of appearance
and values are copied verbatim. A slot name can repeat (food_type twice), it then
appears twice as an argument. <SOS>/<EOS> and language tags are added later with
the vocabulary, not here.

Inside a value, backslash and double quote are escaped as \\ and \". MASSIVE has
no such values, but the model can generate them.

Check the whole dataset (not part of pytest, it reads the raw data):
    python -m src.data.converter --check
"""

import argparse
import json
import re
import sys
from pathlib import Path

# same regex as notebooks/01_dataset_audit.ipynb
SLOT_RE = re.compile(r"\[\s*([^\[\]:]+?)\s*:\s*([^\[\]]*?)\s*\]")
NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

Slots = list[tuple[str, str]]


def tokenize(text: str) -> list[str]:
    """Whitespace tokenization, shared by utterances and slot values."""
    return text.split()


def parse_annot(annot_utt: str) -> Slots:
    """Return the (name, value) slots of an annotated utterance, in order.

    Raises ValueError on a bracket the regex did not match (e.g. "[time]")
    or on an empty value (e.g. "[time : ]").
    """
    slots = SLOT_RE.findall(annot_utt)
    if annot_utt.count("[") != len(slots) or annot_utt.count("]") != len(slots):
        raise ValueError(f"malformed slot annotation: {annot_utt!r}")
    for name, value in slots:
        if value == "":
            raise ValueError(f"empty value for slot {name!r}: {annot_utt!r}")
    return slots


def strip_annot(annot_utt: str) -> str:
    """Remove the slot markup and keep the values: should give back `utt`."""
    return SLOT_RE.sub(lambda m: m.group(2), annot_utt)


def escape(value: str) -> str:
    """Escape a value so it can sit between double quotes."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def to_call(intent: str, slots: Slots) -> str:
    """Build the call string, e.g. alarm_set(time="five am")."""
    args = ", ".join(f'{name}="{escape(value)}"' for name, value in slots)
    return f"{intent}({args})"


def to_target_tokens(intent: str, slots: Slots) -> list[str]:
    """Build the decoder target tokens (without <SOS>/<EOS>)."""
    tokens = [intent, "("]
    for i, (name, value) in enumerate(slots):
        if i > 0:
            tokens.append(",")
        tokens += [name, "=", '"', *tokenize(escape(value)), '"']
    tokens.append(")")
    return tokens


def tokens_to_call(tokens: list[str]) -> str:
    """Inverse of to_target_tokens: join decoded tokens into a call string.

    Words between quote tokens are joined with spaces. Any token list gives a
    string; a malformed one (e.g. no closing quote or ")") is rejected later by
    parse_call, so it counts as an invalid call instead of crashing.
    """
    parts, value, in_value = [], [], False
    for tok in tokens:
        if tok == '"':
            if in_value:
                parts.append('"' + " ".join(value) + '"')
                value = []
            in_value = not in_value
        elif in_value:
            value.append(tok)
        elif tok == ",":
            parts.append(", ")
        else:
            parts.append(tok)
    if in_value:  # unclosed quote, kept so parse_call sees it
        parts.append('"' + " ".join(value))
    return "".join(parts)


def parse_call(call: str) -> tuple[str, Slots]:
    """Parse a call string back into (intent, slots). Raises ValueError if malformed."""
    def fail(msg: str) -> ValueError:
        return ValueError(f"{msg} at position {pos}: {call!r}")

    pos = 0
    m = NAME_RE.match(call, pos)
    if not m:
        raise fail("expected function name")
    intent, pos = m.group(), m.end()
    if call[pos:pos + 1] != "(":
        raise fail("expected '('")
    pos += 1

    slots: Slots = []
    while True:
        while call[pos:pos + 1] == " ":
            pos += 1
        if call[pos:pos + 1] == ")":
            pos += 1
            break
        if slots:
            if call[pos:pos + 1] != ",":
                raise fail("expected ',' or ')'")
            pos += 1
            while call[pos:pos + 1] == " ":
                pos += 1

        m = NAME_RE.match(call, pos)
        if not m:
            raise fail("expected argument name")
        name, pos = m.group(), m.end()
        if call[pos:pos + 2] != '="':
            raise fail("expected '=\"'")
        pos += 2

        chars = []
        while True:
            if pos >= len(call):
                raise fail("unclosed quote")
            ch = call[pos]
            if ch == '"':
                pos += 1
                break
            if ch == "\\":
                nxt = call[pos + 1:pos + 2]
                if nxt not in ("\\", '"'):
                    raise fail("bad escape")
                chars.append(nxt)
                pos += 2
            else:
                chars.append(ch)
                pos += 1
        if not chars:
            raise fail(f"empty value for {name!r}")
        slots.append((name, "".join(chars)))

    if pos != len(call):
        raise fail("unexpected text after ')'")
    return intent, slots


def convert_row(row: dict) -> dict:
    """Convert one MASSIVE row (as saved by download_massive) into model inputs/targets."""
    slots = parse_annot(row["annot_utt"])
    return {
        "id": row["id"],
        "locale": row["locale"],
        "utt": row["utt"],
        "src_tokens": tokenize(row["utt"]),
        "intent": row["intent"],
        "slots": slots,
        "call": to_call(row["intent"], slots),
        "target_tokens": to_target_tokens(row["intent"], slots),
    }


def _contains(seq: list[str], sub: list[str]) -> bool:
    return any(seq[i:i + len(sub)] == sub for i in range(len(seq) - len(sub) + 1))


def check(data_dir: Path, locales: list[str], splits: list[str]) -> bool:
    """Run the converter on every row and print counts. Returns True if all rows pass."""
    print(f"{'locale':<7} {'split':<6} {'rows':>6} {'errors':>6} {'strip!=utt':>10} "
          f"{'roundtrip':>9} {'slots':>6} {'empty':>5} {'copyable':>8}")
    ok = True
    for loc in locales:
        for split in splits:
            path = data_dir / loc / f"{split}.jsonl"
            with path.open(encoding="utf-8") as f:
                rows = [json.loads(line) for line in f]
            errors = bad_strip = bad_trip = n_slots = n_empty = copyable = 0
            for row in rows:
                if re.search(r":\s*\]", row["annot_utt"]):
                    n_empty += 1
                try:
                    ex = convert_row(row)
                except ValueError as e:
                    errors += 1
                    print("  error:", e)
                    continue
                if strip_annot(row["annot_utt"]) != row["utt"]:
                    bad_strip += 1
                # call -> parse back, and target tokens -> call string
                if (parse_call(ex["call"]) != (ex["intent"], ex["slots"])
                        or tokens_to_call(ex["target_tokens"]) != ex["call"]):
                    bad_trip += 1
                for _, value in ex["slots"]:
                    n_slots += 1
                    # value tokens appear as a contiguous span of the utterance tokens
                    copyable += _contains(ex["src_tokens"], tokenize(value))
            ok &= errors == bad_strip == bad_trip == 0
            print(f"{loc:<7} {split:<6} {len(rows):>6} {errors:>6} {bad_strip:>10} "
                  f"{bad_trip:>9} {n_slots:>6} {n_empty:>5} {copyable:>8}")
    print("all rows pass" if ok else "some rows FAILED")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="convert every row and verify it")
    parser.add_argument("--data-dir", type=Path, default=Path("data/massive"))
    parser.add_argument("--locales", nargs="+", default=["en-US", "fr-FR", "ar-SA"])
    parser.add_argument("--splits", nargs="+", default=["train", "dev", "test"])
    args = parser.parse_args()
    if not args.check:
        parser.print_help()
        return
    sys.exit(0 if check(args.data_dir, args.locales, args.splits) else 1)


if __name__ == "__main__":
    main()
