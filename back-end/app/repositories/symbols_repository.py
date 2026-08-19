"""Reads for the symbols reference table."""

from app.repositories.base import BaseRepository


class SymbolsRepository(BaseRepository):
    """Data access for the tracked-symbols reference table."""

    def list_symbols(self) -> list[dict]:
        """All tracked symbols in alphabetical order."""
        return self.supabase.table("symbols").select("*").order("symbol").execute().data
