"""Baselines: o régua que qualquer candidato precisa bater para ser publicado.

Protocolo comum dos modelos do projeto (duck typing, sem ABC):

- ``fit(train_frame, feature_columns, target_columns)`` — só linhas de treino.
- ``predict(frame) -> pd.DataFrame`` — colunas = target_columns, índice = frame.
"""

import pandas as pd
from sklearn.linear_model import Ridge


class NaiveZeroReturn:
    """Random walk: o melhor palpite para o log-retorno futuro é zero."""

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "NaiveZeroReturn":
        self.target_columns = tuple(target_columns)
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(0.0, index=frame.index, columns=list(self.target_columns))


class DriftBaseline:
    """Drift por símbolo: prevê o log-retorno médio observado no treino."""

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "DriftBaseline":
        self.target_columns = tuple(target_columns)
        self.symbol_means = train_frame.groupby("symbol")[list(target_columns)].mean()
        self.global_means = train_frame[list(target_columns)].mean()
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        # Símbolo fora do treino (histórico curto) cai na média global.
        aligned = self.symbol_means.reindex(frame["symbol"])
        aligned = aligned.fillna(self.global_means)
        aligned.index = frame.index
        return aligned[list(self.target_columns)]


class RidgeBaseline:
    """Regressão linear regularizada sobre as features: um alvo por horizonte."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "RidgeBaseline":
        self.feature_columns = tuple(feature_columns)
        self.target_columns = tuple(target_columns)
        x = train_frame[list(feature_columns)].to_numpy()
        self.models = {}
        for target in target_columns:
            model = Ridge(alpha=self.alpha)
            model.fit(x, train_frame[target].to_numpy())
            self.models[target] = model
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        x = frame[list(self.feature_columns)].to_numpy()
        predictions = {target: self.models[target].predict(x) for target in self.target_columns}
        return pd.DataFrame(predictions, index=frame.index)[list(self.target_columns)]


def is_degenerate_prediction(predictions: pd.DataFrame, epsilon: float = 1e-12) -> bool:
    """True se o modelo colapsou no naive: variância ~zero em todos os horizontes.

    Usado como sanity check em cima de candidatos "espertos" — um DL que produz
    isso está apenas imitando o random walk com custo maior.
    """
    return bool((predictions.std(ddof=0) <= epsilon).all())
