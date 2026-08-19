"""Read endpoints for candlestick data."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import KlinesRepoDep, get_claims
from app.core.timeframe import Timeframe
from app.schemas.market import KlineOut

router = APIRouter(
    prefix="/api/v1/klines",
    tags=["klines"],
    dependencies=[Depends(get_claims)],
)


@router.get("/{timeframe}")
def list_klines(
    timeframe: Timeframe,
    repo: KlinesRepoDep,
    symbol: Annotated[str, Query(min_length=1, max_length=20, description="ex.: BTCUSDT")],
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    start: Annotated[Optional[datetime], Query(description="ISO 8601, inclusivo")] = None,
    end: Annotated[Optional[datetime], Query(description="ISO 8601, inclusivo")] = None,
) -> list[KlineOut]:
    """Candles de um ativo, do mais recente para o mais antigo. Timeframes: 15m, 1h, 1d."""
    rows = repo.query_klines(timeframe, symbol=symbol.upper(), limit=limit, start=start, end=end)
    return [KlineOut.model_validate(row) for row in rows]
