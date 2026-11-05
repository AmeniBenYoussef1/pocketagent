"""Bahdanau (additive) attention."""

import torch
from torch import nn


class BahdanauAttention(nn.Module):
    """score_j = v . tanh(W_enc enc_j + W_dec query), softmax over real source positions.

    enc_dim:   size of the encoder outputs (2H for a BiLSTM)
    query_dim: size of the decoder state used as query (H)
    attn_dim:  size of the hidden layer inside the score
    """

    def __init__(self, enc_dim: int, query_dim: int, attn_dim: int):
        super().__init__()
        self.W_enc = nn.Linear(enc_dim, attn_dim, bias=False)
        self.W_dec = nn.Linear(query_dim, attn_dim)
        self.v = nn.Linear(attn_dim, 1, bias=False)

    def project_keys(self, enc_out: torch.Tensor) -> torch.Tensor:
        """W_enc enc_j for every position, computed once per batch: (B, T_src, D) -> (B, T_src, A)."""
        return self.W_enc(enc_out)

    def forward(self, query: torch.Tensor, keys: torch.Tensor, enc_out: torch.Tensor,
                mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        query:   (B, H)          decoder state
        keys:    (B, T_src, A)   from project_keys
        enc_out: (B, T_src, D)   the values that get averaged
        mask:    (B, T_src)      True at real source tokens
        returns  context (B, D), weights (B, T_src) summing to 1 over real tokens
        """
        scores = self.v(torch.tanh(keys + self.W_dec(query).unsqueeze(1))).squeeze(-1)  # (B, T_src)
        scores = scores.masked_fill(~mask, float("-inf"))  # padding gets weight 0 after softmax
        weights = torch.softmax(scores, dim=-1)  # (B, T_src)
        context = torch.bmm(weights.unsqueeze(1), enc_out).squeeze(1)  # (B, 1, T_src) x (B, T_src, D) -> (B, D)
        return context, weights
