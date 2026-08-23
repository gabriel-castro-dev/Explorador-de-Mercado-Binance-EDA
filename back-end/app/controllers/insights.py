"""Model-generated insights for the home page (daily reading)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.deps import FeaturesRepoDep, TickersRepoDep, get_claims
from app.schemas.insights import DailyReadingOut
from app.services.insights_service import InsightsService, InsightsUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/insights",
    tags=["insights"],
    dependencies=[Depends(get_claims)],
)


@router.get("/daily-reading", responses={503: {"description": "Leitura indisponível."}})
def get_daily_reading(
    tickers_repo: TickersRepoDep, features_repo: FeaturesRepoDep
) -> DailyReadingOut:
    """Leitura do dia gerada pelo modelo de linguagem (cache global por dia UTC).

    O texto resume apenas números calculados no servidor (snapshot 24h,
    volumes, ATR relativo) — nunca dados inventados. A primeira requisição
    autenticada do dia gera e grava; as demais leem o cache. Sem cache e sem
    geração possível, responde 503 e o front mostra o estado vazio.
    """
    service = InsightsService(tickers_repo=tickers_repo, features_repo=features_repo)
    try:
        return service.get_daily_reading()
    except InsightsUnavailableError as exc:
        logger.warning("Leitura do dia indisponível: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A leitura do dia está indisponível no momento.",
        ) from None
