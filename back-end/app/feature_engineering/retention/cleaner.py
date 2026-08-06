import logging
from typing import Any

logger = logging.getLogger(__name__)


class RetentionCleaner:
    """Orchestrator of the data retention policy.

    Reads the retention configuration and delegates the cleanup of each
    table to the retention repository via the ``clean_old_data`` RPC.

    Attributes:
        repo: RetentionRepository used to execute the cleanup RPCs.
        TIMESTAMP_COLUMNS: Mapping of table names to their timestamp columns.
    """

    def __init__(self, retention_repository: Any):
        """Initialize the retention cleaner.

        Args:
            retention_repository: Repository used to execute the retention RPCs.
        """
        self.repo = retention_repository
        self.TIMESTAMP_COLUMNS = {
            "klines_15m": "open_time",
            "klines_1h": "open_time",
            "klines_1d": "open_time",
            "ticker_24hr_history": "open_time",
            "orderbook_tickers": "fetched_at",
            "features_15m": "timestamp",
            "features_1h": "timestamp",
            "features_24h": "timestamp",
        }

    def clean_table(self, table_name: str, interval: str) -> None:
        """Clean a single table according to its retention interval.

        Args:
            table_name: Name of the table to clean.
            interval: Retention interval (e.g., '30 days') or 'permanent' to skip.

        Raises:
            Exception: If the retention RPC fails.
        """
        if interval.lower() == "permanent":
            logger.info(
                f"Tabela '{table_name}' configurada como PERMANENTE. Nenhuma limpeza efetuada."
            )
            return

        time_column = self.TIMESTAMP_COLUMNS.get(table_name, "timestamp")

        try:
            self.repo.delete_old_data(
                table_name=table_name, time_column=time_column, interval=interval
            )
            logger.info(f"Limpeza concluída em '{table_name}' (retenção: {interval}).")
        except Exception as e:
            logger.error(f"Erro ao limpar tabela '{table_name}': {e}")
            raise

    def run_retention_policy(self, retention_config: dict[str, str]) -> None:
        """Run the retention policy for all configured tables.

        Args:
            retention_config: Mapping of table names to retention intervals.
        """
        logger.info("Iniciando execução da política de retenção...")
        for table_name, interval in retention_config.items():
            self.clean_table(table_name, interval)
        logger.info("Política de retenção concluída.")
