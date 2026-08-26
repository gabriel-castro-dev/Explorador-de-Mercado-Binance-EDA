"""Inferência batch: última linha completa de cada símbolo → curva de 7 dias.

A origem da previsão de um símbolo é a linha mais recente cujo conjunto de
features finais está completo (targets não importam aqui — o futuro é o que
está sendo previsto). O preço exibido é reconstruído do último close:
``close × exp(y_h)``, com banda dos quantis de resíduo da validação.

A nuvem de Monte Carlo (``build_monte_carlo_rows``) nasce das mesmas origens,
do mesmo modelo publicado e dos mesmos resíduos que definem a banda — no
fallback, os do naive (``ŷ = 0``), para que curva, banda e nuvem contem a
mesma história.
"""

import logging

import numpy as np
import pandas as pd

from app.ml.dataset import MLDataset, horizon_of
from app.ml.evaluation.metrics import EvaluationReport
from app.ml.models.baselines import NaiveZeroReturn
from app.ml.montecarlo import (
    classify_paths,
    seed_from_version,
    simulate_paths,
    validation_residuals,
)
from app.ml.training import TrainingOutcome, residual_quantiles

logger = logging.getLogger(__name__)

FALLBACK_SUFFIX = "-fallback-naive"
FALLBACK_MODEL_TYPE = "naive-fallback"
STEP_SECONDS = 86_400  # passo diário (timeframe 1d)
_PATH_SIGNIFICANT_DIGITS = 6  # jsonb: 6 algarismos bastam para desenhar; corta o payload


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
        quantiles=outcome.residual_quantiles,
    )


def build_fallback_rows(outcome: TrainingOutcome, run_at: pd.Timestamp) -> list[dict]:
    """Fallback naive (random walk) quando o gate reprova o campeão.

    O dashboard nunca fica sem curva; ``is_fallback`` deixa o estado degradado
    visível na API e nas métricas. A banda usa os resíduos do naive — é o
    erro do modelo publicado, não o do campeão reprovado.
    """
    return _forecast_rows(
        model=_fitted_naive(outcome),
        outcome=outcome,
        run_at=run_at,
        model_version=fallback_version(outcome.model_version),
        is_fallback=True,
        quantiles=residual_quantiles(outcome.validation_frame, _naive_predictions(outcome)),
    )


def build_monte_carlo_rows(
    outcome: TrainingOutcome,
    run_at: pd.Timestamp,
    n_paths: int = 1000,
    published_fallback: bool = False,
) -> list[dict]:
    """Linhas para ``monte_carlo_runs``: uma por símbolo, ``n_paths`` trajetórias em preço.

    Mesmo modelo, mesmas origens e mesmos resíduos da curva publicada (campeão
    ou naive no fallback); seed derivada da ``model_version`` gravada.
    """
    if published_fallback:
        model = _fitted_naive(outcome)
        model_version = fallback_version(outcome.model_version)
        predictions_on_validation = _naive_predictions(outcome)
    else:
        model = outcome.model
        model_version = outcome.model_version
        predictions_on_validation = outcome.validation_predictions

    targets = outcome.final.target_columns
    residuals = validation_residuals(outcome.validation_frame, predictions_on_validation, targets)
    origins, predictions = _predict_origins(model, outcome)

    rows: list[dict] = []
    for (_, origin), (_, prediction) in zip(
        origins.iterrows(), predictions.iterrows(), strict=True
    ):
        paths = simulate_paths(
            close=float(origin["close"]),
            predicted_log_returns=prediction[list(targets)].to_numpy(dtype=float),
            residuals=residuals,
            n_paths=n_paths,
            seed=seed_from_version(model_version, str(origin["symbol"])),
        )
        rows.append(
            {
                "symbol": origin["symbol"],
                "model_version": model_version,
                "run_at": run_at.isoformat(),
                "horizon_days": horizon_of(targets[-1]),
                "step_seconds": STEP_SECONDS,
                "n_simulated": int(paths.shape[0]),
                "paths": _compact(paths),
                "classified": classify_paths(paths),
            }
        )
    logger.info(
        "%s nuvens de Monte Carlo geradas (%s trajetórias × %s passos, fallback=%s).",
        len(rows),
        n_paths,
        len(targets),
        published_fallback,
    )
    return rows


def _fitted_naive(outcome: TrainingOutcome) -> NaiveZeroReturn:
    return NaiveZeroReturn().fit(
        outcome.final.frame, outcome.final.feature_columns, outcome.final.target_columns
    )


def _naive_predictions(outcome: TrainingOutcome) -> pd.DataFrame:
    """``ŷ = 0`` nas linhas de validação (o random walk não precisa de features)."""
    return pd.DataFrame(
        0.0, index=outcome.validation_frame.index, columns=list(outcome.final.target_columns)
    )


def _predict_origins(model: object, outcome: TrainingOutcome) -> tuple[pd.DataFrame, pd.DataFrame]:
    origins = latest_origin_rows(outcome.dataset, outcome.final.feature_columns)
    scaled = outcome.scaler.transform(origins)
    return origins, model.predict(scaled)


def _compact(paths: np.ndarray) -> list[list[float]]:
    return [[float(f"{value:.{_PATH_SIGNIFICANT_DIGITS}g}") for value in path] for path in paths]


def _forecast_rows(
    model: object,
    outcome: TrainingOutcome,
    run_at: pd.Timestamp,
    model_version: str,
    is_fallback: bool,
    quantiles: pd.DataFrame,
) -> list[dict]:
    origins, predictions = _predict_origins(model, outcome)

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
