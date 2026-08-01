import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RetentionCleaner:
    """Orquestrador da política de retenção de dados."""

    TIMESTAMP_COLUMNS = {
        "klines_15m": "open_time",
        "klines_1h": "open_time",
        "klines_1d": "open_time",
        "ticker_24hr_history": "open_time",
        "orderbook_tickers": "fetched_at",
        "features_15m": "timestamp",
        "features_1h": "timestamp",
        "features_24h": "timestamp",
    }

    def __init__(self, retention_repository: Any):
        self.repo = retention_repository

    def clean_table(self, table_name: str, interval: str) -> None:
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

    def run_retention_policy(self, retention_config: Dict[str, str]) -> None:
        logger.info("Iniciando execução da política de retenção...")
        for table_name, interval in retention_config.items():
            self.clean_table(table_name, interval)
        logger.info("Política de retenção concluída.")
