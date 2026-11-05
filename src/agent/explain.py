"""What the model did for a predicted call: token probabilities, attention, p_gen.

The call is replayed with teacher forcing. For a greedy call these are exactly the
numbers seen while decoding; for a beam call they score the chosen sequence the same way.
"""

import math

import torch

from src.data.converter import parse_call, to_target_tokens
from src.data.vocab import SOS_ID, UNK_ID


@torch.no_grad()
def replay(predictor, utterance: str, locale: str, call: str) -> dict | None:
    """None for a malformed call. Otherwise:

    src_tokens   input tokens (with the language tag if the model uses one)
    tgt_tokens   call tokens + "<EOS>"
    token_probs  probability of each call token under the model
    confidence   geometric mean of token_probs
    attention    T_tgt x T_src weights, or None for E0
    p_gen        per call token, 1 = generated, 0 = copied, or None without copy
    """
    try:
        tgt_tokens = to_target_tokens(*parse_call(call)) + ["<EOS>"]
    except ValueError:
        return None
    model, vocab, device = predictor.model, predictor.tgt_vocab, predictor.device
    src_tokens = predictor.source_tokens(utterance, locale)
    src = torch.tensor([predictor.src_vocab.encode(src_tokens)], device=device)  # (1, T_src)
    src_lens = torch.tensor([len(src_tokens)])
    attention = p_gen = None

    if getattr(model, "uses_copy", False):
        from src.models.copy import extend_source
        ext = extend_source([src_tokens], vocab)
        oov = ext["oovs"][0]
        ids = [vocab.stoi[t] if t in vocab else len(vocab) + oov.index(t) if t in oov else UNK_ID
               for t in tgt_tokens]
        tgt_in = torch.tensor([[SOS_ID] + ids[:-1]], device=device)  # (1, T_tgt)
        log_probs, attn, gens = model(src, src_lens, tgt_in, ext["src_ext"].to(device), ext["n_oov"],
                                      return_attn=True)  # (1, T_tgt, V + n_oov)
        attention, p_gen = attn[0].tolist(), gens[0].tolist()
    else:
        ids = vocab.encode(tgt_tokens)
        tgt_in = torch.tensor([[SOS_ID] + ids[:-1]], device=device)
        if hasattr(model.decoder, "attention"):
            logits, attn = model(src, src_lens, tgt_in, return_attn=True)
            attention = attn[0].tolist()
        else:
            logits = model(src, src_lens, tgt_in)
        log_probs = torch.log_softmax(logits, dim=-1)  # (1, T_tgt, V)

    token_logp = log_probs[0].gather(1, torch.tensor(ids, device=device).unsqueeze(1)).squeeze(1)  # (T_tgt,)
    token_probs = token_logp.exp().tolist()
    return {"src_tokens": src_tokens, "tgt_tokens": tgt_tokens, "token_probs": token_probs,
            "confidence": math.exp(token_logp.mean().item()), "attention": attention, "p_gen": p_gen}
