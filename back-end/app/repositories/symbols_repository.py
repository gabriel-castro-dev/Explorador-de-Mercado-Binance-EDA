"""Reads for the symbols reference table."""

from app.repositories.base import BaseRepository


class SymbolsRepository(BaseRepository):
    """Data access for the symbols reference table.

    Reads come from the ``symbols_with_tracking`` view, which adds the
    data-derived ``tracked`` flag (the symbol has candles in ``klines_1d``);
    writes still target the base ``symbols`` table.
    """

    def list_symbols(self, tracked: bool | None = None) -> list[dict]:
        """All symbols in alphabetical order, each with its ``tracked`` flag.

        Args:
            tracked: When given, keep only tracked (``True``) or untracked
                (``False``) symbols; ``None`` returns the whole table.
        """
        query = self.supabase.table("symbols_with_tracking").select("*")
        if tracked is not None:
            query = query.eq("tracked", tracked)
        return query.order("symbol").execute().data

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
