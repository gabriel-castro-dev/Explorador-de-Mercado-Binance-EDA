"""Orquestração do treino diário: candidatos → walk-forward → campeão → gate.

Procedimento de produção (ADR-0004):

1. Walk-forward expanding-window com ``n_folds`` janelas contíguas cobrindo os
   últimos ``validation_days`` (embargo antes de cada janela) avalia todos os
   candidatos nas mesmas linhas.
2. O campeão sai de :func:`app.ml.selection.select_champion` e passa pelo gate
   de publicação (skill vs naive + não-degenerado).
3. Passando ou não, o campeão é reajustado com TODO o histórico disponível —
   quem decide o que publicar é o chamador (inference/main), usando o gate.
4. As bandas de incerteza vêm dos quantis dos resíduos de validação do campeão,
   por horizonte, com largura forçada a não diminuir com o horizonte.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.ml.config import MLConfig
from app.ml.dataset import MLDataset, build_dataset, finalize_training_frame
from app.ml.evaluation.gates import GateResult, publication_gate
from app.ml.evaluation.metrics import EvaluationReport, evaluate_predictions, skill_score
from app.ml.evaluation.walkforward import WalkForwardResult, evaluate_walk_forward
from app.ml.models.baselines import DriftBaseline, NaiveZeroReturn, RidgeBaseline
from app.ml.models.ensemble import MeanEnsemble, mean_predictions
from app.ml.models.gbm import LightGBMModel
from app.ml.models.gru import GRUModel
from app.ml.scaling import FeatureScaler
from app.ml.selection import ChampionSelection, select_champion
from app.ml.splits import walk_forward_windows

logger = logging.getLogger(__name__)

_LOWER_QUANTILE = 0.1
_UPPER_QUANTILE = 0.9


@dataclass(frozen=True)
class TrainingOutcome:
    champion: ChampionSelection
    gate: GateResult
    model: object  # campeão reajustado em todo o histórico
    scaler: FeatureScaler
    dataset: MLDataset  # dataset completo (build_dataset), para a inferência
    final: MLDataset  # dataset finalizado do refit (colunas podadas)
    validation_report: EvaluationReport
    naive_report: EvaluationReport
    validation_frame: pd.DataFrame  # linhas avaliadas na validação (com targets)
    validation_predictions: pd.DataFrame  # previsões do campeão nessas linhas
    residual_quantiles: pd.DataFrame  # index: target; colunas: lower, upper
    fold_skills: list[float]  # skill h=1 do campeão vs naive, fold a fold
    model_version: str
    train_start: pd.Timestamp
    train_end: pd.Timestamp


def candidate_factories(config: MLConfig) -> dict[str, Callable[[], object]]:
    gbm_params = config.models.get("gbm", {})
    gru_params = config.models.get("gru", {})
    seed = config.training.seed
    return {
        "naive": NaiveZeroReturn,
        "drift": DriftBaseline,
        "ridge": RidgeBaseline,
        "gbm": lambda: LightGBMModel(seed=seed, params=gbm_params),
        "gru": lambda: GRUModel(
            lookback=config.dataset.lookback_window, seed=seed, params=gru_params
        ),
    }


def run_training(
    features: pd.DataFrame,
    klines: pd.DataFrame,
    config: MLConfig,
    git_sha: str,
    run_date: pd.Timestamp,
    factories: dict[str, Callable[[], object]] | None = None,
) -> TrainingOutcome:
    factories = factories or candidate_factories(config)
    if "naive" not in factories:
        raise ValueError("O conjunto de candidatos precisa incluir o 'naive'.")

    dataset = build_dataset(features, klines, config.dataset)
    dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
    folds = walk_forward_windows(
        dates,
        eval_days=config.splits.fold_days,
        embargo_days=config.splits.embargo_days,
        n_folds=config.splits.n_folds,
        min_train_days=config.dataset.min_history_days,
    )

    results: dict[str, WalkForwardResult] = {}
    for name, factory in factories.items():
        logger.info("Avaliando candidato '%s' no walk-forward de validação.", name)
        results[name] = evaluate_walk_forward(dataset, factory, folds, config)

    champion = select_champion(results)
    logger.info("Campeão: %s (skill %.4f).", champion.name, champion.skill)

    champion_predictions = _champion_predictions(champion, results)
    champion_report = _champion_report(champion, results, champion_predictions)
    gate = publication_gate(
        champion_report, results["naive"].pooled, champion_predictions, config.gate
    )
    logger.info("Gate: %s", gate.reason)

    residual_quantiles = _residual_quantiles(
        results[champion.members[0]].pooled_frame, champion_predictions
    )
    fold_skills = _fold_skills(champion, results)

    # Refit final com todo o histórico (linhas com target completo).
    final = finalize_training_frame(dataset, dates, config.dataset)
    scaler = FeatureScaler(clip_sigma=config.training.clip_sigma).fit(
        final.frame, final.feature_columns
    )
    scaled_train = scaler.transform(final.frame)
    model: object
    if len(champion.members) > 1:
        model = MeanEnsemble([factories[name]() for name in champion.members])
    else:
        model = factories[champion.members[0]]()
    model.fit(scaled_train, final.feature_columns, final.target_columns)

    slug = champion.name.replace(":", "-").replace("+", "-")
    model_version = f"{run_date:%Y%m%d}-{git_sha[:7]}-{slug}"
    return TrainingOutcome(
        champion=champion,
        gate=gate,
        model=model,
        scaler=scaler,
        dataset=dataset,
        final=final,
        validation_report=champion_report,
        naive_report=results["naive"].pooled,
        validation_frame=results[champion.members[0]].pooled_frame,
        validation_predictions=champion_predictions,
        residual_quantiles=residual_quantiles,
        fold_skills=fold_skills,
        model_version=model_version,
        train_start=final.frame["timestamp"].min(),
        train_end=final.frame["timestamp"].max(),
    )


def _champion_predictions(
    champion: ChampionSelection, results: dict[str, WalkForwardResult]
) -> pd.DataFrame:
    return mean_predictions([results[name].pooled_predictions for name in champion.members])


def _champion_report(
    champion: ChampionSelection,
    results: dict[str, WalkForwardResult],
    champion_predictions: pd.DataFrame,
) -> EvaluationReport:
    if len(champion.members) == 1:
        return results[champion.members[0]].pooled
    reference = results[champion.members[0]]
    return evaluate_predictions(
        reference.pooled_frame,
        champion_predictions,
        tuple(champion_predictions.columns),
    )


def _fold_skills(champion: ChampionSelection, results: dict[str, WalkForwardResult]) -> list[float]:
    """Skill h=1 do campeão contra o naive em cada fold (estabilidade por regime)."""
    naive_reports = results["naive"].fold_reports
    member_reports = [results[name].fold_reports for name in champion.members]
    skills = []
    for fold_index, naive_report in enumerate(naive_reports):
        first = naive_report.per_horizon.index[0]
        naive_mae = naive_report.per_horizon.loc[first, "mae"]
        # Ensemble: média dos MAEs dos membros aproxima o fold; o pool exato
        # já está em validation_report — aqui interessa a tendência por fold.
        member_mae = sum(
            reports[fold_index].per_horizon.loc[first, "mae"] for reports in member_reports
        ) / len(member_reports)
        skills.append(float(skill_score(member_mae, naive_mae)))
    return skills


def _residual_quantiles(frame: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    """Quantis dos resíduos de validação, com largura não-decrescente no horizonte."""
    rows = {}
    for target in predictions.columns:
        residual = frame[target].to_numpy() - predictions[target].to_numpy()
        rows[target] = {
            "lower": float(np.quantile(residual, _LOWER_QUANTILE)),
            "upper": float(np.quantile(residual, _UPPER_QUANTILE)),
        }
    quantiles = pd.DataFrame.from_dict(rows, orient="index")
    # Incerteza não encolhe com o horizonte: banda cumulativamente envolvente.
    quantiles["lower"] = quantiles["lower"].cummin()
    quantiles["upper"] = quantiles["upper"].cummax()
    return quantiles
