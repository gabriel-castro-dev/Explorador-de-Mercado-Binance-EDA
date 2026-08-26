"""Read endpoint for ML price forecasts (latest run)."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import ForecastRepoDep, get_claims
from app.schemas.forecast import ForecastOut

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
    """
    rows = repo.get_latest_run_predictions(symbol=symbol.upper() if symbol else None)
    return [ForecastOut.model_validate(row) for row in rows]
