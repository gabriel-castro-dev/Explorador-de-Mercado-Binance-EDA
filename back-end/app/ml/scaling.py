"""Escalonamento de features com fit restrito ao treino.

O scaler é um dos vetores clássicos de leakage: um fit no dataset inteiro deixa
média e desvio da validação/teste vazarem para o treino. Aqui o contrato é
explícito — ``fit`` recebe apenas linhas de treino e ``transform`` reutiliza
essas estatísticas em qualquer conjunto.
"""

import pandas as pd


class FeatureScaler:
    """Z-score por coluna com clip em ±clip_sigma, estatísticas do treino."""

    def __init__(self, clip_sigma: float = 10.0):
        if clip_sigma <= 0:
            raise ValueError("clip_sigma deve ser positivo.")
        self.clip_sigma = clip_sigma
        self.feature_columns: tuple[str, ...] | None = None
        self.means: pd.Series | None = None
        self.stds: pd.Series | None = None

    def fit(self, train_frame: pd.DataFrame, feature_columns: tuple[str, ...]) -> "FeatureScaler":
        if train_frame.empty:
            raise ValueError("Não há linhas de treino para ajustar o scaler.")
        missing = set(feature_columns) - set(train_frame.columns)
        if missing:
            raise ValueError(f"Colunas ausentes no treino: {', '.join(sorted(missing))}.")
        values = train_frame[list(feature_columns)]
        self.feature_columns = tuple(feature_columns)
        self.means = values.mean()
        # Coluna constante tem std 0: escalar viraria inf/NaN — vira 1.0 e a
        # coluna sai centrada em zero, inofensiva para o modelo.
        self.stds = values.std(ddof=0).replace(0.0, 1.0)
        return self

    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        if self.feature_columns is None or self.means is None or self.stds is None:
            raise RuntimeError("FeatureScaler.transform chamado antes do fit.")
        missing = set(self.feature_columns) - set(frame.columns)
        if missing:
            raise ValueError(f"Colunas ausentes no transform: {', '.join(sorted(missing))}.")
        result = frame.copy()
        columns = list(self.feature_columns)
        scaled = (result[columns] - self.means) / self.stds
        result[columns] = scaled.clip(-self.clip_sigma, self.clip_sigma)
        return result
