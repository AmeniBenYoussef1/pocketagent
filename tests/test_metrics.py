"""Unit tests for src/training/metrics.py (values computed by hand)."""

import pytest

from src.training.metrics import build_schema, compute_metrics, evaluate_by_locale

SCHEMA = {"intents": {"alarm_set", "alarm_query", "takeaway_order"},
          "slots": {"time", "date", "place_name", "food_type"}}


def m(pred, gold, **kwargs):
    return compute_metrics([pred], [gold], SCHEMA, **kwargs)


def test_perfect():
    r = m('alarm_set(time="five am", date="friday")', 'alarm_set(time="five am", date="friday")')
    for key in ["exact_match", "exact_match_strict", "intent_accuracy", "slot_precision",
                "slot_recall", "slot_f1", "parse_rate", "valid_call_rate"]:
        assert r[key] == 1.0, key


def test_right_intent_wrong_value():
    r = m('alarm_set(time="six am")', 'alarm_set(time="five am")')
    assert r["intent_accuracy"] == 1.0
    assert r["exact_match"] == 0.0
    assert (r["slot_precision"], r["slot_recall"], r["slot_f1"]) == (0.0, 0.0, 0.0)


def test_missing_slot():
    r = m('alarm_set(time="a")', 'alarm_set(time="a", date="b")')
    assert (r["slot_precision"], r["slot_recall"]) == (1.0, 0.5)
    assert r["slot_f1"] == pytest.approx(2 / 3)
    assert r["exact_match"] == 0.0


def test_extra_slot():
    r = m('alarm_set(time="a", place_name="c")', 'alarm_set(time="a")')
    assert (r["slot_precision"], r["slot_recall"]) == (0.5, 1.0)


def test_repeated_slot_name_counts_as_multiset():
    r = m('takeaway_order(food_type="x", food_type="x")', 'takeaway_order(food_type="x", food_type="y")')
    assert (r["slot_precision"], r["slot_recall"]) == (0.5, 0.5)
    assert r["exact_match"] == 0.0


def test_swapped_order_is_exact_but_not_strict():
    r = m('alarm_set(date="friday", time="nine am")', 'alarm_set(time="nine am", date="friday")')
    assert r["exact_match"] == 1.0
    assert r["exact_match_strict"] == 0.0
    assert r["slot_f1"] == 1.0


def test_no_slot_call():
    r = m("alarm_query()", "alarm_query()")
    assert r["exact_match"] == 1.0
    assert r["per_intent"]["alarm_query"]["slot_f1"] is None
    assert r["macro_slot_f1"] is None


def test_unparseable_prediction_is_wrong_everywhere():
    r = m('alarm_set(time="five am"', 'alarm_set(time="five am")')
    assert r["parse_rate"] == 0.0
    assert r["valid_call_rate"] == 0.0
    assert r["intent_accuracy"] == 0.0
    assert r["exact_match"] == 0.0
    assert (r["slot_precision"], r["slot_recall"]) == (0.0, 0.0)


def test_unknown_intent_or_slot_parses_but_is_invalid():
    r = compute_metrics(["make_coffee()", 'alarm_set(color="red")'],
                        ["alarm_query()", 'alarm_set(time="a")'], SCHEMA)
    assert r["parse_rate"] == 1.0
    assert r["valid_call_rate"] == 0.0
    assert r["intent_accuracy"] == 0.5


GOLD = ['alarm_set(time="a")', 'alarm_set(time="b")', "alarm_query()", "alarm_query()"]
PRED = ['alarm_set(time="a")', "alarm_query()", "alarm_query()", 'alarm_set(time="c")']


def test_per_intent_and_macro():
    r = compute_metrics(PRED, GOLD, SCHEMA, n_train={"alarm_set": 10})
    s, q = r["per_intent"]["alarm_set"], r["per_intent"]["alarm_query"]
    assert (s["n"], s["n_train"], q["n_train"]) == (2, 10, 0)
    # alarm_set: predicted twice, right once, 1 of 2 gold
    assert (s["intent_precision"], s["intent_recall"], s["intent_f1"]) == (0.5, 0.5, 0.5)
    assert s["exact_match"] == 0.5
    assert s["slot_f1"] == pytest.approx(2 / 3)  # tp 1, pred 1, gold 2
    # alarm_query: the extra time="c" on a no-slot gold gives slot F1 0
    assert q["slot_f1"] == 0.0
    assert r["macro_intent_f1"] == 0.5
    assert r["macro_exact_match"] == 0.5
    assert r["macro_slot_f1"] == pytest.approx(1 / 3)
    assert (r["exact_match"], r["intent_accuracy"], r["slot_f1"]) == (0.5, 0.5, 0.5)


def test_no_n_train_by_default():
    r = compute_metrics(PRED, GOLD, SCHEMA)
    assert "n_train" not in r["per_intent"]["alarm_set"]


def test_by_locale():
    locales = ["en-US", "en-US", "fr-FR", "fr-FR"]
    counts = {"en-US": {"alarm_set": 3}, "fr-FR": {"alarm_set": 4}}
    r = evaluate_by_locale(PRED, GOLD, locales, SCHEMA, counts)
    assert list(r) == ["overall", "en-US", "fr-FR"]
    assert (r["overall"]["n"], r["en-US"]["n"], r["fr-FR"]["n"]) == (4, 2, 2)
    assert r["en-US"]["exact_match"] == 0.5  # ex 0 right, ex 1 wrong
    assert r["fr-FR"]["exact_match"] == 0.5  # ex 2 right, ex 3 wrong
    assert r["overall"]["per_intent"]["alarm_set"]["n_train"] == 7
    assert r["fr-FR"]["per_intent"]["alarm_query"]["n_train"] == 0


def test_build_schema(rows):
    schema = build_schema(rows)
    assert schema == {"intents": {"alarm_set", "alarm_query"}, "slots": {"time"}}


def test_errors():
    with pytest.raises(ValueError):
        compute_metrics(["alarm_query()"], [], SCHEMA)
    with pytest.raises(ValueError):
        compute_metrics(["alarm_query()"], ["not a call"], SCHEMA)
