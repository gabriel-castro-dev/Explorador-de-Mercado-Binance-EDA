"""Métricas de avaliação: erro de regressão, direção e skill score vs naive.

MAE/RMSE isolados enganam em séries near-random-walk (prever "nada muda" já
parece bom). A métrica de decisão do projeto é o skill score contra o naive —
positivo significa que o modelo carrega informação além do random walk.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EvaluationReport:
    """Métricas por horizonte e recorte por símbolo (horizonte h=1)."""

    per_horizon: pd.DataFrame  # index: target (y_1..); colunas: mae, rmse, dir_acc, n
    per_symbol: pd.DataFrame  # index: symbol; colunas: mae, dir_acc, n  (no y_1)


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    diff = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.sqrt(np.mean(diff**2)))


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Fração de acertos de sinal (subiu/caiu); retorno exatamente zero não conta."""
    true_sign = np.sign(np.asarray(y_true))
    pred_sign = np.sign(np.asarray(y_pred))
    relevant = true_sign != 0
    if not relevant.any():
        return float("nan")
    return float(np.mean(true_sign[relevant] == pred_sign[relevant]))


def skill_score(mae_model: float, mae_reference: float) -> float:
    """``1 − MAE_modelo / MAE_referência``: >0 bate a referência, <0 perde."""
    if mae_reference <= 0:
        raise ValueError("MAE de referência deve ser positivo para calcular skill.")
    return 1.0 - mae_model / mae_reference


def evaluate_predictions(
    frame: pd.DataFrame,
    predictions: pd.DataFrame,
    target_columns: tuple[str, ...],
) -> EvaluationReport:
    """Compara previsões com os targets realizados de ``frame`` (índices alinhados)."""
    if not frame.index.equals(predictions.index):
        raise ValueError("frame e predictions precisam ter o mesmo índice.")
    missing = set(target_columns) - set(predictions.columns)
    if missing:
        raise ValueError(f"Previsões sem colunas de target: {', '.join(sorted(missing))}.")

    horizon_rows = {}
    for target in target_columns:
        y_true = frame[target].to_numpy()
        y_pred = predictions[target].to_numpy()
        horizon_rows[target] = {
            "mae": mean_absolute_error(y_true, y_pred),
            "rmse": root_mean_squared_error(y_true, y_pred),
            "dir_acc": directional_accuracy(y_true, y_pred),
            "n": len(y_true),
        }
    per_horizon = pd.DataFrame.from_dict(horizon_rows, orient="index")

    first_target = target_columns[0]
    symbol_rows = {}
    for symbol, group in frame.groupby("symbol", sort=True):
        y_true = group[first_target].to_numpy()
        y_pred = predictions.loc[group.index, first_target].to_numpy()
        symbol_rows[symbol] = {
            "mae": mean_absolute_error(y_true, y_pred),
            "dir_acc": directional_accuracy(y_true, y_pred),
            "n": len(group),
        }
    per_symbol = pd.DataFrame.from_dict(symbol_rows, orient="index")

    return EvaluationReport(per_horizon=per_horizon, per_symbol=per_symbol)


def skill_by_horizon(
    model_report: EvaluationReport, reference_report: EvaluationReport
) -> pd.Series:
    """Skill score por horizonte de um relatório contra o de referência (naive)."""
    if not model_report.per_horizon.index.equals(reference_report.per_horizon.index):
        raise ValueError("Relatórios com horizontes diferentes não são comparáveis.")
    return pd.Series(
        {
            target: skill_score(
                model_report.per_horizon.loc[target, "mae"],
                reference_report.per_horizon.loc[target, "mae"],
            )
            for target in model_report.per_horizon.index
        },
        name="skill_score",
    )
