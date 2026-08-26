"""Inferência batch: última linha completa de cada símbolo → curva de 7 dias.

A origem da previsão de um símbolo é a linha mais recente cujo conjunto de
features finais está completo (targets não importam aqui — o futuro é o que
está sendo previsto). O preço exibido é reconstruído do último close:
``close × exp(y_h)``, com banda dos quantis de resíduo da validação.
"""

import logging

import numpy as np
import pandas as pd

from app.ml.dataset import MLDataset, horizon_of
from app.ml.evaluation.metrics import EvaluationReport
from app.ml.models.baselines import NaiveZeroReturn
from app.ml.training import TrainingOutcome

logger = logging.getLogger(__name__)

FALLBACK_SUFFIX = "-fallback-naive"
FALLBACK_MODEL_TYPE = "naive-fallback"


def fallback_version(model_version: str) -> str:
    return f"{model_version}{FALLBACK_SUFFIX}"


def latest_origin_rows(dataset: MLDataset, feature_columns: tuple[str, ...]) -> pd.DataFrame:
    """Última linha por símbolo com todas as features finais preenchidas."""
    frame = dataset.frame
    complete = frame.dropna(subset=list(feature_columns))
    if complete.empty:
        raise ValueError("Nenhuma linha com features completas para inferência.")
    latest = complete.sort_values("timestamp").groupby("symbol", sort=True).tail(1)
    return latest.sort_values("symbol")


def build_forecast_rows(outcome: TrainingOutcome, run_at: pd.Timestamp) -> list[dict]:
    """Linhas para ``predictions`` usando o campeão reajustado (gate aprovado)."""
    return _forecast_rows(
        model=outcome.model,
        outcome=outcome,
        run_at=run_at,
        model_version=outcome.model_version,
        is_fallback=False,
    )


def build_fallback_rows(outcome: TrainingOutcome, run_at: pd.Timestamp) -> list[dict]:
    """Fallback naive (random walk) quando o gate reprova o campeão.

    O dashboard nunca fica sem curva; ``is_fallback`` deixa o estado degradado
    visível na API e nas métricas.
    """
    naive = NaiveZeroReturn().fit(
        outcome.final.frame, outcome.final.feature_columns, outcome.final.target_columns
    )
    return _forecast_rows(
        model=naive,
        outcome=outcome,
        run_at=run_at,
        model_version=fallback_version(outcome.model_version),
        is_fallback=True,
    )


def _forecast_rows(
    model: object,
    outcome: TrainingOutcome,
    run_at: pd.Timestamp,
    model_version: str,
    is_fallback: bool,
) -> list[dict]:
    origins = latest_origin_rows(outcome.dataset, outcome.final.feature_columns)
    scaled = outcome.scaler.transform(origins)
    predictions = model.predict(scaled)

    quantiles = outcome.residual_quantiles
    rows: list[dict] = []
    for (_, origin), (_, prediction) in zip(
        origins.iterrows(), predictions.iterrows(), strict=True
    ):
        close = float(origin["close"])
        for target in outcome.final.target_columns:
            horizon = horizon_of(target)
            log_return = float(prediction[target])
            rows.append(
                {
                    "symbol": origin["symbol"],
                    "model_version": model_version,
                    "run_at": run_at.isoformat(),
                    "target_time": (origin["timestamp"] + pd.Timedelta(days=horizon)).isoformat(),
                    "horizon_days": horizon,
                    "predicted_close": close * float(np.exp(log_return)),
                    "predicted_log_return": log_return,
                    "pred_lower": close
                    * float(np.exp(log_return + quantiles.loc[target, "lower"])),
                    "pred_upper": close
                    * float(np.exp(log_return + quantiles.loc[target, "upper"])),
                    "is_fallback": is_fallback,
                }
            )
    logger.info(
        "%s linhas de previsão geradas (%s símbolos, %s horizontes, fallback=%s).",
        len(rows),
        origins["symbol"].nunique(),
        len(outcome.final.target_columns),
        is_fallback,
    )
    return rows


def build_metrics_record(
    outcome: TrainingOutcome,
    run_at: pd.Timestamp,
    git_sha: str,
    published_fallback: bool,
) -> dict:
    """Linha de ``model_metrics`` da rodada: rastreabilidade modelo→métrica→previsão.

    As métricas gravadas são sempre as do modelo que foi PUBLICADO: no fallback,
    as do naive na validação (skill 0 por definição). O campeão reprovado fica
    registrado em ``hyperparams`` para auditoria, sem se passar pelo publicado.
    """
    published: EvaluationReport = (
        outcome.naive_report if published_fallback else outcome.validation_report
    )
    naive = outcome.naive_report.per_horizon
    return {
        "model_version": fallback_version(outcome.model_version)
        if published_fallback
        else outcome.model_version,
        "model_type": FALLBACK_MODEL_TYPE if published_fallback else outcome.champion.name,
        "trained_at": run_at.isoformat(),
        "train_start": outcome.train_start.isoformat(),
        "train_end": outcome.train_end.isoformat(),
        "git_sha": git_sha,
        "hyperparams": {
            "champion": outcome.champion.name,
            "members": list(outcome.champion.members),
            "ranking": {k: float(v) for k, v in outcome.champion.ranking.items()},
            "gate": {"passed": outcome.gate.passed, "reason": outcome.gate.reason},
            "n_folds": len(outcome.fold_skills),
        },
        "metrics": {
            "skill_score_h1": 0.0 if published_fallback else outcome.gate.skill,
            "per_fold_skill_h1": [] if published_fallback else outcome.fold_skills,
            "per_horizon": _report_rows(published.per_horizon),
            "per_symbol": _report_rows(published.per_symbol),
        },
        "baseline_mae": {target: _jsonable(naive.loc[target, "mae"]) for target in naive.index},
        "is_fallback": published_fallback,
    }


def _report_rows(table: pd.DataFrame) -> dict:
    return {
        str(key): {column: _jsonable(value) for column, value in row.items()}
        for key, row in table.to_dict(orient="index").items()
    }


def _jsonable(value):
    number = float(value)
    return None if np.isnan(number) else number
