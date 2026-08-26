"""Avaliação walk-forward: treina no passado, avalia no bloco seguinte, repete.

Cada fold refaz o pipeline inteiro a partir das datas de treino do fold —
finalize (poda de colunas/símbolos), scaler e fit acontecem dentro do fold,
exatamente como aconteceriam em produção naquele ponto do tempo. Nada é
reaproveitado entre folds.
"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from app.ml.config import MLConfig
from app.ml.dataset import MLDataset, finalize_training_frame
from app.ml.evaluation.metrics import EvaluationReport, evaluate_predictions
from app.ml.scaling import FeatureScaler
from app.ml.splits import WalkForwardFold

ModelFactory = Callable[[], object]


@dataclass(frozen=True)
class WalkForwardResult:
    """Métricas agregadas (pool de todos os folds) e o rastro por fold."""

    pooled: EvaluationReport
    fold_reports: list[EvaluationReport]
    pooled_predictions: pd.DataFrame  # colunas de target, índice do frame avaliado
    pooled_frame: pd.DataFrame  # linhas avaliadas (symbol, timestamp, targets)


def evaluate_walk_forward(
    dataset: MLDataset,
    model_factory: ModelFactory,
    folds: list[WalkForwardFold],
    config: MLConfig,
) -> WalkForwardResult:
    if not folds:
        raise ValueError("Avaliação walk-forward exige ao menos um fold.")

    fold_reports: list[EvaluationReport] = []
    frames: list[pd.DataFrame] = []
    predictions: list[pd.DataFrame] = []

    for fold in folds:
        final = finalize_training_frame(dataset, fold.train_dates, config.dataset)
        frame = final.frame
        train_frame = frame[frame["timestamp"].isin(fold.train_dates)]
        eval_frame = frame[frame["timestamp"].isin(fold.eval_dates)]
        if train_frame.empty or eval_frame.empty:
            raise ValueError("Fold sem linhas de treino ou avaliação após o finalize.")

        scaler = FeatureScaler(clip_sigma=config.training.clip_sigma).fit(
            train_frame, final.feature_columns
        )
        scaled_train = scaler.transform(train_frame)
        scaled_eval = scaler.transform(eval_frame)

        model = model_factory()
        model.fit(scaled_train, final.feature_columns, final.target_columns)
        fold_predictions = model.predict(scaled_eval)

        fold_reports.append(
            evaluate_predictions(eval_frame, fold_predictions, final.target_columns)
        )
        frames.append(eval_frame)
        predictions.append(fold_predictions)

    pooled_frame = pd.concat(frames, ignore_index=False)
    pooled_predictions = pd.concat(predictions, ignore_index=False)
    # Índices vêm do frame original: folds não podem se sobrepor.
    if pooled_frame.index.has_duplicates:
        raise ValueError("Folds walk-forward avaliaram a mesma linha mais de uma vez.")

    target_columns = tuple(pooled_predictions.columns)
    pooled = evaluate_predictions(pooled_frame, pooled_predictions, target_columns)
    return WalkForwardResult(
        pooled=pooled,
        fold_reports=fold_reports,
        pooled_predictions=pooled_predictions,
        pooled_frame=pooled_frame,
    )
