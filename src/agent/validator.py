"""Check a parsed call against the tool specs before anything runs."""

from dataclasses import dataclass, field

from src.agent.parser import ParsedCall


@dataclass(frozen=True)
class ToolSpec:
    """required: every name must be present. one_of: groups where at least one name must be present.
    sensitive: never runs without explicit confirmation (draft first)."""

    required: tuple[str, ...] = ()
    one_of: tuple[tuple[str, ...], ...] = ()
    optional: tuple[str, ...] = ()
    sensitive: bool = False
    questions: dict[str, str] = field(default_factory=dict)


# required arguments chosen from MASSIVE en-US train: alarm_set has a time in 75% of examples,
# calendar_set an event_name in 64% and a date in 51%, email_sendemail a person or relation in 71%
TOOLS: dict[str, ToolSpec] = {
    "alarm_set": ToolSpec(
        required=("time",), optional=("date", "timeofday", "event_name", "alarm_type", "general_frequency"),
        questions={"time": "At what time should I set the alarm?"}),
    "weather_query": ToolSpec(
        optional=("place_name", "date", "time", "timeofday", "weather_descriptor")),
    "calendar_set": ToolSpec(
        required=("event_name", "date"),
        optional=("time", "timeofday", "person", "relation", "place_name", "general_frequency"),
        questions={"event_name": "What should I put in the calendar?", "date": "For which day?"}),
    "play_music": ToolSpec(
        optional=("song_name", "artist_name", "music_genre", "playlist_name", "player_setting",
                  "music_descriptor", "media_type", "radio_name", "app_name")),
    "email_sendemail": ToolSpec(
        one_of=(("person", "relation", "email_address"),),
        optional=("event_name", "date", "time", "timeofday", "place_name"),
        sensitive=True,
        questions={"person": "Who should I send the e-mail to?"}),
}


@dataclass
class ValidationResult:
    """status: "ok", "unknown_tool" or "missing_args". ignored: arguments the tool doesn't use."""

    status: str
    missing: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)
    question: str | None = None


def validate(call: ParsedCall) -> ValidationResult:
    spec = TOOLS.get(call.intent)
    if spec is None:
        return ValidationResult("unknown_tool")

    missing = [name for name in spec.required if name not in call.args]
    for group in spec.one_of:
        if not any(name in call.args for name in group):
            missing.append(group[0])
    known = set(spec.required) | set(spec.optional) | {n for g in spec.one_of for n in g}
    ignored = [name for name in call.args if name not in known]
    if missing:
        return ValidationResult("missing_args", missing, ignored, spec.questions.get(missing[0]))
    return ValidationResult("ok", ignored=ignored)
