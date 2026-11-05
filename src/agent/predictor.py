"""Load a trained run and turn utterances into (call, confidence)."""

from dataclasses import dataclass
from pathlib import Path

import torch
import yaml
from torch.nn.utils.rnn import pad_sequence

from src.data.converter import tokenize
from src.data.vocab import LANG_TAGS, PAD_ID, Vocab
from src.inference.greedy import greedy_decode, ids_to_calls
from src.training.train import build_model, get_device


@dataclass
class Prediction:
    call: str          # may be malformed: the dispatcher rejects it then
    confidence: float  # in (0, 1]: geometric mean ("mean") or lowest ("min") chosen token probability


class Predictor:
    """Greedy decoding with the best checkpoint of a run (model.pt + vocabularies + config)."""

    def __init__(self, model: torch.nn.Module, cfg: dict, src_vocab: Vocab, tgt_vocab: Vocab, device: torch.device,
                 confidence: str = "mean"):
        self.model = model.to(device).eval()
        self.cfg, self.src_vocab, self.tgt_vocab, self.device = cfg, src_vocab, tgt_vocab, device
        self.confidence = confidence

    @classmethod
    def from_run(cls, run_dir: Path, device: str = "auto", confidence: str = "mean") -> "Predictor":
        run_dir = Path(run_dir)
        cfg = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
        src_vocab, tgt_vocab = Vocab.load(run_dir / "vocab_src.json"), Vocab.load(run_dir / "vocab_tgt.json")
        dev = get_device(device)
        model = build_model(cfg, len(src_vocab), len(tgt_vocab))
        model.load_state_dict(torch.load(run_dir / "model.pt", map_location=dev))
        return cls(model, cfg, src_vocab, tgt_vocab, dev, confidence)

    def source_tokens(self, utterance: str, locale: str) -> list[str]:
        """Same preprocessing as MassiveDataset: [lang tag] + whitespace tokens, truncated."""
        data = self.cfg["data"]
        if locale not in data["locales"]:
            raise ValueError(f"model trained on {data['locales']}, not {locale}")
        tokens = ([LANG_TAGS[locale]] if data["lang_tag"] else []) + tokenize(utterance)
        return tokens[:data["max_src_len"]]

    @torch.no_grad()
    def decode(self, utterances: list[str], locales: list[str], beam_size: int = 1) -> list[str]:
        """Calls only, greedy or beam search (score them with explain.replay)."""
        if beam_size == 1:
            return [p.call for p in self.predict(utterances, locales)]
        from src.inference.beam import beam_search
        src, src_lens, kwargs, oovs = self._inputs(utterances, locales)
        ids = beam_search(self.model, src, src_lens, beam_size, **kwargs)
        return ids_to_calls(ids, self.tgt_vocab, oovs)

    def _inputs(self, utterances: list[str], locales: list[str]):
        src_tokens = [self.source_tokens(u, loc) for u, loc in zip(utterances, locales)]
        src = pad_sequence([torch.tensor(self.src_vocab.encode(t)) for t in src_tokens],
                           batch_first=True, padding_value=PAD_ID).to(self.device)  # (B, T_src)
        src_lens = torch.tensor([len(t) for t in src_tokens])  # (B,)
        kwargs, oovs = {}, None
        if getattr(self.model, "uses_copy", False):
            from src.models.copy import extend_source
            ext = extend_source(src_tokens, self.tgt_vocab)
            kwargs, oovs = {"src_ext": ext["src_ext"].to(self.device), "n_oov": ext["n_oov"]}, ext["oovs"]
        return src, src_lens, kwargs, oovs

    @torch.no_grad()
    def predict(self, utterances: list[str], locales: list[str]) -> list[Prediction]:
        src, src_lens, kwargs, oovs = self._inputs(utterances, locales)
        ids, confidence = greedy_decode(self.model, src, src_lens, return_confidence=True,
                                        confidence=self.confidence, **kwargs)
        calls = ids_to_calls(ids, self.tgt_vocab, oovs)
        return [Prediction(c, float(p)) for c, p in zip(calls, confidence.tolist())]
