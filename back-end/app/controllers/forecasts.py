"""Read endpoints for ML price forecasts (latest run) and its metrics."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import ForecastRepoDep, get_claims
from app.schemas.forecast import ForecastMetricsOut, ForecastOut

router = APIRouter(
    prefix="/api/v1/forecasts",
    tags=["forecasts"],
    dependencies=[Depends(get_claims)],
)


@router.get("")
def list_forecasts(
    repo: ForecastRepoDep,
    symbol: Annotated[
        Optional[str], Query(min_length=1, max_length=20, description="ex.: BTCUSDT")
    ] = None,
) -> list[ForecastOut]:
    """Curva de previsão (1–7 dias) do run mais recente, por ativo.

    Ordenada por símbolo e horizonte; `[]` quando ainda não há previsões.
    `model_type` vem de `model_metrics` da mesma `model_version` (um run = uma versão).
    """
    rows = repo.get_latest_run_predictions(symbol=symbol.upper() if symbol else None)
    if not rows:
        return []
    model_type = repo.get_model_type(rows[0]["model_version"])
    return [ForecastOut.model_validate({**row, "model_type": model_type}) for row in rows]


@router.get("/metrics")
def get_forecast_metrics(repo: ForecastRepoDep) -> ForecastMetricsOut | None:
    """Métricas da rodada que assinou o run mais recente (`model_metrics`).

    MAE/RMSE em **log-retorno** (nunca USDT). `confidence` por símbolo =
    `round(dir_acc × 100)` no horizonte 1, `null` abaixo do piso de amostras de
    validação. `realized_metrics` só existe após o `ml-evaluate` semanal.
    Resposta `null` (200) enquanto não há rodada publicada.
    """
    record = repo.get_latest_run_metrics()
    return ForecastMetricsOut.from_record(record) if record else None
