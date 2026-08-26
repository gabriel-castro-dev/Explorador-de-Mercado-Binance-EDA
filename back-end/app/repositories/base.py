from collections.abc import Callable

from app.clients.supabase_client import get_supabase_client
from supabase import Client


class BaseRepository:
    """Base repository providing a shared Supabase connection.

    Specialized repositories inherit from this class to obtain a
    configured Supabase client for persistence queries, plus the two
    access patterns every table repository ends up needing: paginated
    full reads and batched upserts.

    Attributes:
        supabase: Configured Supabase client.
    """

    _READ_PAGE_SIZE = 1000
    _UPSERT_BATCH_SIZE = 500

    def __init__(self, supabase: Client | None = None):
        """Initialize the repository with an injected or default client.

        Args:
            supabase: Optional pre-built Supabase client; defaults to the
                factory-provided connection.
        """
        self.supabase = supabase or get_supabase_client()

    def _fetch_all(self, build_query: Callable[[], object]) -> list[dict]:
        """Read every row of a query, paginating past the PostgREST row cap.

        PostgREST truncates unbounded selects at the project's max-rows
        setting, so a single request silently drops every row after the
        cutoff. ``build_query`` must return a fresh, ordered query builder
        (without ``range``) on each call.
        """
        rows: list[dict] = []
        offset = 0
        while True:
            page = (build_query().range(offset, offset + self._READ_PAGE_SIZE - 1).execute()).data
            rows.extend(page)
            if len(page) < self._READ_PAGE_SIZE:
                return rows
            offset += self._READ_PAGE_SIZE

    def _upsert_in_batches(self, table: str, rows: list[dict], on_conflict: str) -> None:
        for start in range(0, len(rows), self._UPSERT_BATCH_SIZE):
            self.supabase.table(table).upsert(
                rows[start : start + self._UPSERT_BATCH_SIZE], on_conflict=on_conflict
            ).execute()
