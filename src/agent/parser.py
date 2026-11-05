"""Parse a predicted call string into a function name and arguments."""

from dataclasses import dataclass, field

from src.data.converter import parse_call


class ParseError(ValueError):
    """The call string is malformed."""


@dataclass
class ParsedCall:
    """A call with arguments grouped by name. A repeated slot (food_type twice) gives a list of 2."""

    intent: str
    args: dict[str, list[str]] = field(default_factory=dict)

    def first(self, name: str) -> str | None:
        """First value of an argument, or None."""
        values = self.args.get(name)
        return values[0] if values else None


def parse(call: str) -> ParsedCall:
    """'alarm_set(time="five am")' -> ParsedCall("alarm_set", {"time": ["five am"]})."""
    try:
        intent, slots = parse_call(call.strip())
    except ValueError as e:
        raise ParseError(str(e)) from e
    args: dict[str, list[str]] = {}
    for name, value in slots:
        args.setdefault(name, []).append(value)
    return ParsedCall(intent, args)
