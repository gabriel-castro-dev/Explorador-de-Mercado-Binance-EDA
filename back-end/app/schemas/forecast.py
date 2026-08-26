"""API response schemas for ML forecasts (predictions table)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ForecastOut(BaseModel):
    """One forecast point of the latest run: symbol × target_time × horizon.

    ``is_fallback=True`` means the champion failed the publication gate and the
    curve is the naive random walk — the UI must surface the degraded state.
    """

    # extra="ignore": ids surrogate do banco / colunas futuras nunca quebram a resposta
    model_config = ConfigDict(extra="ignore")

    symbol: str
    model_version: str
    run_at: datetime
    target_time: datetime
    horizon_days: int
    predicted_close: float
    predicted_log_return: float
    pred_lower: float
    pred_upper: float
    is_fallback: bool
