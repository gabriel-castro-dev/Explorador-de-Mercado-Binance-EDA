"""Persistence for calculated feature rows."""

import logging
from typing import Any

import pandas as pd
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FeaturesRepository(BaseRepository):
    """Store calculated features in their timeframe-specific tables."""

    _TABLES: dict[str, str] = {
        "15m": "features_15m",
        "1h": "features_1h",
        "24h": "features_24h",
    }
    _GENERATED_COLUMNS: frozenset[str] = frozenset(
        {"macd", "macd_histogram", "bb_width"}
    )

    def save_features(self, timeframe: str, df: pd.DataFrame) -> None:
        """Upsert features using the (symbol, timestamp) conflict key.

        Args:
            timeframe: Feature timeframe key (e.g., '15m', '1h', '24h').
            df: DataFrame with the feature rows to persist.

        Raises:
            ValueError: If the timeframe is not supported.
        """
        if df.empty:
            logger.warning("Nenhuma feature para salvar no timeframe %s.", timeframe)
            return
        try:
            table = self._TABLES[timeframe]
        except KeyError as error:
            raise ValueError(
                f"Timeframe não suportado: {timeframe!r}. Use um de: {', '.join(self._TABLES)}."
            ) from error

        payload = self._to_records(
            df.drop(columns=self._GENERATED_COLUMNS, errors="ignore")
        )
        if not payload:
            logger.warning(
                "Nenhuma feature válida para salvar no timeframe %s.", timeframe
            )
            return
        try:
            self.supabase.table(table).upsert(
                payload, on_conflict="symbol,timestamp"
            ).execute()
            logger.info("%s features salvas em %s.", len(payload), table)
        except Exception:
            logger.exception("Falha ao salvar features em %s.", table)
            raise

    @staticmethod
    def _to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert Pandas nulls and timestamps to Supabase-compatible records.

        Args:
            df: DataFrame with the feature rows.

        Returns:
            List of dicts ready for a Supabase upsert.
        """
        normalized = df.replace([float("inf"), float("-inf")], None)
        normalized = normalized.astype(object).where(pd.notna(normalized), None)
        records: list[dict[str, Any]] = normalized.to_dict(orient="records")
        for record in records:
            for column, value in record.items():
                if isinstance(value, pd.Timestamp):
                    record[column] = value.isoformat()
        return records
