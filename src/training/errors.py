"""Sort a wrong prediction into one error type.

The first category that applies wins, in this order:

    invalid call        does not parse
    wrong intent        parses, wrong function name
    missing slot        right intent, some gold argument names missing
    extra slot          right intent, argument names not in gold
    wrong slot names    both missing and extra names
    value with <UNK>    names right, a wrong value contains <UNK>
    repeated copy       names right, a wrong value repeats a word ("am am") that gold doesn't repeat
    value partly wrong  names right, a wrong value shares words with the gold value
    value wrong         names right, a wrong value shares no word with the gold value

Argument order is ignored, as in exact_match.
"""

from collections import Counter

from src.training.metrics import safe_parse

CATEGORIES = ["correct", "invalid call", "wrong intent", "missing slot", "extra slot",
              "wrong slot names", "value with <UNK>", "repeated copy", "value partly wrong", "value wrong"]


def _has_repeat(words: list[str]) -> set[str]:
    return {a for a, b in zip(words, words[1:]) if a == b}


def wrong_value_pairs(pred_slots: list[tuple[str, str]], gold_slots: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """(pred value, gold value) pairs that differ, matched by slot name in order of appearance."""
    pairs = []
    for name in dict.fromkeys(n for n, _ in gold_slots):
        p = [v for n, v in pred_slots if n == name]
        g = [v for n, v in gold_slots if n == name]
        # values that appear on both sides are right whatever their position
        p_left = list((Counter(p) - Counter(g)).elements())
        g_left = list((Counter(g) - Counter(p)).elements())
        pairs += list(zip(p_left, g_left))
    return pairs


def classify(pred: str, gold: str) -> str:
    """Error type of one prediction (or "correct")."""
    gold_intent, gold_slots = safe_parse(gold)
    parsed = safe_parse(pred)
    if parsed is None:
        return "invalid call"
    intent, slots = parsed
    if intent != gold_intent:
        return "wrong intent"
    if Counter(slots) == Counter(gold_slots):
        return "correct"

    pred_names, gold_names = Counter(n for n, _ in slots), Counter(n for n, _ in gold_slots)
    missing, extra = gold_names - pred_names, pred_names - gold_names
    if missing and extra:
        return "wrong slot names"
    if missing:
        return "missing slot"
    if extra:
        return "extra slot"

    pairs = wrong_value_pairs(slots, gold_slots)
    if any("<UNK>" in p.split() for p, _ in pairs):
        return "value with <UNK>"
    if any(_has_repeat(p.split()) - _has_repeat(g.split()) for p, g in pairs):
        return "repeated copy"
    if any(set(p.split()) & set(g.split()) for p, g in pairs):
        return "value partly wrong"
    return "value wrong"
