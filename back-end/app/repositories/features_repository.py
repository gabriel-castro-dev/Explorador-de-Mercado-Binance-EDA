"""Persistence for calculated feature rows."""

import logging
from datetime import datetime
from typing import Any

import pandas as pd

from app.core.timeframe import Timeframe
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class FeaturesRepository(BaseRepository):
    _TABLES = {"15m": "features_15m", "1h": "features_1h", "24h": "features_24h"}
    _GENERATED_COLUMNS = frozenset({"macd", "macd_histogram", "bb_width"})

    def get_all_features(self, timeframe: Timeframe) -> pd.DataFrame:
        """Read the whole feature table, paginating past the PostgREST row cap.

        Unbounded selects are truncated at the project's max-rows setting; the
        ML dataset would silently lose every symbol after the cutoff.
        """
        rows = self._fetch_all(
            lambda: (
                self.supabase.table(timeframe.feature_table)
                .select("*")
                .order("symbol")
                .order("timestamp")
            )
        )
        return pd.DataFrame(rows)

    def query_features(
        self,
        timeframe: Timeframe,
        symbol: str,
        limit: int = 200,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[dict]:
        """Read indicator rows for one symbol, newest first, with optional filters."""
        query = (
            self.supabase.table(timeframe.feature_table)
            .select("*")
            .eq("symbol", symbol)
            .order("timestamp", desc=True)
            .limit(limit)
        )
        if start is not None:
            query = query.gte("timestamp", start.isoformat())
        if end is not None:
            query = query.lte("timestamp", end.isoformat())
        return query.execute().data

    def save_features(self, timeframe: str, df: pd.DataFrame) -> None:
        if df.empty:
            logger.warning("Nenhuma feature para salvar no timeframe %s.", timeframe)
            return
        try:
            table = self._TABLES[timeframe]
        except KeyError as error:
            raise ValueError(f"Timeframe não suportado: {timeframe!r}.") from error
        sanitized = df.drop(columns=self._GENERATED_COLUMNS, errors="ignore")
        try:
            self._upsert_in_batches(
                table, self._to_records(sanitized), on_conflict="symbol,timestamp"
            )
            logger.info("%s features salvas em %s.", len(sanitized), table)
        except Exception:
            logger.exception("Falha ao salvar features em %s.", table)
            raise

    @staticmethod
    def _to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        normalized = df.replace([float("inf"), float("-inf")], None)
        normalized = normalized.astype(object).where(pd.notna(normalized), None)
        records = normalized.to_dict(orient="records")
        for record in records:
            for column, value in record.items():
                if isinstance(value, pd.Timestamp):
                    record[column] = value.isoformat()
        return records
