"""Ingestion jobs for ticker data: fetch from Binance, normalize, persist."""

import logging

import pandas as pd

from app.repositories.tickers_repository import TickersRepository
from app.services.binance_market_data_service import BinanceMarketService

logger = logging.getLogger(__name__)

# Timestamp format used as part of the upsert conflict keys — must stay
# byte-identical to what existing rows carry.
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

_TICKER_24HR_COLUMN_MAP = {
    "symbol": "symbol",
    "priceChange": "price_change",
    "priceChangePercent": "price_change_percent",
    "weightedAvgPrice": "weighted_avg_price",
    "prevClosePrice": "prev_close_price",
    "lastPrice": "last_price",
    "lastQty": "last_qty",
    "bidPrice": "bid_price",
    "bidQty": "bid_qty",
    "askPrice": "ask_price",
    "askQty": "ask_qty",
    "openPrice": "open_price",
    "highPrice": "high_price",
    "lowPrice": "low_price",
    "volume": "volume",
    "quoteVolume": "quote_volume",
    "openTime": "open_time",
    "closeTime": "close_time",
    "firstId": "first_id",
    "lastId": "last_id",
    "count": "count",
}

_ORDERBOOK_COLUMN_MAP = {
    "symbol": "symbol",
    "bidPrice": "bid_price",
    "bidQty": "bid_qty",
    "askPrice": "ask_price",
    "askQty": "ask_qty",
}


def ingest_ticker_24hr(
    market_service: BinanceMarketService, tickers_repo: TickersRepository
) -> int:
    """Fetch the 24-hour summaries, normalize columns, and upsert them.

    Returns:
        Number of rows persisted.
    """
    df = market_service.get_ticker_24hr()
    if df.empty:
        logger.warning("Nenhum ticker 24h retornado pela Binance.")
        return 0
    df_prep = df.copy().rename(columns=_TICKER_24HR_COLUMN_MAP)
    for column in ("open_time", "close_time"):
        if column in df_prep.columns:
            df_prep[column] = df_prep[column].dt.strftime(_TIMESTAMP_FORMAT)
    return tickers_repo.upsert_ticker_24hr(df_prep)


def ingest_orderbook_tickers(
    market_service: BinanceMarketService, tickers_repo: TickersRepository
) -> int:
    """Fetch the order-book snapshot, normalize columns, and upsert it.

    Returns:
        Number of rows persisted.
    """
    df = market_service.get_orderbook_tickers()
    if df.empty:
        logger.warning("Nenhum orderbook ticker retornado pela Binance.")
        return 0
    df_prep = df.copy().rename(columns=_ORDERBOOK_COLUMN_MAP)
    df_prep["fetched_at"] = pd.Timestamp.now(tz="UTC").strftime(_TIMESTAMP_FORMAT)
    return tickers_repo.upsert_orderbook_tickers(df_prep)
