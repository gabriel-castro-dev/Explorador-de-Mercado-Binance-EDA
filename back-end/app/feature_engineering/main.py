"""Feature-engineering pipeline orchestrator."""

import logging
from pathlib import Path
from typing import Any

import yaml

from app.feature_engineering.pipelines.klines_pipeline import KlinesPipeline
from app.feature_engineering.pipelines.orderbook import OrderbookPipeline
from app.feature_engineering.pipelines.ticker_24hr import Ticker24hrPipeline
from app.feature_engineering.retention.cleaner import RetentionCleaner
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository
from app.repositories.retention_repository import RetentionRepository
from app.repositories.tickers_repository import TickersRepository
from config import setup_logging

logger = logging.getLogger(__name__)
_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "features.yml"


def load_config(config_path: Path = _CONFIG_PATH) -> dict[str, Any]:
    """Load feature-engineering configuration."""
    with config_path.open(encoding="utf-8") as config_file:
        return yaml.safe_load(config_file) or {}


def run() -> None:
    """Run feature pipelines before applying configured retention."""
    features_repo = FeaturesRepository()
    klines_repo = KlinesRepository()
    tickers_repo = TickersRepository()

    klines_pipeline = KlinesPipeline(klines_repo, features_repo)
    orderbook_pipeline = OrderbookPipeline(tickers_repo, features_repo)
    ticker_pipeline = Ticker24hrPipeline(tickers_repo, features_repo)

    try:
        for timeframe in ("15m", "1h", "24h"):
            klines_pipeline.run(timeframe)
        for timeframe in ("15m", "1h", "24h"):
            orderbook_pipeline.run(timeframe)
        ticker_pipeline.run()

        retention = load_config().get("retention", {})
        if not isinstance(retention, dict):
            raise TypeError("Configuração 'retention' deve ser um mapeamento.")
        RetentionCleaner(RetentionRepository()).run_retention_policy(retention)
    except Exception:
        logger.exception("Execução de feature engineering falhou.")
        raise


if __name__ == "__main__":
    setup_logging()
    run()
