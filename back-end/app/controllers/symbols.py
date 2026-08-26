"""Read endpoint for the symbols reference table."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.controllers.deps import SymbolsRepoDep, get_claims
from app.schemas.market import SymbolOut

router = APIRouter(
    prefix="/api/v1/symbols",
    tags=["symbols"],
    dependencies=[Depends(get_claims)],
)


@router.get("")
def list_symbols(
    repo: SymbolsRepoDep,
    tracked: Annotated[
        Optional[bool],
        Query(
            description=(
                "Filtro opcional: `true` devolve só os ativos rastreados "
                "(com candles em klines_1d); `false`, só os sem candles."
            )
        ),
    ] = None,
) -> list[SymbolOut]:
    """Ativos conhecidos pela plataforma, em ordem alfabética.

    Cada item traz `tracked`: `true` quando o ativo faz parte do universo de
    análise (tem candles/indicadores); `false` para pares vistos só pelo
    job de tickers 24h.
    """
    return [SymbolOut.model_validate(row) for row in repo.list_symbols(tracked=tracked)]
