"""Greedy decoding: take the most likely token at each step until <EOS>."""

import torch
from torch import nn

from src.data.converter import tokens_to_call
from src.data.dataset import MAX_GEN_LEN
from src.data.vocab import EOS_ID, PAD_ID, SOS_ID, Vocab


@torch.no_grad()
def greedy_decode(model: nn.Module, src: torch.Tensor, src_lens: torch.Tensor,
                  max_len: int = MAX_GEN_LEN, return_confidence: bool = False, confidence: str = "mean",
                  **start_kwargs):
    """Decode a batch. Call model.eval() first so dropout is off.

    Works with any model that has start(src, src_lens, **start_kwargs) -> state and
    step(y_prev, state) -> (scores, state), e.g. Seq2Seq, AttnSeq2Seq, CopySeq2Seq
    (which needs src_ext and n_oov).

    src:      (B, T_src) on the model's device
    src_lens: (B,)
    returns   (B, T_out) predicted ids without <SOS>, T_out <= max_len.
              A row that produced <EOS> is padded with <PAD> after it.
              With return_confidence, also (B,) confidence in (0, 1] over the chosen tokens,
              <EOS> included: confidence="mean" is the geometric mean of their probabilities,
              "min" the probability of the least likely one.
    """
    state = model.start(src, src_lens, **start_kwargs)
    B = src.size(0)
    y = torch.full((B,), SOS_ID, dtype=torch.long, device=src.device)  # (B,)
    finished = torch.zeros(B, dtype=torch.bool, device=src.device)  # (B,)
    logp_sum = torch.zeros(B, device=src.device)  # (B,)
    logp_min = torch.zeros(B, device=src.device)  # (B,) log 1 = 0 before any token
    n_tokens = torch.zeros(B, device=src.device)  # (B,)
    steps = []
    for _ in range(max_len):
        scores, state = model.step(y, state)  # (B, V_tgt) logits, or log-probs for the copy model
        logp = torch.log_softmax(scores, dim=-1)  # (B, V_tgt), same argmax as scores
        y = logp.argmax(dim=-1)  # (B,) predicted token, fed back as the next input
        active = (~finished).float()
        chosen = logp.gather(1, y.unsqueeze(1)).squeeze(1)  # (B,) log-prob of the chosen token
        logp_sum += chosen * active
        logp_min = torch.where(active.bool(), torch.minimum(logp_min, chosen), logp_min)
        n_tokens += active
        y = y.masked_fill(finished, PAD_ID)  # rows already done only get padding
        steps.append(y)
        finished |= y == EOS_ID
        if finished.all():
            break
    ids = torch.stack(steps, dim=1)  # (B, T_out)
    if return_confidence:
        if confidence == "min":
            return ids, torch.exp(logp_min)  # (B,)
        return ids, torch.exp(logp_sum / n_tokens)  # (B,)
    return ids


def ids_to_calls(ids: torch.Tensor, tgt_vocab: Vocab, oovs: list[list[str]] | None = None) -> list[str]:
    """(B, T_out) predicted ids -> one call string per row (possibly invalid).

    With a copy model, ids >= len(tgt_vocab) point to oovs[row][id - len(tgt_vocab)],
    the source words of that example that are not in the target vocabulary.
    """
    V = len(tgt_vocab)
    calls = []
    for b, row in enumerate(ids.tolist()):
        tokens = []
        for i in row:
            if i == EOS_ID:
                break
            if i in (PAD_ID, SOS_ID):
                continue
            tokens.append(oovs[b][i - V] if i >= V else tgt_vocab.itos[i])
        calls.append(tokens_to_call(tokens))
    return calls
