"""Reads for the symbols reference table."""

from app.repositories.base import BaseRepository


class SymbolsRepository(BaseRepository):
    """Data access for the tracked-symbols reference table."""

    def list_symbols(self) -> list[dict]:
        """All tracked symbols in alphabetical order."""
        return self.supabase.table("symbols").select("*").order("symbol").execute().data

    def ensure_symbols(self, symbols: list[str]) -> None:
        """Insert any missing symbols so FK constraints on data tables hold.

        The klines/features tables reference ``symbols(symbol)``; only the
        ticker ingestion has a trigger that auto-inserts. Any other write
        path (e.g. the historical backfill) must seed the reference first.
        """
        if not symbols:
            return
        self.supabase.table("symbols").upsert(
            [{"symbol": symbol} for symbol in symbols],
            on_conflict="symbol",
            ignore_duplicates=True,
        ).execute()
