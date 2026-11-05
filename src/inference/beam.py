"""Beam search: keep the K most likely partial calls at each step."""

import torch
from torch import nn

from src.data.dataset import MAX_GEN_LEN
from src.data.vocab import EOS_ID, PAD_ID, SOS_ID


@torch.no_grad()
def beam_search(model: nn.Module, src: torch.Tensor, src_lens: torch.Tensor, beam_size: int = 5,
                max_len: int = MAX_GEN_LEN, alpha: float = 0.6, **start_kwargs) -> torch.Tensor:
    """Decode a batch with beam search. Call model.eval() first.

    The model needs start(src, src_lens, **start_kwargs) -> state,
    step(y_prev, state) -> (scores, state) and reorder_state(state, index).
    step can return logits or log-probs, log_softmax gives log-probs in both cases.

    The B examples are expanded to B * K rows. A beam that produced <EOS> is
    frozen: it can only add <PAD> at cost 0. The final choice per example
    divides the log-prob by length ** alpha (alpha = 0 keeps the raw log-prob).

    returns (B, T_out) ids without <SOS>, padded with <PAD> after <EOS>,
            same format as greedy_decode
    """
    B, K = src.size(0), beam_size
    device = src.device
    state = model.start(src, src_lens, **start_kwargs)
    rows = torch.arange(B, device=device).repeat_interleave(K)  # (B*K,) example of each row
    state = model.reorder_state(state, rows)

    scores = torch.full((B, K), float("-inf"), device=device)  # (B, K) total log-prob per beam
    scores[:, 0] = 0.0  # all K beams start identical, keep one so the first step gives K different tokens
    y = torch.full((B * K,), SOS_ID, dtype=torch.long, device=device)  # (B*K,)
    tokens = torch.empty((B * K, 0), dtype=torch.long, device=device)  # (B*K, t)
    finished = torch.zeros(B * K, dtype=torch.bool, device=device)  # (B*K,)

    for _ in range(max_len):
        logits, state = model.step(y, state)
        logp = torch.log_softmax(logits, dim=-1)  # (B*K, V)
        V = logp.size(-1)
        # frozen beams: only <PAD>, at no cost
        logp[finished] = float("-inf")
        logp[finished, PAD_ID] = 0.0

        cand = (scores.view(-1, 1) + logp).view(B, K * V)  # (B, K*V) every beam x every next token
        scores, flat = cand.topk(K, dim=-1)  # (B, K)
        beam, tok = flat // V, flat % V  # which beam it extends, which token it adds
        parent = (torch.arange(B, device=device).unsqueeze(1) * K + beam).view(-1)  # (B*K,) row index

        state = model.reorder_state(state, parent)
        tokens = torch.cat([tokens[parent], tok.view(-1, 1)], dim=1)  # (B*K, t+1)
        finished = finished[parent] | (tok.view(-1) == EOS_ID)
        y = tok.view(-1)
        if finished.all():
            break

    # length = tokens up to and including <EOS>
    lengths = (tokens != PAD_ID).sum(dim=1).clamp(min=1).view(B, K).float()  # (B, K)
    best = (scores / lengths ** alpha).argmax(dim=-1)  # (B,)
    return tokens.view(B, K, -1)[torch.arange(B, device=device), best]  # (B, T_out)
