"""Canonical timeframe vocabulary shared by the API, repositories and pipelines."""

from enum import Enum


class Timeframe(str, Enum):
    """A market-data timeframe and everything derived from it.

    Canonical values are the kline spellings ("15m", "1h", "1d");
    "24h" is accepted as an alias for D1 because the feature tables
    use that historical name (features_24h).
    """

    M15 = "15m"
    H1 = "1h"
    D1 = "1d"

    @classmethod
    def _missing_(cls, value: object) -> "Timeframe | None":
        if value == "24h":  # grafia legada das tabelas de features
            return cls.D1
        return None

    @property
    def kline_table(self) -> str:
        """Raw candle table for this timeframe."""
        return {"15m": "klines_15m", "1h": "klines_1h", "1d": "klines_1d"}[self.value]

    @property
    def feature_table(self) -> str:
        """Calculated-indicator table for this timeframe."""
        return {"15m": "features_15m", "1h": "features_1h", "1d": "features_24h"}[self.value]

    @property
    def pandas_freq(self) -> str:
        """Pandas resample frequency string."""
        return {"15m": "15min", "1h": "h", "1d": "D"}[self.value]

    @property
    def time_column(self) -> str:
        """Time column of the kline tables."""
        return "open_time"

    @property
    def feature_time_column(self) -> str:
        """Time column of the feature tables."""
        return "timestamp"
