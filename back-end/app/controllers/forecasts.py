"""Read endpoints for ML price forecasts (latest run), its metrics and Monte Carlo cloud."""

from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.controllers.deps import ForecastRepoDep, KlinesRepoDep, get_claims
from app.core.timeframe import Timeframe
from app.ml.dataset import drop_open_candles
from app.schemas.forecast import (
    ForecastMetricsOut,
    ForecastOut,
    MonteCarloSeriesOut,
    ObservedPointOut,
)

router = APIRouter(
    prefix="/api/v1/forecasts",
    tags=["forecasts"],
    dependencies=[Depends(get_claims)],
)

OBSERVED_WINDOW = 60  # velas fechadas de klines_1d desenhadas antes da linha de corte

_SymbolQuery = Query(min_length=1, max_length=20, description="ex.: BTCUSDT")


@router.get("")
def list_forecasts(
    repo: ForecastRepoDep,
    symbol: Annotated[Optional[str], _SymbolQuery] = None,
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


@router.get("/monte-carlo")
def get_monte_carlo(
    repo: ForecastRepoDep,
    klines: KlinesRepoDep,
    symbol: Annotated[str, _SymbolQuery],
) -> MonteCarloSeriesOut:
    """Nuvem de Monte Carlo mais recente de um ativo (`monte_carlo_runs`).

    Trajetórias **reais** simuladas pelo job (bootstrap dos resíduos de validação,
    determinístico por `model_version`); `observed` = últimas 60 velas **fechadas**
    de `klines_1d`, oldest-first. 404 quando o ativo ainda não tem simulação.
    """
    symbol = symbol.upper()
    cloud = repo.get_latest_monte_carlo(symbol)
    if cloud is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sem simulação de Monte Carlo para {symbol}.",
        )
    candles = klines.query_klines(Timeframe.D1, symbol, limit=OBSERVED_WINDOW + 1)
    return MonteCarloSeriesOut(
        symbol=symbol,
        horizon_days=cloud["horizon_days"],
        observed=_observed_points(candles, as_of=_now()),
        step_seconds=cloud["step_seconds"],
        paths=cloud["paths"],
        simulated_count=cloud["n_simulated"],
        classified=cloud.get("classified") or None,
    )


def _observed_points(candles: list[dict], as_of: pd.Timestamp) -> list[ObservedPointOut]:
    """Velas fechadas até ``as_of``, oldest-first, limitadas a ``OBSERVED_WINDOW``."""
    if not candles:
        return []
    frame = drop_open_candles(pd.DataFrame(candles), as_of)
    frame = frame.assign(open_time=pd.to_datetime(frame["open_time"], utc=True))
    frame = frame.sort_values("open_time").tail(OBSERVED_WINDOW)
    return [
        ObservedPointOut(time=int(row.open_time.timestamp()), value=float(row.close))
        for row in frame.itertuples(index=False)
    ]


def _now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC")
