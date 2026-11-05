"""Turn copied time and date values into machine values with dateparser.

    time "five p. m."      -> "17:00"
    date "this friday"     -> "2026-11-06"

dateparser alone gets some MASSIVE values wrong or doesn't parse them, so a few
rewrites run first:
    - "p. m." / "a. m." (MASSIVE spelling) -> pm / am
    - French "5 heures" is read by dateparser as "5 hours from now": rewritten to 05:00
    - French and Arabic number words, Arabic morning/evening words, colloquial
      "بكرة" (tomorrow), "next monday" (dateparser returns None)
A value that still doesn't parse is kept raw with value None, never guessed.
"""

import re
from dataclasses import dataclass
from datetime import datetime

import dateparser

LANG = {"en-US": "en", "fr-FR": "fr", "ar-SA": "ar"}
TIME_SLOTS = {"time"}
DATE_SLOTS = {"date"}

NUMBERS = {
    "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
           "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
           "fifty": 50},
    "fr": {"une": 1, "un": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7, "huit": 8,
           "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "quinze": 15, "vingt": 20, "trente": 30},
    "ar": {"واحد": 1, "واحدة": 1, "اثنين": 2, "ثنتين": 2, "ثلاث": 3, "ثلاثة": 3, "اربع": 4, "أربع": 4, "اربعة": 4,
           "أربعة": 4, "خمس": 5, "خمسة": 5, "ست": 6, "ستة": 6, "سبع": 7, "سبعة": 7, "ثمان": 8, "ثمانية": 8,
           "تسع": 9, "تسعة": 9, "عشر": 10, "عشرة": 10, "احدعش": 11, "اطنعش": 12, "اثنعش": 12},
}
AR_AM = r"(?:الصبح|الصباح|صباحا|صباحاً|الفجر)"
AR_PM = r"(?:المساء|مساء|مساءً|العصر|الظهر|بالليل|الليل|ليلا)"
AR_TOMORROW = r"(?:لبكره|لبكرة|بكره|بكرة)"


@dataclass
class Normalized:
    """raw: the copied value; value: machine value or None if it couldn't be parsed."""

    raw: str
    value: str | None


def _words_to_digits(text: str, lang: str) -> str:
    table = NUMBERS.get(lang, {})
    return " ".join(str(table[w]) if w in table else w for w in text.split())


def rewrite(text: str, lang: str) -> str:
    """Fixed rewrites before dateparser (see module docstring)."""
    t = text.lower().strip()
    t = re.sub(r"\bp\.\s*m\.?", "pm", t)
    t = re.sub(r"\ba\.\s*m\.?", "am", t)
    if lang == "en":
        t = re.sub(r"\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", r"\1", t)
        t = re.sub(r"\bo'? ?clock\b", "", t)
        # "six thirty pm" -> "6:30 pm"; only when followed by am/pm, so "two hours" stays a duration
        t = _words_to_digits(t, lang)
        t = re.sub(r"\b(\d{1,2}) (\d{2})\b(?= ?(?:am|pm))", r"\1:\2", t)
    if lang == "fr":
        t = _words_to_digits(t, lang)
        t = re.sub(r"\b(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)\s+prochain\b", r"\1", t)
        t = re.sub(r"\bmidi\b", "12:00", t)
        t = re.sub(r"\bminuit\b", "00:00", t)
        # "5 heures 30", "5h30", "17 h" -> clock time, not a duration
        t = re.sub(r"\b(\d{1,2})\s*h(?:eures?)?(?:\s*(\d{2}))?\b",
                   lambda m: f"{int(m.group(1)):02d}:{m.group(2) or '00'}", t)
        t = re.sub(r"\b(?:du matin)\b", "am", t)
        t = re.sub(r"\b(?:de l'après-midi|du soir)\b", "pm", t)
    if lang == "ar":
        t = re.sub(AR_TOMORROW, "غدا", t)
        t = re.sub(r"\b(?:الساعة|الساعه|يوم)\b", " ", t)
        t = _words_to_digits(t, lang)
        t = re.sub(AR_AM, "am", t)
        t = re.sub(AR_PM, "pm", t)
    return re.sub(r"\s+", " ", t).strip()


def _parse(text: str, lang: str, now: datetime) -> datetime | None:
    settings = {"RELATIVE_BASE": now, "PREFER_DATES_FROM": "future"}
    rewritten = rewrite(text, lang)
    # rewrites can leave english am/pm in a french or arabic value, so allow english too
    langs = [lang] if lang == "en" else [lang, "en"]
    return dateparser.parse(rewritten, languages=langs, settings=settings)


def normalize_time(value: str, locale: str, now: datetime) -> Normalized:
    lang = LANG.get(locale, "en")
    # a bare number is an hour ("الساعة خمسة" -> "5"); dateparser would read it as a day
    bare = re.fullmatch(r"(\d{1,2})", rewrite(value, lang))
    if bare and int(bare.group(1)) <= 24:
        return Normalized(value, f"{int(bare.group(1)) % 24:02d}:00")
    parsed = _parse(value, lang, now)
    return Normalized(value, parsed.strftime("%H:%M") if parsed else None)


def normalize_date(value: str, locale: str, now: datetime) -> Normalized:
    parsed = _parse(value, LANG.get(locale, "en"), now)
    return Normalized(value, parsed.strftime("%Y-%m-%d") if parsed else None)


def normalize_args(args: dict[str, list[str]], locale: str, now: datetime) -> dict[str, Normalized]:
    """First value of each argument, normalized if it is a time or a date, raw otherwise."""
    out = {}
    for name, values in args.items():
        if name in TIME_SLOTS:
            out[name] = normalize_time(values[0], locale, now)
        elif name in DATE_SLOTS:
            out[name] = normalize_date(values[0], locale, now)
        else:
            out[name] = Normalized(values[0], values[0])
    return out
