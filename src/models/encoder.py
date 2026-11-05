"""LSTM encoder: source ids -> one vector per position + final (h, c)."""

import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence

from src.data.vocab import PAD_ID


class Encoder(nn.Module):
    """Embedding + LSTM over the source utterance.

    E0: unidirectional, only the final (h, c) is used to start the decoder.
    E1: bidirectional, the per-position outputs (B, T_src, 2H) feed attention.
    """

    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int,
                 num_layers: int = 1, dropout: float = 0.0, bidirectional: bool = False):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_ID)
        self.dropout = nn.Dropout(dropout)
        # nn.LSTM only applies dropout between layers, so it needs 2+ layers
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers=num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0, bidirectional=bidirectional)
        self.out_dim = hidden_dim * (2 if bidirectional else 1)

    def forward(self, src: torch.Tensor, src_lens: torch.Tensor
                ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """
        src:      (B, T_src) ids, padded with PAD_ID
        src_lens: (B,) true lengths, all >= 1
        returns   outputs (B, T_src, D) with D = H, or 2H if bidirectional; zeros at padded positions
                  (h, c), each (L * num_directions, B, H): state after the last real token
                  (bidirectional: index 2l is layer l forward, 2l + 1 layer l backward)
        """
        emb = self.dropout(self.embedding(src))  # (B, T_src, E)
        # packing skips the padded positions; lengths must be on the CPU
        packed = pack_padded_sequence(emb, src_lens.cpu(), batch_first=True, enforce_sorted=False)
        packed_out, (h, c) = self.lstm(packed)  # h, c: (L * dirs, B, H), back in the original batch order
        outputs, _ = pad_packed_sequence(packed_out, batch_first=True, total_length=src.size(1))  # (B, T_src, D)
        return outputs, (h, c)
