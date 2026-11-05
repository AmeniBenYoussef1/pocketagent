"""From a predicted call string to an action, with the safety checks of the project.

    parse -> known tool? -> confidence gate -> required arguments -> normalize -> run (draft first if sensitive)

Statuses:
    rejected            malformed call or unknown function: nothing runs
    needs_confirmation  low model confidence, or a sensitive action: a draft is created and only
                        confirm(draft_id) sends it (confirmed=True never sends anything)
    needs_input         a required argument is missing, or a time/date can't be understood;
                        `missing` names it, and the answer comes back through `fill`
    executed            the tool ran
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.agent.normalizer import DATE_SLOTS, LANG, TIME_SLOTS, normalize_args
from src.agent.parser import ParseError, parse
from src.agent.tools import TOOL_FUNCTIONS, MockBackend, email_cancel, email_send
from src.agent.validator import TOOLS, validate


@dataclass
class AgentResponse:
    status: str
    message: str
    intent: str | None = None
    args: dict[str, str | None] = field(default_factory=dict)
    result: dict | None = None
    call: str | None = None          # set by Agent: the predicted call
    confidence: float | None = None  # set by Agent: the model's confidence in it
    missing: list[str] = field(default_factory=list)


class Dispatcher:
    """confidence_threshold: below it, ask before running (confidence comes from the model, 0 to 1)."""

    def __init__(self, backend: MockBackend | None = None, confidence_threshold: float = 0.5, now_fn=datetime.now):
        self.backend = backend or MockBackend()
        self.confidence_threshold = confidence_threshold
        self.now_fn = now_fn

    def dispatch(self, call: str, locale: str = "en-US", confidence: float | None = None,
                 confirmed: bool = False, fill: dict[str, str] | None = None) -> AgentResponse:
        """fill: answers to a needs_input question, added to the call's arguments."""
        try:
            parsed = parse(call)
        except ParseError:
            return AgentResponse("rejected", "I couldn't turn that into an action. Could you rephrase it?")
        for name, value in (fill or {}).items():
            parsed.args[name] = [value]

        if parsed.intent not in TOOLS:
            return AgentResponse("rejected", f"I understood this as {parsed.intent}, which I can't do yet.",
                                 parsed.intent)
        if confidence is not None and confidence < self.confidence_threshold and not confirmed:
            return AgentResponse("needs_confirmation", "I'm not sure I got that right. Did you mean this?",
                                 parsed.intent)

        check = validate(parsed)
        if check.status == "missing_args":
            return AgentResponse("needs_input", check.question or f"I need the {check.missing[0]}.",
                                 parsed.intent, missing=check.missing)

        args = {n: v for n, v in parsed.args.items() if n not in check.ignored}
        normalized = normalize_args(args, locale, self.now_fn())
        values = {n: v.value for n, v in normalized.items()}
        for name, norm in normalized.items():
            if (name in TIME_SLOTS or name in DATE_SLOTS) and norm.value is None:
                return AgentResponse("needs_input", f"I didn't understand the {name} \"{norm.raw}\". Can you say it another way?",
                                     parsed.intent, values, missing=[name])

        result = TOOL_FUNCTIONS[parsed.intent](self.backend, language=LANG.get(locale, "en"), **values)
        if TOOLS[parsed.intent].sensitive:
            # always a draft first, even with confirmed=True: confirmed only means "the model
            # understood me"; sending needs its own explicit step, confirm(draft_id)
            return AgentResponse("needs_confirmation", f"Draft ready for {result['to']}. Send it?",
                                 parsed.intent, values, result)
        return AgentResponse("executed", "Done.", parsed.intent, values, result)

    def _draft(self, draft_id: int) -> dict | None:
        return next((d for d in self.backend.drafts if d["id"] == draft_id and not d["sent"]), None)

    def confirm(self, draft_id: int) -> AgentResponse:
        """The user confirmed a draft returned by a needs_confirmation response: send it."""
        if self._draft(draft_id) is None:
            return AgentResponse("rejected", "No unsent draft with that id.")
        return AgentResponse("executed", "Sent.", "email_sendemail", result=email_send(self.backend, draft_id))

    def cancel(self, draft_id: int) -> AgentResponse:
        """The user cancelled a draft: delete it, nothing is sent."""
        if self._draft(draft_id) is None:
            return AgentResponse("rejected", "No unsent draft with that id.")
        return AgentResponse("executed", "Draft deleted.", "email_sendemail", result=email_cancel(self.backend, draft_id))
