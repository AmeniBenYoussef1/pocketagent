"""Tiny converted rows shared by the vocab and dataset tests."""

import pytest

from src.data.converter import convert_row

RAW = [
    ("en-US", "alarm_set", "wake me up at five am", "wake me up at [time : five am]"),
    ("en-US", "alarm_set", "wake me up at six am", "wake me up at [time : six am]"),
    ("en-US", "alarm_query", "what alarms do i have", "what alarms do i have"),
    ("fr-FR", "alarm_set", "réveille-moi à cinq heures", "réveille-moi à [time : cinq heures]"),
    ("ar-SA", "alarm_set", "صحيني تسعة الصباح", "صحيني [time : تسعة الصباح]"),
]


@pytest.fixture
def rows() -> list[dict]:
    return [
        convert_row({"id": str(i), "locale": loc, "intent": intent, "utt": utt, "annot_utt": annot})
        for i, (loc, intent, utt, annot) in enumerate(RAW)
    ]
