"""The models the web app can use, loaded on first use and kept in memory.

    b0  TF-IDF nearest train utterance (char 2-5 grams), returns that utterance's call
    e0  LSTM encoder-decoder        e1  + attention        e2  + copy
E models decode greedy or with beam 3; the predicted call is then replayed to get
token probabilities, attention and p_gen.
"""

import math
import time
from pathlib import Path

from src.agent.explain import replay

MODELS = {
    "b0": ("B0", "Retrieval", None),
    "e0": ("E0", "LSTM", "e0_lstm"),
    "e1": ("E1", "Attention", "e1_attn"),
    "e2": ("E2", "Copy", "e2_copy"),
}
DECODINGS = {"greedy": 1, "beam3": 3}


class ModelHub:
    def __init__(self, exp_dir: Path, data_dir: Path, device: str = "auto", confidence: str = "mean"):
        self.exp_dir, self.data_dir, self.device, self.confidence = Path(exp_dir), Path(data_dir), device, confidence
        self._predictors: dict = {}
        self._retrievers: dict = {}

    def available(self) -> list[dict]:
        out = []
        for mid, (short, name, run) in MODELS.items():
            ready = (self.data_dir / "en-US" / "train.jsonl").exists() if run is None \
                else (self.exp_dir / run / "model.pt").exists()
            out.append({"id": mid, "short": short, "name": name, "ready": ready,
                        "decodings": ["nearest"] if run is None else list(DECODINGS)})
        return out

    def predictor(self, model_id: str):
        if model_id not in self._predictors:
            from src.agent.predictor import Predictor
            self._predictors[model_id] = Predictor.from_run(self.exp_dir / MODELS[model_id][2], self.device)
        return self._predictors[model_id]

    def _retriever(self, locale: str):
        if locale not in self._retrievers:
            from src.baselines.retrieval import TfidfRetriever
            from src.data.dataset import load_split
            rows = load_split(self.data_dir, [locale], "train")
            self._retrievers[locale] = (TfidfRetriever("char_wb", (2, 5)).fit([r["utt"] for r in rows]), rows)
        return self._retrievers[locale]

    def parse(self, utterance: str, locale: str, model_id: str = "e2", decoding: str = "greedy") -> dict:
        if model_id not in MODELS:
            raise KeyError(model_id)
        if MODELS[model_id][2] is None:
            retriever, rows = self._retriever(locale)
            t0 = time.perf_counter()
            idx, sim = retriever.nearest([utterance])
            near = rows[int(idx[0])]
            return {"model": model_id, "decoding": "nearest", "call": near["call"],
                    "confidence": float(sim[0]), "latency_ms": (time.perf_counter() - t0) * 1000,
                    "tokens": None, "attention": None, "nearest": near["utt"]}

        predictor = self.predictor(model_id)
        t0 = time.perf_counter()
        call = predictor.decode([utterance], [locale], beam_size=DECODINGS[decoding])[0]
        latency = (time.perf_counter() - t0) * 1000
        info = replay(predictor, utterance, locale, call)
        if info is None:  # malformed call: nothing to score
            return {"model": model_id, "decoding": decoding, "call": call, "confidence": None,
                    "latency_ms": latency, "tokens": None, "attention": None}
        probs = info["token_probs"]
        confidence = min(probs) if self.confidence == "min" else math.exp(sum(map(math.log, probs)) / len(probs))
        gens = info["p_gen"] or [None] * len(probs)
        tokens = [{"token": t, "prob": p, "p_gen": g, "source": None if g is None else ("copied" if g < 0.5 else "generated")}
                  for t, p, g in zip(info["tgt_tokens"], probs, gens)]
        attention = None if info["attention"] is None else \
            {"src_tokens": info["src_tokens"], "tgt_tokens": info["tgt_tokens"], "weights": info["attention"]}
        return {"model": model_id, "decoding": decoding, "call": call, "confidence": confidence,
                "latency_ms": latency, "tokens": tokens, "attention": attention}
