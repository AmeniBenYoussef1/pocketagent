"""E1: BiLSTM encoder + LSTM decoder with Bahdanau attention."""

import torch
from torch import nn

from src.data.vocab import PAD_ID
from src.models.attention import BahdanauAttention
from src.models.encoder import Encoder

# decoder state carried between steps: (h, c, enc_out, keys, mask)
AttnState = tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]


class AttnDecoder(nn.Module):
    """One step: attend with the previous top-layer h, feed [emb; context] to the LSTM,
    predict from [h_t; context; emb] through a tanh projection to H."""

    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int, enc_dim: int,
                 num_layers: int, dropout: float, attn_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_ID)
        self.dropout = nn.Dropout(dropout)
        self.attention = BahdanauAttention(enc_dim, hidden_dim, attn_dim)
        self.lstm = nn.LSTM(emb_dim + enc_dim, hidden_dim, num_layers=num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0)
        self.pre_out = nn.Linear(hidden_dim + enc_dim + emb_dim, hidden_dim)
        self.out = nn.Linear(hidden_dim, vocab_size)

    def step(self, y_prev: torch.Tensor, state: AttnState
             ) -> tuple[torch.Tensor, AttnState, torch.Tensor, torch.Tensor]:
        """
        y_prev:  (B,)
        returns  logits (B, V_tgt), new state, attention weights (B, T_src),
                 features [h_t; context; emb] (B, H + D + E), used by p_gen in E2
        """
        h, c, enc_out, keys, mask = state
        emb = self.dropout(self.embedding(y_prev))  # (B, E)
        context, weights = self.attention(h[-1], keys, enc_out, mask)  # (B, D), (B, T_src)
        rnn_in = torch.cat([emb, context], dim=-1).unsqueeze(1)  # (B, 1, E + D)
        out, (h, c) = self.lstm(rnn_in, (h, c))  # out (B, 1, H), h c (L, B, H)
        features = torch.cat([out.squeeze(1), context, emb], dim=-1)  # (B, H + D + E)
        logits = self.out(self.dropout(torch.tanh(self.pre_out(features))))  # (B, V_tgt)
        return logits, (h, c, enc_out, keys, mask), weights, features


class AttnSeq2Seq(nn.Module):
    """BiLSTM encoder, bridge to the decoder's initial state, attention decoder."""

    def __init__(self, src_vocab_size: int, tgt_vocab_size: int, emb_dim: int = 256,
                 hidden_dim: int = 512, num_layers: int = 2, dropout: float = 0.3, attn_dim: int = 256):
        super().__init__()
        self.num_layers = num_layers
        self.encoder = Encoder(src_vocab_size, emb_dim, hidden_dim, num_layers, dropout, bidirectional=True)
        enc_dim = self.encoder.out_dim  # 2H
        # forward + backward final states of each layer -> decoder initial state
        self.bridge_h = nn.Linear(enc_dim, hidden_dim)
        self.bridge_c = nn.Linear(enc_dim, hidden_dim)
        self.decoder = AttnDecoder(tgt_vocab_size, emb_dim, hidden_dim, enc_dim, num_layers, dropout, attn_dim)

    def start(self, src: torch.Tensor, src_lens: torch.Tensor) -> AttnState:
        """Encode, build the decoder's initial (h, c), precompute attention keys."""
        enc_out, (h, c) = self.encoder(src, src_lens)  # (B, T_src, 2H), h c (2L, B, H)
        B = src.size(0)
        # (2L, B, H) -> (L, 2, B, H) -> (L, B, 2H): concat directions per layer
        h = h.view(self.num_layers, 2, B, -1).permute(0, 2, 1, 3).reshape(self.num_layers, B, -1)
        c = c.view(self.num_layers, 2, B, -1).permute(0, 2, 1, 3).reshape(self.num_layers, B, -1)
        h0 = torch.tanh(self.bridge_h(h)).contiguous()  # (L, B, H)
        c0 = self.bridge_c(c).contiguous()  # (L, B, H)
        mask = src != PAD_ID  # (B, T_src)
        keys = self.decoder.attention.project_keys(enc_out)  # (B, T_src, A)
        return h0, c0, enc_out, keys, mask

    def step(self, y_prev: torch.Tensor, state: AttnState) -> tuple[torch.Tensor, AttnState]:
        """Decoding interface used by greedy and beam search."""
        logits, state, _, _ = self.decoder.step(y_prev, state)
        return logits, state

    @staticmethod
    def reorder_state(state: tuple, index: torch.Tensor) -> tuple:
        """Select batch rows (beam search): h, c have batch on dim 1, the rest on dim 0."""
        h, c, *rest = state
        return (h.index_select(1, index), c.index_select(1, index),
                *(x.index_select(0, index) for x in rest))

    def forward(self, src: torch.Tensor, src_lens: torch.Tensor, tgt_in: torch.Tensor,
                return_attn: bool = False):
        """Teacher forcing, one step at a time (attention depends on the previous state).

        tgt_in:  (B, T)
        returns  logits (B, T, V_tgt), and attention (B, T, T_src) if return_attn
        """
        state = self.start(src, src_lens)
        all_logits, all_weights = [], []
        for t in range(tgt_in.size(1)):
            logits, state, weights, _ = self.decoder.step(tgt_in[:, t], state)  # (B, V_tgt), (B, T_src)
            all_logits.append(logits)
            all_weights.append(weights)
        logits = torch.stack(all_logits, dim=1)  # (B, T, V_tgt)
        if return_attn:
            return logits, torch.stack(all_weights, dim=1)  # (B, T, T_src)
        return logits
