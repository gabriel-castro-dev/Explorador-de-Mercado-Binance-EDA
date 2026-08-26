"""Ensemble por média simples de modelos já ajustados (regra do ADR-0004)."""

import pandas as pd


def mean_predictions(predictions: list[pd.DataFrame]) -> pd.DataFrame:
    """Média elemento a elemento de previsões alinhadas (mesmo índice/colunas)."""
    if not predictions:
        raise ValueError("mean_predictions exige ao menos uma previsão.")
    stacked = sum(predictions[1:], start=predictions[0].copy())
    return stacked / len(predictions)


class MeanEnsemble:
    """Média das previsões dos membros; segue o protocolo fit/predict do projeto."""

    def __init__(self, members: list):
        if len(members) < 2:
            raise ValueError("MeanEnsemble exige ao menos dois membros.")
        self.members = list(members)

    def fit(
        self,
        train_frame: pd.DataFrame,
        feature_columns: tuple[str, ...],
        target_columns: tuple[str, ...],
    ) -> "MeanEnsemble":
        for member in self.members:
            member.fit(train_frame, feature_columns, target_columns)
        return self

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        return mean_predictions([member.predict(frame) for member in self.members])
