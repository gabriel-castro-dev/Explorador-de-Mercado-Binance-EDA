"""Read endpoint for 24-hour market snapshots."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import TickersRepoDep, get_claims
from app.schemas.market import Ticker24hOut

router = APIRouter(
    prefix="/api/v1/tickers",
    tags=["tickers"],
    dependencies=[Depends(get_claims)],
)


@router.get("/24h")
def list_24h_snapshots(
    repo: TickersRepoDep,
    symbol: Annotated[
        Optional[str], Query(min_length=1, max_length=20, description="ex.: BTCUSDT")
    ] = None,
    tracked: Annotated[
        Optional[bool],
        Query(description="Filtro opcional: `true` devolve só os ativos rastreados (com candles)."),
    ] = None,
) -> list[Ticker24hOut]:
    """Snapshot 24h mais recente por ativo (ou de um ativo específico)."""
    rows = repo.get_latest_24h_snapshots(symbol=symbol.upper() if symbol else None, tracked=tracked)
    return [Ticker24hOut.model_validate(row) for row in rows]
