"""E0: LSTM encoder-decoder without attention."""

import torch
from torch import nn

from src.models.decoder import Decoder
from src.models.encoder import Encoder


class Seq2Seq(nn.Module):
    """Encoder + decoder. The encoder's final (h, c) is the decoder's initial state.

    Both use the same hidden_dim and num_layers, so the state always fits.
    """

    def __init__(self, src_vocab_size: int, tgt_vocab_size: int, emb_dim: int = 256,
                 hidden_dim: int = 512, num_layers: int = 2, dropout: float = 0.3):
        super().__init__()
        self.encoder = Encoder(src_vocab_size, emb_dim, hidden_dim, num_layers, dropout)
        self.decoder = Decoder(tgt_vocab_size, emb_dim, hidden_dim, num_layers, dropout)

    def forward(self, src: torch.Tensor, src_lens: torch.Tensor, tgt_in: torch.Tensor) -> torch.Tensor:
        """Teacher-forced pass used for training.

        src:      (B, T_src)
        src_lens: (B,)
        tgt_in:   (B, T_tgt - 1)  tgt[:, :-1], starts with <SOS>
        returns   logits (B, T_tgt - 1, V_tgt), to compare with tgt[:, 1:]
        """
        _, state = self.encoder(src, src_lens)  # h, c: (L, B, H)
        logits, _ = self.decoder(tgt_in, state)  # (B, T_tgt - 1, V_tgt)
        return logits

    # decoding interface shared by all models, used by greedy and beam search
    def start(self, src: torch.Tensor, src_lens: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode the source and return the initial decoder state (h, c), each (L, B, H)."""
        _, state = self.encoder(src, src_lens)
        return state

    def step(self, y_prev: torch.Tensor, state: tuple) -> tuple[torch.Tensor, tuple]:
        """y_prev (B,) -> logits (B, V_tgt), new state."""
        return self.decoder.step(y_prev, state)

    @staticmethod
    def reorder_state(state: tuple, index: torch.Tensor) -> tuple:
        """Select batch rows of the state (beam search): h, c are (L, B, H)."""
        h, c = state
        return h.index_select(1, index), c.index_select(1, index)
