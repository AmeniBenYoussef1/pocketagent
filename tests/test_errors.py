"""Unit tests for src/training/errors.py."""

import pytest

from src.training.errors import CATEGORIES, classify, wrong_value_pairs

GOLD = 'alarm_set(time="five am", date="friday")'


@pytest.mark.parametrize("pred, expected", [
    ('alarm_set(time="five am", date="friday")', "correct"),
    ('alarm_set(date="friday", time="five am")', "correct"),           # order ignored
    ('alarm_set(time="five am"', "invalid call"),
    ('alarm_query(time="five am", date="friday")', "wrong intent"),
    ('alarm_set(time="five am")', "missing slot"),
    ('alarm_set(time="five am", date="friday", place_name="home")', "extra slot"),
    ('alarm_set(time="five am", place_name="friday")', "wrong slot names"),
    ('alarm_set(time="<UNK> am", date="friday")', "value with <UNK>"),
    ('alarm_set(time="am am", date="friday")', "repeated copy"),
    ('alarm_set(time="six am", date="friday")', "value partly wrong"),
    ('alarm_set(time="noon", date="friday")', "value wrong"),
])
def test_classify(pred, expected):
    assert classify(pred, GOLD) == expected
    assert expected in CATEGORIES


def test_repeat_that_gold_also_has_is_not_a_repeated_copy():
    gold = 'play_music(song_name="bye bye love")'
    assert classify('play_music(song_name="bye bye blues")', gold) == "value partly wrong"


def test_unk_wins_over_repeat():
    assert classify('alarm_set(time="<UNK> <UNK>", date="friday")', GOLD) == "value with <UNK>"


def test_wrong_value_pairs_with_repeated_names():
    pred = [("food_type", "soup"), ("food_type", "salad")]
    gold = [("food_type", "sandwich"), ("food_type", "soup")]
    assert wrong_value_pairs(pred, gold) == [("salad", "sandwich")]


def test_no_slot_calls():
    assert classify("alarm_query()", "alarm_query()") == "correct"
    assert classify('alarm_query(date="today")', "alarm_query()") == "extra slot"
