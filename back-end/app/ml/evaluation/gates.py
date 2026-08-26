"""Gate de publicação: previsão só sai do job se carregar informação de verdade.

Duas condições, ambas na validação:

1. Skill score vs naive no horizonte h=1 acima do mínimo configurado — um modelo
   que não bate o random walk não tem o que publicar.
2. Previsões não-degeneradas — variância ~zero é o naive disfarçado de modelo.
"""

from dataclasses import dataclass

import pandas as pd

from app.ml.config import GateConfig
from app.ml.evaluation.metrics import EvaluationReport, skill_score
from app.ml.models.baselines import is_degenerate_prediction


@dataclass(frozen=True)
class GateResult:
    passed: bool
    skill: float
    reason: str


def publication_gate(
    candidate_report: EvaluationReport,
    naive_report: EvaluationReport,
    candidate_predictions: pd.DataFrame,
    config: GateConfig,
) -> GateResult:
    first_horizon = candidate_report.per_horizon.index[0]
    skill = skill_score(
        candidate_report.per_horizon.loc[first_horizon, "mae"],
        naive_report.per_horizon.loc[first_horizon, "mae"],
    )
    if is_degenerate_prediction(candidate_predictions):
        return GateResult(
            passed=False,
            skill=skill,
            reason="Previsões degeneradas (variância ~zero): naive disfarçado.",
        )
    if skill < config.min_skill_score:
        return GateResult(
            passed=False,
            skill=skill,
            reason=(
                f"Skill score {skill:.4f} em {first_horizon} abaixo do mínimo "
                f"{config.min_skill_score:.4f}: não bate o naive na validação."
            ),
        )
    return GateResult(
        passed=True,
        skill=skill,
        reason=f"Skill score {skill:.4f} em {first_horizon} — publicação liberada.",
    )
