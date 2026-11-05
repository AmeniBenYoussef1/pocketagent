"""LSTM decoder: previous target tokens + state -> logits over the target vocabulary."""

import torch
from torch import nn

from src.data.vocab import PAD_ID

State = tuple[torch.Tensor, torch.Tensor]


class Decoder(nn.Module):
    """Embedding + LSTM + linear output layer, without attention (E0).

    The initial state is the encoder's final (h, c), so hidden_dim and num_layers
    must match the encoder.
    """

    def __init__(self, vocab_size: int, emb_dim: int, hidden_dim: int,
                 num_layers: int = 1, dropout: float = 0.0):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, emb_dim, padding_idx=PAD_ID)
        self.dropout = nn.Dropout(dropout)
        self.lstm = nn.LSTM(emb_dim, hidden_dim, num_layers=num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0)
        self.out = nn.Linear(hidden_dim, vocab_size)

    def forward(self, tgt_in: torch.Tensor, state: State) -> tuple[torch.Tensor, State]:
        """Teacher forcing: run over the whole gold prefix at once.

        tgt_in:  (B, T) gold tokens <SOS> y1 .. y_{n}, padded at the end
        state:   (h, c), each (L, B, H)
        returns  logits (B, T, V_tgt), new state
        """
        emb = self.dropout(self.embedding(tgt_in))  # (B, T, E)
        # no packing: padding is only at the end, and an LSTM never looks ahead,
        # so it can't change the logits of real positions (those are all the loss uses)
        outputs, state = self.lstm(emb, state)  # (B, T, H)
        logits = self.out(self.dropout(outputs))  # (B, T, V_tgt)
        return logits, state

    def step(self, y_prev: torch.Tensor, state: State) -> tuple[torch.Tensor, State]:
        """One decoding step, used by greedy and beam search.

        y_prev:  (B,) previous token (gold or predicted)
        returns  logits (B, V_tgt), new state
        """
        logits, state = self.forward(y_prev.unsqueeze(1), state)  # (B, 1, V_tgt)
        return logits.squeeze(1), state  # (B, V_tgt)
