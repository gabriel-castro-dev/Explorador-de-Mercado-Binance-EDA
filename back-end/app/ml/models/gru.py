"""GRU global multi-horizonte (PyTorch, CPU): janelas de lookback + embedding de símbolo.

Contratos deste modelo:

- Janela de entrada termina na própria linha t (features de t são conhecidas na
  origem da previsão) e usa apenas linhas anteriores do mesmo símbolo; sem
  histórico suficiente, a janela é preenchida à esquerda com zeros (espaço
  escalado, média ~0).
- ``fit`` guarda as linhas de treino como contexto: no ``predict``, as janelas
  das primeiras linhas avaliadas se estendem para trás sobre esse histórico —
  que é estritamente passado em relação a qualquer data avaliada.
- Early stopping usa uma validação interna temporal (cauda das datas de treino)
  com embargo igual ao maior horizonte, espelhando a regra dos splits externos.
- Determinismo: mesma seed ⇒ mesmos pesos iniciais, mesma ordem de batches,
  mesmas previsões (single-thread CPU).
"""

import numpy as np
import pandas as pd
import torch
from torch import nn

from app.ml.dataset import horizon_of

_DEFAULT_PARAMS = {
    "hidden_size": 64,
    "embedding_dim": 8,
    "dropout": 0.2,
    "learning_rate": 1e-3,
    "weight_decay": 1e-4,
    "batch_size": 256,
    "max_epochs": 100,
    "patience": 10,
    "inner_val_fraction": 0.15,
}

_UNKNOWN_SYMBOL_ID = 0
_REQUESTED = "_requested"
_ORIGIN = "_origin"


class _GRUNetwork(nn.Module):
    def __init__(
        self,
        n_features: int,
        n_symbols: int,
        n_targets: int,
        hidden_size: int,
        embedding_dim: int,
        dropout: float,
    ):
        super().__init__()
        self.gru = nn.GRU(n_features, hidden_size, batch_first=True)
        self.embedding = nn.Embedding(n_symbols + 1, embedding_dim)  # id 0 = desconhecido
        self.head = nn.Sequential(
            nn.Dropout(dropout), nn.Linear(hidden_size + embedding_dim, n_targets)
        )

    def forward(self, sequences: torch.Tensor, symbol_ids: torch.Tensor) -> torch.Tensor:
        _, hidden = self.gru(sequences)
        latent = torch.cat([hidden[-1], self.embedding(symbol_ids)], dim=1)
        return self.head(latent)


class GRUModel:
    """Segue o protocolo dos modelos do projeto (fit/predict, ver baselines.py)."""

    def __init__(self, lookback: int = 60, seed: int = 42, params: dict | None = None):
        self.lookback = lookback
        self.seed = seed
        self.params = {**_DEFAULT_PARAMS, **(params or {})}

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "GRUModel":
        torch.manual_seed(self.seed)
        rng = np.random.default_rng(self.seed)

        self.feature_columns = tuple(feature_columns)
        self.target_columns = tuple(target_columns)
        self.symbol_to_id = {
            symbol: index + 1 for index, symbol in enumerate(sorted(train_frame["symbol"].unique()))
        }
        # Contexto para o predict: estritamente linhas de treino (passado).
        self._history = train_frame[["symbol", "timestamp", *self.feature_columns]].copy()

        sequences, symbol_ids, targets, timestamps, _ = self._windows(
            train_frame, with_targets=True
        )
        inner_train, inner_val = self._inner_split(timestamps)

        self.network = _GRUNetwork(
            n_features=len(self.feature_columns),
            n_symbols=len(self.symbol_to_id),
            n_targets=len(self.target_columns),
            hidden_size=self.params["hidden_size"],
            embedding_dim=self.params["embedding_dim"],
            dropout=self.params["dropout"],
        )
        optimizer = torch.optim.Adam(
            self.network.parameters(),
            lr=self.params["learning_rate"],
            weight_decay=self.params["weight_decay"],
        )
        loss_fn = nn.MSELoss()
        batch_size = self.params["batch_size"]

        best_state = None
        best_val_loss = float("inf")
        epochs_without_improvement = 0
        self.epochs_run_ = 0

        for _ in range(self.params["max_epochs"]):
            self.epochs_run_ += 1
            self.network.train()
            for batch in _batches(rng.permutation(inner_train), batch_size):
                optimizer.zero_grad()
                output = self.network(sequences[batch], symbol_ids[batch])
                loss = loss_fn(output, targets[batch])
                loss.backward()
                optimizer.step()

            self.network.eval()
            with torch.no_grad():
                val_output = self.network(sequences[inner_val], symbol_ids[inner_val])
                val_loss = float(loss_fn(val_output, targets[inner_val]))
            if val_loss < best_val_loss - 1e-9:
                best_val_loss = val_loss
                best_state = {
                    key: value.detach().clone() for key, value in self.network.state_dict().items()
                }
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
                if epochs_without_improvement >= self.params["patience"]:
                    break

        if best_state is not None:
            self.network.load_state_dict(best_state)
        self.network.eval()
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not frame.index.is_unique:
            raise ValueError("GRUModel.predict exige índice único no frame.")
        columns = ["symbol", "timestamp", *self.feature_columns]
        history = self._history[
            ~pd.MultiIndex.from_frame(self._history[["symbol", "timestamp"]]).isin(
                pd.MultiIndex.from_frame(frame[["symbol", "timestamp"]])
            )
        ][columns].assign(**{_REQUESTED: False, _ORIGIN: None})
        requested = frame[columns].assign(**{_REQUESTED: True, _ORIGIN: list(frame.index)})
        # ignore_index: histórico e frame vêm de DataFrames distintos, cujos
        # índices inteiros colidem — a identidade da linha pedida viaja em
        # coluna própria, nunca no índice.
        combined = pd.concat([history, requested], ignore_index=True).sort_values(
            ["symbol", "timestamp"], kind="stable"
        )

        sequences, symbol_ids, _, _, origins = self._windows(
            combined, with_targets=False, only_requested=True
        )
        with torch.no_grad():
            output = self.network(sequences, symbol_ids).numpy()
        result = pd.DataFrame(output, index=origins, columns=list(self.target_columns))
        return result.loc[frame.index]

    def _windows(
        self,
        frame: pd.DataFrame,
        with_targets: bool,
        only_requested: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None, pd.Series, list]:
        lookback = self.lookback
        sequence_list: list[np.ndarray] = []
        symbol_id_list: list[int] = []
        target_list: list[np.ndarray] = []
        timestamp_list: list[pd.Timestamp] = []
        origin_list: list = []

        for symbol, group in frame.groupby("symbol", sort=True):
            ordered = group.sort_values("timestamp")
            values = ordered[list(self.feature_columns)].to_numpy(dtype=np.float32)
            symbol_id = self.symbol_to_id.get(symbol, _UNKNOWN_SYMBOL_ID)
            targets = (
                ordered[list(self.target_columns)].to_numpy(dtype=np.float32)
                if with_targets
                else None
            )
            for position, (_, row) in enumerate(ordered.iterrows()):
                if only_requested and not row[_REQUESTED]:
                    continue
                if only_requested:
                    origin_list.append(row[_ORIGIN])
                start = max(0, position - lookback + 1)
                window = values[start : position + 1]
                if len(window) < lookback:
                    padding = np.zeros((lookback - len(window), values.shape[1]), dtype=np.float32)
                    window = np.concatenate([padding, window])
                sequence_list.append(window)
                symbol_id_list.append(symbol_id)
                timestamp_list.append(row["timestamp"])
                if with_targets:
                    target_list.append(targets[position])

        sequences = torch.from_numpy(np.stack(sequence_list))
        symbol_ids = torch.tensor(symbol_id_list, dtype=torch.long)
        target_tensor = torch.from_numpy(np.stack(target_list)) if with_targets else None
        return sequences, symbol_ids, target_tensor, pd.Series(timestamp_list), origin_list

    def _inner_split(self, timestamps: pd.Series) -> tuple[np.ndarray, np.ndarray]:
        """Cauda temporal do treino vira validação interna, com embargo = max(h)."""
        max_horizon = max(horizon_of(name) for name in self.target_columns)
        unique_dates = pd.DatetimeIndex(timestamps.unique()).sort_values()
        n_val_dates = max(1, int(len(unique_dates) * self.params["inner_val_fraction"]))
        val_start = unique_dates[-n_val_dates]
        train_end = val_start - pd.Timedelta(days=max_horizon + 1)

        train_indices = np.flatnonzero((timestamps <= train_end).to_numpy())
        val_indices = np.flatnonzero((timestamps >= val_start).to_numpy())
        if len(train_indices) == 0 or len(val_indices) == 0:
            raise ValueError(
                "Treino curto demais para a validação interna da GRU — "
                "reduza inner_val_fraction ou aumente o histórico."
            )
        return train_indices, val_indices


def _batches(order: np.ndarray, batch_size: int):
    for start in range(0, len(order), batch_size):
        yield torch.from_numpy(np.ascontiguousarray(order[start : start + batch_size]))
