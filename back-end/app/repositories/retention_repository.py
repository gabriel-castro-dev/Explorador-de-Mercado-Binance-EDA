from app.repositories.base import BaseRepository


class RetentionRepository(BaseRepository):
    def delete_old_data(self, table_name: str, time_column: str, interval: str) -> None:
        """Executa a RPC de limpeza no Supabase."""
        self.supabase.rpc(
            "clean_old_data",
            {
                "table_name": table_name,
                "time_column": time_column,
                "retention_interval": interval,
            },
        ).execute()
