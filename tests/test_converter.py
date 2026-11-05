"""Unit tests for src/data/converter.py (inline examples only, no raw data)."""

import pytest

from src.data.converter import (
    convert_row,
    parse_annot,
    parse_call,
    strip_annot,
    to_call,
    to_target_tokens,
    tokenize,
    tokens_to_call,
)


def test_no_slots():
    assert parse_annot("what alarms do i have") == []
    assert to_call("alarm_query", []) == "alarm_query()"
    assert to_target_tokens("alarm_query", []) == ["alarm_query", "(", ")"]


def test_one_slot():
    slots = parse_annot("set an alarm for [time : two hours from now]")
    assert slots == [("time", "two hours from now")]
    assert to_call("alarm_set", slots) == 'alarm_set(time="two hours from now")'


def test_several_slots_keep_order_of_appearance():
    slots = parse_annot("wake me up at [time : five am] [date : this week]")
    assert slots == [("time", "five am"), ("date", "this week")]
    assert to_call("alarm_set", slots) == 'alarm_set(time="five am", date="this week")'
    assert to_target_tokens("alarm_set", slots) == [
        "alarm_set", "(", "time", "=", '"', "five", "am", '"', ",",
        "date", "=", '"', "this", "week", '"', ")",
    ]
    # not alphabetical
    assert [n for n, _ in parse_annot("[date : today] at [time : six]")] == ["date", "time"]


def test_repeated_slot_name():
    annot = "order a [food_type : sandwich] and [food_type : soup] from [business_name : italian's]"
    slots = parse_annot(annot)
    assert slots == [("food_type", "sandwich"), ("food_type", "soup"), ("business_name", "italian's")]
    assert to_call("takeaway_order", slots) == (
        'takeaway_order(food_type="sandwich", food_type="soup", business_name="italian\'s")'
    )
    assert parse_call(to_call("takeaway_order", slots)) == ("takeaway_order", slots)


def test_arabic():
    annot = "صحيني [time : تسعة الصباح] يوم [date : الجمعة]"
    slots = parse_annot(annot)
    assert slots == [("time", "تسعة الصباح"), ("date", "الجمعة")]
    assert to_call("alarm_set", slots) == 'alarm_set(time="تسعة الصباح", date="الجمعة")'
    assert strip_annot(annot) == "صحيني تسعة الصباح يوم الجمعة"


def test_arabic_diacritics_kept():
    value = "دائماً"  # ends with a tanwin diacritic
    slots = parse_annot(f"[date : {value}]")
    assert slots[0][1] == value
    assert parse_call(to_call("alarm_set", slots)) == ("alarm_set", slots)


def test_french_apostrophe_not_escaped():
    slots = parse_annot("quelle est [time : l'heure] à [place_name : paris]")
    assert to_call("datetime_query", slots) == 'datetime_query(time="l\'heure", place_name="paris")'
    assert "l'heure" in to_target_tokens("datetime_query", slots)


def test_quote_and_backslash_are_escaped():
    slots = [("message", 'say "hi"'), ("path", "c:\\temp")]
    call = to_call("email_sendemail", slots)
    assert call == r'email_sendemail(message="say \"hi\"", path="c:\\temp")'
    assert to_target_tokens("email_sendemail", slots)[5:8] == ["say", '\\"hi\\"', '"']
    assert parse_call(call) == ("email_sendemail", slots)


def test_comma_parens_equals_inside_value():
    slots = [("event_name", "lunch, (maybe) a=b"), ("date", "friday")]
    call = to_call("calendar_set", slots)
    assert call == 'calendar_set(event_name="lunch, (maybe) a=b", date="friday")'
    assert parse_call(call) == ("calendar_set", slots)


def test_spacing_variants_in_annotation():
    assert parse_annot("at [time:five am]") == [("time", "five am")]
    assert parse_annot("at [ time :  five am ]") == [("time", "five am")]


def test_strip_annot_gives_back_utt():
    assert strip_annot("wake me up at [time : nine am] on [date : friday]") == (
        "wake me up at nine am on friday"
    )
    assert strip_annot("olly quiet") == "olly quiet"


def test_empty_value_raises():
    with pytest.raises(ValueError, match="empty value"):
        parse_annot("wake me up at [time : ]")
    with pytest.raises(ValueError, match="empty value"):
        parse_call('alarm_set(time="")')


def test_malformed_annotation_raises():
    with pytest.raises(ValueError):
        parse_annot("wake me up at [time]")
    with pytest.raises(ValueError):
        parse_annot("wake me up at [time : five am")


@pytest.mark.parametrize("call", [
    'alarm_set(time="five am"',          # missing )
    'alarm_set(time="five am)',          # unclosed quote
    'alarm_set(time "five am")',         # missing =
    'alarm_set(time=five am)',           # unquoted value
    'alarm_set(time="five am",)',        # trailing comma
    'alarm_set(time="a" date="b")',      # missing comma
    'alarm_set(time="five am") extra',   # text after )
    'alarm_set(time="a\\nb")',           # unknown escape
    '(time="five am")',                  # no function name
    "",
])
def test_malformed_call_raises(call):
    with pytest.raises(ValueError):
        parse_call(call)


def test_tokenize_shared_by_utt_and_values():
    row = {"id": "1", "locale": "en-US", "intent": "alarm_set",
           "utt": "wake me up at five am this week",
           "annot_utt": "wake me up at [time : five am] [date : this week]"}
    ex = convert_row(row)
    assert ex["src_tokens"] == tokenize(row["utt"])
    assert ex["call"] == 'alarm_set(time="five am", date="this week")'
    # value tokens can be found in the source tokens (needed for the copy mechanism)
    assert ex["src_tokens"][4:6] == tokenize("five am")


@pytest.mark.parametrize("intent, slots", [
    ("alarm_query", []),
    ("alarm_set", [("time", "five am"), ("date", "this week")]),
    ("alarm_set", [("time", "تسعة الصباح"), ("date", "الجمعة")]),
    ("takeaway_order", [("food_type", "sandwich"), ("food_type", "soup")]),
    ("email_sendemail", [("message", 'say "hi"'), ("path", r"c:\temp")]),
    ("calendar_set", [("event_name", "lunch , (maybe) a=b")]),
])
def test_tokens_to_call_inverts_to_target_tokens(intent, slots):
    tokens = to_target_tokens(intent, slots)
    assert tokens_to_call(tokens) == to_call(intent, slots)
    assert parse_call(tokens_to_call(tokens)) == (intent, slots)


@pytest.mark.parametrize("tokens", [
    ["alarm_set", "(", "time", "=", '"', "five", "am", '"'],        # no )
    ["alarm_set", "(", "time", "=", '"', "five", "am", ")"],        # unclosed quote
    ["alarm_set", "(", "time", '"', "five", '"', ")"],              # no =
    ["alarm_set", "(", "time", "=", '"', '"', ")"],                 # empty value
    ["alarm_set", "(", ",", ")"],                                   # stray comma
    [],                                                             # nothing decoded
])
def test_malformed_tokens_give_an_invalid_call(tokens):
    with pytest.raises(ValueError):
        parse_call(tokens_to_call(tokens))
