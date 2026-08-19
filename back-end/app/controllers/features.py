"""Read endpoints for calculated technical indicators."""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import FeaturesRepoDep, get_claims
from app.core.timeframe import Timeframe
from app.schemas.market import FeatureRowOut

router = APIRouter(
    prefix="/api/v1/features",
    tags=["features"],
    dependencies=[Depends(get_claims)],
)


@router.get("/{timeframe}")
def list_features(
    timeframe: Timeframe,
    repo: FeaturesRepoDep,
    symbol: Annotated[str, Query(min_length=1, max_length=20, description="ex.: BTCUSDT")],
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
    start: Annotated[Optional[datetime], Query(description="ISO 8601, inclusivo")] = None,
    end: Annotated[Optional[datetime], Query(description="ISO 8601, inclusivo")] = None,
) -> list[FeatureRowOut]:
    """Indicadores de um ativo, do mais recente para o mais antigo.

    Timeframes: 15m, 1h, 1d — "24h" é aceito como sinônimo de "1d"
    (grafia histórica da tabela features_24h).
    """
    rows = repo.query_features(timeframe, symbol=symbol.upper(), limit=limit, start=start, end=end)
    return [FeatureRowOut.model_validate(row) for row in rows]
