"""Monitoramento: pontua previsões passadas contra o close realizado.

O que a validação não pega, o tempo pega: aqui cada ``model_version`` recente é
avaliada sobre as previsões cujo ``target_time`` já tem vela realizada, sempre
contra o naive (random walk) nas MESMAS linhas. Skill realizado < 0 por K
versões seguidas derruba o job (exit ≠ 0), ficando visível no Actions.

O close de origem não precisa de consulta extra: ele é recuperável da própria
linha publicada (``origin = predicted_close × exp(−predicted_log_return)``).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.ml.config import MonitoringConfig

_FIRST_HORIZON = 1


@dataclass(frozen=True)
class RealizedScore:
    model_version: str
    run_at: pd.Timestamp
    is_fallback: bool
    per_horizon: pd.DataFrame  # index: horizon_days; colunas: mae, naive_mae, skill, n
    n_rows: int
    is_degenerate: bool  # previsões publicadas com variância ~zero (naive disfarçado)

    @property
    def skill_h1(self) -> float | None:
        if _FIRST_HORIZON not in self.per_horizon.index:
            return None
        return float(self.per_horizon.loc[_FIRST_HORIZON, "skill"])

    def to_payload(self, computed_at: pd.Timestamp) -> dict:
        return {
            "computed_at": computed_at.isoformat(),
            "n_rows": self.n_rows,
            "is_degenerate": self.is_degenerate,
            "per_horizon": {
                str(horizon): {
                    "mae": float(row["mae"]),
                    "naive_mae": float(row["naive_mae"]),
                    "skill": float(row["skill"]),
                    "n": int(row["n"]),
                }
                for horizon, row in self.per_horizon.to_dict(orient="index").items()
            },
        }


def score_predictions(
    predictions: list[dict], klines: pd.DataFrame, config: MonitoringConfig
) -> list[RealizedScore]:
    """Erro realizado por model_version/horizonte, em ordem cronológica de run.

    Previsões sem vela realizada (gap de coleta) são ignoradas; versões com
    menos de ``min_scored_rows`` linhas pontuadas ficam de fora — pouca amostra
    só produziria alarme falso.
    """
    if not predictions:
        return []
    if klines.empty:
        raise ValueError("Sem klines para pontuar previsões realizadas.")

    closes = klines.copy()
    closes["open_time"] = pd.to_datetime(closes["open_time"], utc=True).dt.normalize()
    close_lookup = {
        (row.symbol, row.open_time): float(row.close) for row in closes.itertuples(index=False)
    }

    frame = pd.DataFrame(predictions)
    frame["target_time"] = pd.to_datetime(frame["target_time"], utc=True).dt.normalize()
    frame["run_at"] = pd.to_datetime(frame["run_at"], utc=True)

    scores: list[RealizedScore] = []
    for version, group in frame.groupby("model_version", sort=False):
        rows = []
        for row in group.itertuples(index=False):
            realized_close = close_lookup.get((row.symbol, row.target_time))
            if realized_close is None:
                continue
            origin_close = float(row.predicted_close) * float(np.exp(-row.predicted_log_return))
            realized_log_return = float(np.log(realized_close / origin_close))
            rows.append(
                {
                    "horizon_days": int(row.horizon_days),
                    "abs_error": abs(float(row.predicted_log_return) - realized_log_return),
                    "naive_abs_error": abs(realized_log_return),
                }
            )
        if len(rows) < config.min_scored_rows:
            continue
        scored = pd.DataFrame(rows)
        per_horizon = scored.groupby("horizon_days").agg(
            mae=("abs_error", "mean"),
            naive_mae=("naive_abs_error", "mean"),
            n=("abs_error", "size"),
        )
        per_horizon["skill"] = 1.0 - per_horizon["mae"] / per_horizon["naive_mae"]
        scores.append(
            RealizedScore(
                model_version=str(version),
                run_at=group["run_at"].max(),
                is_fallback=bool(group["is_fallback"].any()),
                per_horizon=per_horizon,
                n_rows=len(rows),
                is_degenerate=bool(group["predicted_log_return"].std(ddof=0) <= 1e-12),
            )
        )
    scores.sort(key=lambda score: score.run_at)
    return scores


def detect_degradation(scores: list[RealizedScore], config: MonitoringConfig) -> bool:
    """True quando as últimas K versões pontuadas têm skill realizado < 0 em h=1.

    Fallbacks contam: um fallback tem skill ≈ 0 (ele É o naive), então uma
    sequência degradada de verdade só existe quando o campeão publicado vem
    perdendo do random walk repetidamente.
    """
    with_h1 = [score for score in scores if score.skill_h1 is not None]
    if len(with_h1) < config.degradation_runs:
        return False
    recent = with_h1[-config.degradation_runs :]
    return all(score.skill_h1 < 0.0 for score in recent)
