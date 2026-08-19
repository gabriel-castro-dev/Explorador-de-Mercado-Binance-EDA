import logging
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings loaded from environment variables and the ``.env`` file.

    Attributes:
        MAX_RETRIES: Number of API retry attempts.
        RETRY_DELAY: Delay in seconds between retries.
        SUPABASE_URL: Supabase project URL.
        SUPABASE_KEY: Supabase public key.
        BINANCE_API_KEY: Binance API key.
        BINANCE_API_SECRET: Binance API secret.
        USE_TESTNET: Whether to use the Binance testnet.
        BINANCE_PROXY: Optional HTTP(S) proxy URL.
        LOG_LEVEL: Logging level for the application.
        LOG_FORMAT: Format string for log messages.
        LOG_DATE_FORMAT: Date format for log timestamps.
    """

    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    SUPABASE_URL: str
    SUPABASE_KEY: str
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    USE_TESTNET: bool = True
    BINANCE_PROXY: Optional[str] = None

    @field_validator("BINANCE_API_KEY", "BINANCE_API_SECRET", "SUPABASE_KEY")
    @classmethod
    def strip_values(cls, v: str) -> str:
        """Strip surrounding whitespace from sensitive string settings.

        Args:
            v: Value to strip.

        Returns:
            The stripped value, or the original value if it is not a string.
        """
        if isinstance(v, str):
            return v.strip()
        return v

    LOG_LEVEL: int = logging.INFO
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DATE_FORMAT: str = "%d/%m/%Y %H:%M:%S"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Build (once) and return the application settings.

    Lazy construction keeps imports side-effect free: environment
    variables are only required when a component actually needs them.
    """
    return Settings()


def setup_logging():
    """Configure the root logger with a stream handler.

    Initializes logging with the level, format, and date format defined
    in the application settings.
    """
    settings = get_settings()
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        datefmt=settings.LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler()],
    )
