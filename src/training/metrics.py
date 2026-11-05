"""Metrics on predicted vs gold call strings.

Both sides are parsed with converter.parse_call. A prediction that does not parse
counts as wrong everywhere: no intent and no predicted slots.

    exact_match         same intent and same multiset of (name, value) pairs, order ignored
    exact_match_strict  same intent and same slots in the same order
    intent_accuracy     same function name
    slot_precision/recall/f1   micro over (name, value) pairs, values compared verbatim
    parse_rate          prediction parses
    valid_call_rate     parses and uses only intents and slot names from the schema (train)
    macro_*             unweighted mean over gold intents
    per_intent          one row per gold intent (n, n_train, intent P/R/F1, EM, slot F1)

Slot F1 is pair-based, not the span-based seqeval score of the MASSIVE paper.
All scores are fractions in [0, 1].
"""

from collections import Counter
from typing import Mapping

from src.data.converter import parse_call

Slots = list[tuple[str, str]]
Call = tuple[str, Slots]


def safe_parse(call: str) -> Call | None:
    """parse_call, but None instead of an exception."""
    try:
        return parse_call(call)
    except ValueError:
        return None


def build_schema(train_rows: list[dict]) -> dict[str, set[str]]:
    """Intents and slot names seen in converted train rows."""
    return {
        "intents": {row["intent"] for row in train_rows},
        "slots": {name for row in train_rows for name, _ in row["slots"]},
    }


def train_intent_counts(train_rows: list[dict]) -> Counter:
    """Number of train examples per intent (for n_train in the per-intent table)."""
    return Counter(row["intent"] for row in train_rows)


def is_valid(call: Call | None, schema: dict[str, set[str]]) -> bool:
    if call is None:
        return False
    intent, slots = call
    return intent in schema["intents"] and all(name in schema["slots"] for name, _ in slots)


def slot_overlap(pred: Slots, gold: Slots) -> int:
    """Number of (name, value) pairs in common, counted as multisets."""
    return sum((Counter(pred) & Counter(gold)).values())


def prf(tp: int, n_pred: int, n_gold: int) -> tuple[float, float, float]:
    p = tp / n_pred if n_pred else 0.0
    r = tp / n_gold if n_gold else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def compute_metrics(
    pred_calls: list[str],
    gold_calls: list[str],
    schema: dict[str, set[str]],
    n_train: Mapping[str, int] | None = None,
) -> dict:
    """All metrics for one set of predictions. Gold calls must be valid."""
    if len(pred_calls) != len(gold_calls):
        raise ValueError(f"{len(pred_calls)} predictions for {len(gold_calls)} gold calls")

    examples = []
    for pred_str, gold_str in zip(pred_calls, gold_calls):
        gold = parse_call(gold_str)
        pred = safe_parse(pred_str)
        pred_intent, pred_slots = pred if pred is not None else (None, [])
        examples.append({
            "gold_intent": gold[0],
            "pred_intent": pred_intent,
            "parsed": pred is not None,
            "valid": is_valid(pred, schema),
            "em": pred is not None and pred_intent == gold[0] and Counter(pred_slots) == Counter(gold[1]),
            "em_strict": pred == gold,
            "tp": slot_overlap(pred_slots, gold[1]),
            "n_pred": len(pred_slots),
            "n_gold": len(gold[1]),
        })

    n = len(examples)
    tp = sum(e["tp"] for e in examples)
    n_pred = sum(e["n_pred"] for e in examples)
    n_gold = sum(e["n_gold"] for e in examples)
    slot_p, slot_r, slot_f = prf(tp, n_pred, n_gold)

    per_intent = {}
    for intent in sorted({e["gold_intent"] for e in examples}):
        gold_ex = [e for e in examples if e["gold_intent"] == intent]
        n_pred_intent = sum(e["pred_intent"] == intent for e in examples)
        n_correct = sum(e["pred_intent"] == intent for e in gold_ex)
        ip, ir, if1 = prf(n_correct, n_pred_intent, len(gold_ex))
        s_tp = sum(e["tp"] for e in gold_ex)
        s_pred = sum(e["n_pred"] for e in gold_ex)
        s_gold = sum(e["n_gold"] for e in gold_ex)
        row = {
            "n": len(gold_ex),
            "intent_precision": ip,
            "intent_recall": ir,
            "intent_f1": if1,
            "exact_match": _mean([e["em"] for e in gold_ex]),
            # undefined when this intent has no slots on either side
            "slot_f1": prf(s_tp, s_pred, s_gold)[2] if s_pred or s_gold else None,
        }
        if n_train is not None:
            row["n_train"] = n_train.get(intent, 0)
        per_intent[intent] = row

    rows = per_intent.values()
    slot_rows = [r["slot_f1"] for r in rows if r["slot_f1"] is not None]
    return {
        "n": n,
        "exact_match": _mean([e["em"] for e in examples]),
        "exact_match_strict": _mean([e["em_strict"] for e in examples]),
        "intent_accuracy": _mean([e["pred_intent"] == e["gold_intent"] for e in examples]),
        "slot_precision": slot_p,
        "slot_recall": slot_r,
        "slot_f1": slot_f,
        "parse_rate": _mean([e["parsed"] for e in examples]),
        "valid_call_rate": _mean([e["valid"] for e in examples]),
        "macro_intent_f1": _mean([r["intent_f1"] for r in rows]),
        "macro_exact_match": _mean([r["exact_match"] for r in rows]),
        "macro_slot_f1": _mean(slot_rows) if slot_rows else None,
        "per_intent": per_intent,
    }


def evaluate_by_locale(
    pred_calls: list[str],
    gold_calls: list[str],
    locales: list[str],
    schema: dict[str, set[str]],
    n_train_by_locale: Mapping[str, Mapping[str, int]] | None = None,
) -> dict:
    """compute_metrics overall and for each locale. locales[i] is the locale of example i."""
    def counts(loc: str | None) -> Mapping[str, int] | None:
        if n_train_by_locale is None:
            return None
        if loc is None:
            return sum((Counter(c) for c in n_train_by_locale.values()), Counter())
        return n_train_by_locale.get(loc, {})

    results = {"overall": compute_metrics(pred_calls, gold_calls, schema, counts(None))}
    for loc in dict.fromkeys(locales):
        idx = [i for i, l in enumerate(locales) if l == loc]
        results[loc] = compute_metrics(
            [pred_calls[i] for i in idx], [gold_calls[i] for i in idx], schema, counts(loc))
    return results
