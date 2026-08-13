"""One-off historical candle backfill without retention cleanup."""

import logging
import sys
from datetime import datetime, timedelta, timezone

from app.feature_engineering.pipelines.klines_pipeline import KlinesPipeline
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository
from app.services.binance_market_data_service import BinanceMarketService

logger = logging.getLogger(__name__)
_START_DAYS = {"15m": 182, "1h": 739, "1d": 930}
_FEATURE_TIMEFRAMES = {"15m": "15m", "1h": "1h", "1d": "24h"}


def run(
    market_service: BinanceMarketService | None = None,
    klines_repo: KlinesRepository | None = None,
    features_repo: FeaturesRepository | None = None,
    now: datetime | None = None,
) -> None:
    """Backfill candles incrementally, then recalculate their candle features."""
    market_service = market_service or BinanceMarketService()
    klines_repo = klines_repo or KlinesRepository()
    features_repo = features_repo or FeaturesRepository()
    pipeline = KlinesPipeline(klines_repo, features_repo)
    reference_time = now or datetime.now(timezone.utc)

    for interval, days in _START_DAYS.items():
        start_time = reference_time - timedelta(days=days)
        start_str = start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        current_symbol = "<inicialização>"
        try:
            for current_symbol, batch in market_service.iter_historical_klines(
                interval, start_str
            ):
                klines_repo.upsert_klines(interval, batch)
            pipeline.run(_FEATURE_TIMEFRAMES[interval])
        except Exception:
            logger.exception(
                "Carga histórica falhou no intervalo %s, símbolo %s.",
                interval,
                current_symbol,
            )
            raise


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    try:
        run()
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
