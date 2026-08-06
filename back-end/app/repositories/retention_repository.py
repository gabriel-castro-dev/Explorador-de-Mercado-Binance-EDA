from app.repositories.base import BaseRepository


class RetentionRepository(BaseRepository):
    """Data access layer for retention cleanup operations."""

    def delete_old_data(self, table_name: str, time_column: str, interval: str) -> None:
        """Execute the ``clean_old_data`` RPC on Supabase.

        Args:
            table_name: Name of the table to clean.
            time_column: Column used to evaluate the retention age.
            interval: Retention interval (e.g., '30 days').
        """
        self.supabase.rpc(
            "clean_old_data",
            {
                "table_name": table_name,
                "time_column": time_column,
                "retention_interval": interval,
            },
        ).execute()