"""E2: pointer-generator (See et al., 2017) on top of the E1 attention model.

At each step the model either generates a word from the target vocabulary or
copies a source word, mixing the two with p_gen:

    P(w) = p_gen * P_vocab(w) + (1 - p_gen) * sum of attention weights on source positions holding w

Source words missing from the target vocabulary get extended ids V, V+1, ...
for that example only (extend_batch), so they can still be produced.
"""

import torch
from torch import nn

from src.data.converter import parse_call, to_target_tokens
from src.data.vocab import EOS, PAD_ID, SOS, UNK_ID, Vocab
from src.models.attention_seq2seq import AttnSeq2Seq


def _pad(rows: list[list[int]]) -> torch.Tensor:
    T = max(len(r) for r in rows)
    return torch.tensor([r + [PAD_ID] * (T - len(r)) for r in rows], dtype=torch.long)


def extend_source(src_tokens: list[list[str]], tgt_vocab: Vocab) -> dict:
    """Source side of the extended vocabulary (all that's needed at inference).

    returns
        src_ext  (B, T_src) source tokens as target ids, or V + k for the k-th OOV word of the row
        oovs     list of B lists: the OOV source words of each row, in order
        n_oov    longest OOV list in the batch
    """
    V = len(tgt_vocab)
    oovs, src_rows = [], []
    for tokens in src_tokens:
        oov, ids = [], []
        for tok in tokens:
            if tok in tgt_vocab:
                ids.append(tgt_vocab.stoi[tok])
            else:
                if tok not in oov:
                    oov.append(tok)
                ids.append(V + oov.index(tok))
        oovs.append(oov)
        src_rows.append(ids)
    return {"src_ext": _pad(src_rows), "oovs": oovs, "n_oov": max(len(o) for o in oovs)}


def extend_batch(batch: dict, tgt_vocab: Vocab) -> dict:
    """extend_source + the targets of a collated training batch.

    adds tgt_ext (B, T_tgt): target ids where OOV words found in the source use their
    extended id (others stay <UNK>); rebuilt from batch["call"], same layout as batch["tgt"]
    """
    ext = extend_source(batch["src_tokens"], tgt_vocab)
    V = len(tgt_vocab)
    tgt_rows = []
    for call, oov in zip(batch["call"], ext["oovs"]):
        tokens = [SOS] + to_target_tokens(*parse_call(call)) + [EOS]
        tgt_rows.append([tgt_vocab.stoi[t] if t in tgt_vocab else V + oov.index(t) if t in oov else UNK_ID
                         for t in tokens])
    return {**ext, "tgt_ext": _pad(tgt_rows)}


class CopySeq2Seq(AttnSeq2Seq):
    """E1 + a copy switch p_gen. step and forward return log-probs over V + n_oov."""

    uses_copy = True

    def __init__(self, src_vocab_size: int, tgt_vocab_size: int, emb_dim: int = 256,
                 hidden_dim: int = 512, num_layers: int = 2, dropout: float = 0.3, attn_dim: int = 256):
        super().__init__(src_vocab_size, tgt_vocab_size, emb_dim, hidden_dim, num_layers, dropout, attn_dim)
        self.tgt_vocab_size = tgt_vocab_size
        # p_gen from [h_t; context; emb], the same features the output layer sees
        self.gen = nn.Linear(hidden_dim + self.encoder.out_dim + emb_dim, 1)

    def start(self, src: torch.Tensor, src_lens: torch.Tensor, src_ext: torch.Tensor, n_oov: int) -> tuple:
        """E1 state + the extended source ids (B, T_src) and the number of extra ids."""
        return (*super().start(src, src_lens), src_ext, n_oov)

    @staticmethod
    def reorder_state(state: tuple, index: torch.Tensor) -> tuple:
        *attn_state, src_ext, n_oov = state
        return (*AttnSeq2Seq.reorder_state(tuple(attn_state), index), src_ext.index_select(0, index), n_oov)

    def _step(self, y_prev: torch.Tensor, state: tuple):
        *attn_state, src_ext, n_oov = state
        y_in = y_prev.masked_fill(y_prev >= self.tgt_vocab_size, UNK_ID)  # copied OOV words have no embedding
        logits, attn_state, weights, features = self.decoder.step(y_in, tuple(attn_state))  # (B, V), (B, T_src)

        p_gen = torch.sigmoid(self.gen(features))  # (B, 1)
        p_vocab = torch.softmax(logits, dim=-1)  # (B, V)
        dist = torch.cat([p_gen * p_vocab, p_vocab.new_zeros(p_vocab.size(0), n_oov)], dim=-1)  # (B, V + n_oov)
        # add each source position's attention mass to the id of the word it holds
        dist = dist.scatter_add(1, src_ext, (1 - p_gen) * weights)  # (B, V + n_oov), sums to 1
        log_probs = torch.log(dist + 1e-12)
        return log_probs, (*attn_state, src_ext, n_oov), weights, p_gen.squeeze(-1)

    def step(self, y_prev: torch.Tensor, state: tuple) -> tuple[torch.Tensor, tuple]:
        """y_prev (B,), may hold extended ids -> log-probs (B, V + n_oov), new state."""
        log_probs, state, _, _ = self._step(y_prev, state)
        return log_probs, state

    def forward(self, src: torch.Tensor, src_lens: torch.Tensor, tgt_in: torch.Tensor,
                src_ext: torch.Tensor, n_oov: int, return_attn: bool = False):
        """Teacher forcing with extended targets.

        tgt_in:  (B, T) extended ids
        returns  log-probs (B, T, V + n_oov). Cross-entropy on these equals the NLL,
                 since they are already normalized. With return_attn, also the
                 attention (B, T, T_src) and p_gen (B, T).
        """
        state = self.start(src, src_lens, src_ext, n_oov)
        out, attn, gens = [], [], []
        for t in range(tgt_in.size(1)):
            log_probs, state, weights, p_gen = self._step(tgt_in[:, t], state)
            out.append(log_probs)
            attn.append(weights)
            gens.append(p_gen)
        log_probs = torch.stack(out, dim=1)  # (B, T, V + n_oov)
        if return_attn:
            return log_probs, torch.stack(attn, dim=1), torch.stack(gens, dim=1)
        return log_probs
