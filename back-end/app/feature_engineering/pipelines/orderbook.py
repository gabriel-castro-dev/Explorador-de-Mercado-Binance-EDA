"""Pipeline for order-book liquidity features."""

import logging

import pandas as pd

from app.feature_engineering.pipelines.base import BasePipeline
from app.feature_engineering.transforms.technical_indicators import (
    TechnicalIndicatorsTransform,
)
from app.repositories.features_repository import FeaturesRepository
from app.repositories.tickers_repository import TickersRepository

logger = logging.getLogger(__name__)


class OrderbookPipeline(BasePipeline):
    """Aggregate order-book snapshots and persist liquidity features."""

    _FREQUENCIES: dict[str, str] = {"15m": "15min", "1h": "1h", "24h": "1D"}

    def __init__(self, tickers_repo: TickersRepository, features_repo: FeaturesRepository) -> None:
        super().__init__()
        self.tickers_repo = tickers_repo
        self.features_repo = features_repo

    def run(self, timeframe: str) -> None:
        """Calculate bid-ask spread and order imbalance for one timeframe."""
        try:
            frequency = self._FREQUENCIES[timeframe]
        except KeyError as error:
            raise ValueError(f"Timeframe não suportado: {timeframe!r}.") from error
        try:
            snapshots = self.tickers_repo.get_latest_orderbook_tickers()
            if snapshots.empty:
                logger.warning("Nenhum snapshot de orderbook para %s.", timeframe)
                return
            data = snapshots.copy()
            data["fetched_at"] = pd.to_datetime(data["fetched_at"], utc=True)
            data = data.sort_values(["symbol", "fetched_at"])
            data["timestamp"] = data["fetched_at"].dt.floor(frequency)
            aggregated = data.groupby(["symbol", "timestamp"], as_index=False).agg(
                bid_price=("bid_price", "last"),
                ask_price=("ask_price", "last"),
                bid_qty=("bid_qty", "mean"),
                ask_qty=("ask_qty", "mean"),
            )
            aggregated["bid_ask_spread"] = TechnicalIndicatorsTransform.calculate_bid_ask_spread(
                aggregated
            )
            aggregated["order_imbalance"] = TechnicalIndicatorsTransform.calculate_order_imbalance(
                aggregated
            )
            self.features_repo.save_features(
                timeframe,
                aggregated[["symbol", "timestamp", "bid_ask_spread", "order_imbalance"]],
            )
        except Exception:
            logger.exception("Falha no pipeline orderbook para timeframe %s.", timeframe)
            raise
