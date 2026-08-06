"""Pipeline for 24-hour ticker context features."""

import logging

import pandas as pd
from app.feature_engineering.pipelines.base import BasePipeline
from app.feature_engineering.transforms.technical_indicators import (
    TechnicalIndicatorsTransform,
)
from app.repositories.features_repository import FeaturesRepository
from app.repositories.tickers_repository import TickersRepository

logger = logging.getLogger(__name__)


class Ticker24hrPipeline(BasePipeline):
    """Persist daily price and volume context from 24-hour ticker snapshots."""

    def __init__(
        self, tickers_repo: TickersRepository, features_repo: FeaturesRepository
    ) -> None:
        super().__init__()
        self.tickers_repo = tickers_repo
        self.features_repo = features_repo

    def run(self) -> None:
        """Calculate and save daily price and volume changes."""
        try:
            snapshots = self.tickers_repo.get_latest_ticker_24hr()
            if snapshots.empty:
                logger.warning("Nenhum ticker de 24h disponível.")
                return
            data = snapshots.copy()
            data["open_time"] = pd.to_datetime(data["open_time"], utc=True)
            data = data.sort_values(["symbol", "open_time"])
            data["timestamp"] = data["open_time"].dt.floor("1D")
            daily = (
                data.groupby(["symbol", "timestamp"], as_index=False)
                .agg(
                    price_change_percent=("price_change_percent", "last"),
                    volume=("volume", "last"),
                )
                .sort_values(["symbol", "timestamp"])
            )
            daily["volume_change_24h"] = (
                TechnicalIndicatorsTransform.calculate_change_percent(
                    daily, column="volume", period=1
                )
            )
            self.features_repo.save_features(
                "24h",
                daily[
                    ["symbol", "timestamp", "price_change_percent", "volume_change_24h"]
                ],
            )
        except Exception:
            logger.exception("Falha no pipeline ticker_24hr.")
            raise
