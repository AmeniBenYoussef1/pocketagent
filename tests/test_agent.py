"""Unit tests for src/agent/ (parser, normalizer, validator, tools, dispatcher)."""

from datetime import datetime

import pytest

from src.agent.dispatcher import Dispatcher
from src.agent.normalizer import normalize_date, normalize_time
from src.agent.parser import ParseError, parse
from src.agent.tools import MockBackend, weather_query
from src.agent.validator import validate

NOW = datetime(2026, 11, 5, 10, 0)  # a thursday


def test_parse_groups_repeated_names():
    call = parse('takeaway_order(food_type="sandwich", food_type="soup", business_name="italian\'s")')
    assert call.intent == "takeaway_order"
    assert call.args == {"food_type": ["sandwich", "soup"], "business_name": ["italian's"]}
    assert call.first("food_type") == "sandwich" and call.first("time") is None


@pytest.mark.parametrize("bad", ['alarm_set(time="five am"', "alarm_set time", "", 'alarm_set(time=five)'])
def test_parse_rejects_malformed(bad):
    with pytest.raises(ParseError):
        parse(bad)


@pytest.mark.parametrize("value, locale, expected", [
    ("five am", "en-US", "05:00"),
    ("five p. m.", "en-US", "17:00"),          # MASSIVE spelling
    ("six thirty pm", "en-US", "18:30"),
    ("seven o clock", "en-US", "07:00"),
    ("noon", "en-US", "12:00"),
    ("two hours from now", "en-US", "12:00"),
    ("cinq heures", "fr-FR", "05:00"),         # dateparser alone gives 15:00 (5 hours from now)
    ("17 heures", "fr-FR", "17:00"),
    ("cinq heures trente", "fr-FR", "05:30"),
    ("sept heures du soir", "fr-FR", "19:00"),
    ("midi", "fr-FR", "12:00"),
    ("تسعة الصباح", "ar-SA", "09:00"),
    ("الساعة خمسة", "ar-SA", "05:00"),          # bare hour, not the 5th of the month
    ("9 مساء", "ar-SA", "21:00"),
])
def test_normalize_time(value, locale, expected):
    assert normalize_time(value, locale, NOW).value == expected


@pytest.mark.parametrize("value, locale, expected", [
    ("friday", "en-US", "2026-11-06"),
    ("next monday", "en-US", "2026-11-09"),
    ("tomorrow", "en-US", "2026-11-06"),
    ("demain", "fr-FR", "2026-11-06"),
    ("lundi prochain", "fr-FR", "2026-11-09"),
    ("الجمعة", "ar-SA", "2026-11-06"),
    ("يوم الجمعة", "ar-SA", "2026-11-06"),
    ("لبكره", "ar-SA", "2026-11-06"),
])
def test_normalize_date(value, locale, expected):
    assert normalize_date(value, locale, NOW).value == expected


def test_unparseable_value_is_kept_raw_not_guessed():
    n = normalize_date("blah blah", "en-US", NOW)
    assert (n.raw, n.value) == ("blah blah", None)


def test_validate():
    assert validate(parse('alarm_set(time="five am")')).status == "ok"
    assert validate(parse("make_coffee()")).status == "unknown_tool"
    missing = validate(parse('alarm_set(date="friday")'))
    assert (missing.status, missing.missing) == ("missing_args", ["time"])
    assert missing.question == "At what time should I set the alarm?"
    # one_of: any recipient slot is enough
    assert validate(parse('email_sendemail(relation="mom")')).status == "ok"
    assert validate(parse('email_sendemail(event_name="party")')).missing == ["person"]
    # slots the tool doesn't use are reported, not an error
    assert validate(parse('alarm_set(time="five am", color="red")')).ignored == ["color"]


def make():
    return Dispatcher(MockBackend(), confidence_threshold=0.5, now_fn=lambda: NOW)


def test_alarm_is_executed_with_normalized_values():
    agent = make()
    r = agent.dispatch('alarm_set(time="five p. m.", date="friday")')
    assert r.status == "executed"
    assert agent.backend.alarms == [{"id": 1, "time": "17:00", "date": "2026-11-06"}]


def test_arabic_alarm():
    agent = make()
    r = agent.dispatch('alarm_set(date="لبكره", time="ستة الصبح")', locale="ar-SA")
    assert r.status == "executed" and agent.backend.alarms[0]["time"] == "06:00"


@pytest.mark.parametrize("call", ['alarm_set(time="five am"', "delete_all_files()", ""])
def test_malformed_or_unknown_call_never_runs(call):
    agent = make()
    assert agent.dispatch(call).status == "rejected"
    assert agent.backend == MockBackend()


def test_missing_required_argument_asks():
    agent = make()
    r = agent.dispatch('calendar_set(event_name="dentist")')
    assert (r.status, r.message) == ("needs_input", "For which day?")
    assert agent.backend.events == []


def test_time_that_cannot_be_understood_asks():
    agent = make()
    r = agent.dispatch('alarm_set(time="whenever i feel like it")')
    assert r.status == "needs_input" and "time" in r.message
    assert agent.backend.alarms == []


def test_low_confidence_asks_before_running():
    agent = make()
    r = agent.dispatch('alarm_set(time="five am")', confidence=0.3)
    assert r.status == "needs_confirmation" and agent.backend.alarms == []
    r = agent.dispatch('alarm_set(time="five am")', confidence=0.3, confirmed=True)
    assert r.status == "executed" and len(agent.backend.alarms) == 1


def test_email_creates_draft_and_sends_only_after_confirmation():
    agent = make()
    r = agent.dispatch('email_sendemail(person="john", event_name="party")', confidence=0.9)
    assert r.status == "needs_confirmation"
    assert agent.backend.drafts[0]["sent"] is False and agent.backend.outbox == []
    sent = agent.confirm(r.result["id"])
    assert sent.status == "executed" and agent.backend.outbox[0]["to"] == "john"
    assert len(agent.backend.drafts) == 1
    assert agent.confirm(r.result["id"]).status == "rejected"  # can't send twice


def test_calendar_and_weather():
    agent = make()
    r = agent.dispatch('calendar_set(event_name="dentist", date="demain", time="17 heures")', locale="fr-FR")
    assert r.status == "executed"
    assert agent.backend.events[0] == {"id": 1, "event_name": "dentist", "date": "2026-11-06", "time": "17:00"}
    w = agent.dispatch('weather_query(place_name="paris", date="tomorrow")')
    assert w.status == "executed" and w.result["place"] == "paris"
    assert weather_query(agent.backend, "paris", "2026-11-06") == w.result  # deterministic


def test_weather_without_arguments_uses_defaults():
    r = make().dispatch("weather_query()")
    assert r.status == "executed" and r.result["place"] == "current location"
