"""Pipeline for OHLCV-derived features."""

import logging

from app.feature_engineering.pipelines.base import BasePipeline
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository

logger = logging.getLogger(__name__)


class KlinesPipeline(BasePipeline):
    """Calculate and persist technical indicators from stored candles."""

    _FEATURE_GROUPS: dict[str, str] = {
        "15m": "features_15m",
        "1h": "features_1h",
        "24h": "features_24h",
    }
    _DESTINATION_COLUMNS: tuple[str, ...] = (
        "symbol",
        "timestamp",
        "sma_20",
        "sma_50",
        "sma_200",
        "ema_12",
        "ema_26",
        "rsi_14",
        "macd_signal",
        "avg_price_deviation_sma20",
        "avg_price_deviation_sma50",
        "avg_price_deviation_sma200",
        "bb_upper",
        "bb_middle",
        "bb_lower",
        "atr_14",
        "bid_ask_spread",
        "order_imbalance",
        "price_change_percent",
        "volume_change_24h",
        "volume_sma_20",
    )

    def __init__(
        self, klines_repo: KlinesRepository, features_repo: FeaturesRepository
    ) -> None:
        """Initialize the pipeline with data access dependencies.

        Args:
            klines_repo: Repository used to read persisted candles.
            features_repo: Repository used to persist the calculated features.
        """
        super().__init__()
        self.klines_repo = klines_repo
        self.features_repo = features_repo

    def run(self, timeframe: str) -> None:
        """Fetch candles, calculate the configured features, then upsert them.

        Args:
            timeframe: Target timeframe key (e.g., '15m', '1h', '24h').

        Raises:
            ValueError: If the timeframe is not supported or candles lack 'open_time'.
        """
        try:
            feature_group = self._FEATURE_GROUPS[timeframe]
        except KeyError as error:
            raise ValueError(f"Timeframe não suportado: {timeframe!r}.") from error
        try:
            candles = self.klines_repo.get_latest_klines(
                "1d" if timeframe == "24h" else timeframe
            )
            if candles.empty:
                logger.warning("Nenhum candle encontrado para timeframe %s.", timeframe)
                return
            processed = self.apply_transforms(candles, feature_group)
            macd_line = processed["ema_12"] - processed["ema_26"]
            processed["macd_signal"] = macd_line.groupby(
                processed["symbol"], sort=False
            ).transform(lambda values: values.ewm(span=9, adjust=False).mean())
            if "open_time" not in processed.columns:
                raise ValueError("Candles devem conter a coluna 'open_time'.")
            processed = processed.rename(columns={"open_time": "timestamp"})
            self.features_repo.save_features(
                timeframe, processed.reindex(columns=self._DESTINATION_COLUMNS)
            )
        except Exception:
            logger.exception(
                "Falha no pipeline de klines para timeframe %s.", timeframe
            )
            raise
