"""Persistence for liquidity and 24-hour summary tables."""

import logging

import pandas as pd

from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TickersRepository(BaseRepository):
    """Data access layer for liquidity and 24-hour summary tables."""

    def get_latest_orderbook_tickers(self) -> pd.DataFrame:
        """Read retained order-book snapshots in chronological order."""
        response = (
            self.supabase.table("orderbook_tickers")
            .select("*")
            .order("symbol")
            .order("fetched_at")
            .execute()
        )
        return pd.DataFrame(response.data)

    def get_latest_ticker_24hr(self) -> pd.DataFrame:
        """Read retained 24-hour ticker snapshots in chronological order."""
        response = (
            self.supabase.table("ticker_24hr_history")
            .select("*")
            .order("symbol")
            .order("open_time")
            .execute()
        )
        return pd.DataFrame(response.data)

    def get_latest_24h_snapshots(
        self, symbol: str | None = None, tracked: bool | None = None
    ) -> list[dict]:
        """Latest ticker_24hr_history row per symbol (or for one symbol).

        Reads the ``ticker_24hr_latest`` view (``DISTINCT ON (symbol)`` done
        in Postgres), so every symbol of the newest batch is returned no
        matter how many rows the job writes per run.

        Args:
            symbol: Restrict to one symbol.
            tracked: When given, keep only symbols with (``True``) or without
                (``False``) candles in ``klines_1d``; ``None`` returns all.
        """
        query = self.supabase.table("ticker_24hr_latest").select("*")
        if symbol:
            query = query.eq("symbol", symbol)
        if tracked is not None:
            query = query.eq("tracked", tracked)
        return query.order("symbol").execute().data

    def upsert_ticker_24hr(self, df: pd.DataFrame) -> int:
        """Upsert normalized 24-hour ticker rows keyed on (symbol, open_time).

        Args:
            df: Rows already normalized to the table's column names.

        Returns:
            Number of rows persisted.

        Raises:
            Exception: Propagated from Supabase on failure.
        """
        records = df.to_dict(orient="records")
        self.supabase.table("ticker_24hr_history").upsert(
            records, on_conflict="symbol,open_time"
        ).execute()
        logger.info("%s registros de tickers 24h persistidos.", len(records))
        return len(records)

    def upsert_orderbook_tickers(self, df: pd.DataFrame) -> int:
        """Upsert normalized order-book rows keyed on (symbol, fetched_at).

        Args:
            df: Rows already normalized to the table's column names.

        Returns:
            Number of rows persisted.

        Raises:
            Exception: Propagated from Supabase on failure.
        """
        records = df.to_dict(orient="records")
        self.supabase.table("orderbook_tickers").upsert(
            records, on_conflict="symbol,fetched_at"
        ).execute()
        logger.info("%s registros de orderbook persistidos.", len(records))
        return len(records)
