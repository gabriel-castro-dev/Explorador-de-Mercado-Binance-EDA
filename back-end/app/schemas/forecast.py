"""API response schemas for ML forecasts (predictions + model_metrics tables)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Piso de amostras de validação para publicar a confiança por símbolo: o mesmo
# piso de histórico do treino (dataset.min_history_days em app/ml/config/ml.yml —
# tests/ml/test_forecast_metrics_schema.py garante que os dois não driftam).
# Abaixo disso a acurácia direcional é ruído e a confiança vai como null.
MIN_CONFIDENCE_SAMPLES = 120


class ForecastOut(BaseModel):
    """One forecast point of the latest run: symbol × target_time × horizon.

    ``is_fallback=True`` means the champion failed the publication gate and the
    curve is the naive random walk — the UI must surface the degraded state.
    """

    # extra="ignore": ids surrogate do banco / colunas futuras nunca quebram a resposta
    model_config = ConfigDict(extra="ignore")

    symbol: str
    model_version: str
    model_type: str | None = None  # candidato campeão (drift, gbm, gru, ensemble-a-b…)
    run_at: datetime
    target_time: datetime
    horizon_days: int
    predicted_close: float
    predicted_log_return: float
    pred_lower: float
    pred_upper: float
    is_fallback: bool


class GateOut(BaseModel):
    passed: bool
    reason: str


class HorizonMetricsOut(BaseModel):
    """Validation error for one horizon, in LOG-RETURN units (never USDT)."""

    mae_log_return: float
    rmse_log_return: float
    dir_acc: float | None  # None when every validation return was exactly zero
    n: int


class SymbolMetricsOut(BaseModel):
    """Validation error for one symbol at horizon 1, in log-return units."""

    mae_log_return: float
    dir_acc: float | None
    n: int
    confidence: int | None  # round(dir_acc × 100); None below MIN_CONFIDENCE_SAMPLES


class RealizedHorizonOut(BaseModel):
    mae_log_return: float
    naive_mae_log_return: float
    skill: float
    n: int


class RealizedMetricsOut(BaseModel):
    """Realized error filled by the weekly ``ml-evaluate`` job (same log-return units)."""

    computed_at: datetime
    n_rows: int
    is_degenerate: bool
    per_horizon: dict[str, RealizedHorizonOut]  # keyed by horizon_days ("1".."7")


class ForecastMetricsOut(BaseModel):
    """Metrics of the run that signed the latest forecasts (one ``model_metrics`` row).

    Every MAE/RMSE is in log-return units — the model is global, so there is no
    per-symbol error in price. ``confidence`` is the rounded directional
    accuracy (0–100) at horizon 1, ``null`` for symbols with fewer than
    ``MIN_CONFIDENCE_SAMPLES`` validation rows.
    """

    model_version: str
    model_type: str
    trained_at: datetime
    is_fallback: bool
    git_sha: str | None
    gate: GateOut
    skill_score_h1: float
    per_fold_skill_h1: list[float]
    per_horizon: dict[str, HorizonMetricsOut]  # keyed by target ("y_1".."y_7")
    baseline_mae_log_return: dict[str, float]  # naive MAE per target
    per_symbol: dict[str, SymbolMetricsOut]
    realized_metrics: RealizedMetricsOut | None

    @classmethod
    def from_record(cls, record: dict) -> "ForecastMetricsOut":
        """Rename at the edge: jsonb keys of ``model_metrics`` → public contract."""
        metrics = record["metrics"]
        realized = record.get("realized_metrics")
        return cls(
            model_version=record["model_version"],
            model_type=record["model_type"],
            trained_at=record["trained_at"],
            is_fallback=record["is_fallback"],
            git_sha=record.get("git_sha"),
            gate=GateOut.model_validate(record["hyperparams"]["gate"]),
            skill_score_h1=metrics["skill_score_h1"],
            per_fold_skill_h1=metrics["per_fold_skill_h1"],
            per_horizon={
                target: HorizonMetricsOut(
                    mae_log_return=row["mae"],
                    rmse_log_return=row["rmse"],
                    dir_acc=row["dir_acc"],
                    n=row["n"],
                )
                for target, row in metrics["per_horizon"].items()
            },
            baseline_mae_log_return=record["baseline_mae"],
            per_symbol={
                symbol: SymbolMetricsOut(
                    mae_log_return=row["mae"],
                    dir_acc=row["dir_acc"],
                    n=row["n"],
                    confidence=_confidence(row["dir_acc"], row["n"]),
                )
                for symbol, row in metrics["per_symbol"].items()
            },
            realized_metrics=_realized(realized) if realized else None,
        )


def _confidence(dir_acc: float | None, n: float) -> int | None:
    if dir_acc is None or n < MIN_CONFIDENCE_SAMPLES:
        return None
    return round(dir_acc * 100)


def _realized(payload: dict) -> RealizedMetricsOut:
    return RealizedMetricsOut(
        computed_at=payload["computed_at"],
        n_rows=payload["n_rows"],
        is_degenerate=payload["is_degenerate"],
        per_horizon={
            horizon: RealizedHorizonOut(
                mae_log_return=row["mae"],
                naive_mae_log_return=row["naive_mae"],
                skill=row["skill"],
                n=row["n"],
            )
            for horizon, row in payload["per_horizon"].items()
        },
    )
