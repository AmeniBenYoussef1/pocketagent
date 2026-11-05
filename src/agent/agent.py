"""Utterance in, action out: predictor (model) then dispatcher (safety checks and tools)."""

from src.agent.dispatcher import AgentResponse, Dispatcher


class Agent:
    """predictor: anything with predict(utterances, locales) -> [Prediction]."""

    def __init__(self, predictor, dispatcher: Dispatcher):
        self.predictor = predictor
        self.dispatcher = dispatcher

    def handle(self, utterance: str, locale: str = "en-US", confirmed: bool = False) -> AgentResponse:
        pred = self.predictor.predict([utterance], [locale])[0]
        response = self.dispatcher.dispatch(pred.call, locale, pred.confidence, confirmed)
        response.call, response.confidence = pred.call, pred.confidence
        return response
