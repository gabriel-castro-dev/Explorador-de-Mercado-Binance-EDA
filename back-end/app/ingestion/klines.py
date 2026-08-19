"""Ingestion job for candlestick data: fetch from Binance, persist via repository."""

import logging

import pandas as pd

from app.repositories.klines_repository import KlinesRepository
from app.services.binance_market_data_service import BinanceMarketService

logger = logging.getLogger(__name__)


def ingest_klines(
    market_service: BinanceMarketService,
    klines_repo: KlinesRepository,
    interval: str,
    start_str: str | None = None,
) -> int:
    """Fetch klines for one interval and upsert them.

    Args:
        market_service: Source of Binance market data.
        klines_repo: Destination repository.
        interval: Kline interval ("15m", "1h" or "1d").
        start_str: Optional start date for historical loads; when omitted,
            fetches the latest klines only.

    Returns:
        Number of rows persisted.
    """
    df: pd.DataFrame = (
        market_service.get_historical_klines(interval, start_str)
        if start_str
        else market_service.get_klines(interval)
    )
    if df.empty:
        logger.warning("Nenhum kline retornado para o intervalo %s.", interval)
        return 0
    return klines_repo.upsert_klines(interval, df)
