"""Read endpoint for the tracked-symbols reference table."""

from fastapi import APIRouter, Depends

from app.controllers.deps import SymbolsRepoDep, get_claims
from app.schemas.market import SymbolOut

router = APIRouter(
    prefix="/api/v1/symbols",
    tags=["symbols"],
    dependencies=[Depends(get_claims)],
)


@router.get("")
def list_symbols(repo: SymbolsRepoDep) -> list[SymbolOut]:
    """Ativos rastreados pela plataforma, em ordem alfabética."""
    return [SymbolOut.model_validate(row) for row in repo.list_symbols()]
