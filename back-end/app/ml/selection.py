"""Seleção do campeão entre candidatos avaliados no mesmo walk-forward.

Regras (ADR-0004):

- Ranking por skill score vs naive no horizonte h=1 (MAE agregado do pool).
- Ensemble por média entra na disputa apenas quando ≥ 2 candidatos batem o
  naive — e só vence se superar o melhor candidato individual.
- O campeão ainda passa pelo gate de publicação depois (gates.py); a seleção
  apenas ordena, não autoriza publicar.
"""

from dataclasses import dataclass

import pandas as pd

from app.ml.evaluation.metrics import evaluate_predictions, skill_score
from app.ml.evaluation.walkforward import WalkForwardResult
from app.ml.models.ensemble import mean_predictions

NAIVE_NAME = "naive"
ENSEMBLE_PREFIX = "ensemble"


@dataclass(frozen=True)
class ChampionSelection:
    name: str  # ex.: "gbm" ou "ensemble:gbm+gru"
    skill: float
    ranking: pd.Series  # skill por candidato (inclui ensemble quando disputou)
    members: tuple[str, ...]  # candidatos que compõem o campeão (1 ou 2)


def select_champion(results: dict[str, WalkForwardResult]) -> ChampionSelection:
    if NAIVE_NAME not in results:
        raise ValueError(f"Seleção exige o candidato '{NAIVE_NAME}' como referência.")
    if len(results) < 2:
        raise ValueError("Seleção exige ao menos um candidato além do naive.")

    naive = results[NAIVE_NAME]
    reference_index = naive.pooled_frame.index
    first_target = naive.pooled_predictions.columns[0]
    naive_mae = naive.pooled.per_horizon.loc[first_target, "mae"]

    skills: dict[str, float] = {}
    members_by_name: dict[str, tuple[str, ...]] = {}
    for name, result in results.items():
        if name == NAIVE_NAME:
            continue
        if not result.pooled_frame.index.equals(reference_index):
            raise ValueError(
                f"Candidato '{name}' avaliado em linhas diferentes do naive — "
                "os walk-forwards precisam usar os mesmos folds."
            )
        skills[name] = skill_score(result.pooled.per_horizon.loc[first_target, "mae"], naive_mae)
        members_by_name[name] = (name,)

    winners = [name for name, skill in skills.items() if skill > 0.0]
    if len(winners) >= 2:
        top_two = tuple(sorted(winners, key=lambda name: skills[name], reverse=True)[:2])
        ensemble_name = f"{ENSEMBLE_PREFIX}:{top_two[0]}+{top_two[1]}"
        blended = mean_predictions([results[name].pooled_predictions for name in top_two])
        blended_report = evaluate_predictions(
            results[top_two[0]].pooled_frame, blended, tuple(blended.columns)
        )
        skills[ensemble_name] = skill_score(
            blended_report.per_horizon.loc[first_target, "mae"], naive_mae
        )
        members_by_name[ensemble_name] = top_two

    ranking = pd.Series(skills, name="skill_score").sort_values(ascending=False)
    champion_name = str(ranking.index[0])
    return ChampionSelection(
        name=champion_name,
        skill=float(ranking.iloc[0]),
        ranking=ranking,
        members=members_by_name[champion_name],
    )
