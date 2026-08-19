"""CLI dispatcher for the scheduled ingestion jobs."""

import logging
import sys

from app.ingestion.klines import ingest_klines
from app.ingestion.tickers import ingest_orderbook_tickers, ingest_ticker_24hr
from app.repositories.klines_repository import KlinesRepository
from app.repositories.tickers_repository import TickersRepository
from app.services.binance_market_data_service import BinanceMarketService
from config import setup_logging

logger = logging.getLogger(__name__)

_KNOWN_JOBS = ("five-minutes", "hourly", "daily")


def main() -> int:
    """Run the scheduled ingestion job named by the CLI argument.

    Supported job types:
    - 'five-minutes': persist order book tickers.
    - 'hourly': persist 24-hour ticker summaries.
    - 'daily': persist klines for the 15m, 1h, and 1d timeframes.

    Returns:
        Process exit code: 0 on success, 1 on failure, 2 on unknown job.
    """
    job_type = sys.argv[1] if len(sys.argv) > 1 else "hourly"
    if job_type not in _KNOWN_JOBS:
        logger.error("Job desconhecido: %s. Opções: %s", job_type, _KNOWN_JOBS)
        return 2
    try:
        setup_logging()
        market_service = BinanceMarketService()
        if job_type == "five-minutes":
            ingest_orderbook_tickers(market_service, TickersRepository())
        elif job_type == "hourly":
            ingest_ticker_24hr(market_service, TickersRepository())
        elif job_type == "daily":
            klines_repo = KlinesRepository()
            for interval in ("15m", "1h", "1d"):
                ingest_klines(market_service, klines_repo, interval)
    except Exception:
        logger.exception("Job %s falhou.", job_type)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
