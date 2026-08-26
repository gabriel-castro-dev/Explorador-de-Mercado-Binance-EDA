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
    # Exigidas só por quem conecta à Binance (BinanceClient valida na conexão):
    # jobs de ML, feature engineering e API falam apenas com o Supabase.
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    # Real Binance by default: market-data endpoints are public and the ML
    # dataset needs real prices/volumes (the testnet keeps ~2 weeks of
    # synthetic history only). Set USE_TESTNET=true explicitly for testnet.
    USE_TESTNET: bool = False
    BINANCE_PROXY: Optional[str] = None

    # --- API (FastAPI) ---
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = (
        None  # sb_publishable_... ou anon legacy; NUNCA service_role
    )
    SUPABASE_JWT_SECRET: Optional[str] = (
        None  # fallback HS256 legado; prefira signing keys assimetricas
    )
    API_CORS_ORIGINS: str = "http://localhost:3000"  # separado por virgula; default dev Nuxt
    API_VERSION: str = "0.1.0"

    # --- Firebase / Firestore (preferencias do usuario) ---
    # A credencial NUNCA vai para o git nem para dentro da imagem Docker:
    # em dev aponta para o arquivo local; no container, monte um volume
    # read-only (PATH) ou injete o conteudo do JSON (CREDENTIALS_JSON).
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None
    FIRESTORE_COLLECTION: str = "user_preferences"

    # --- Gateways de LLM (leitura do dia; as chaves ficam SO no servidor) ---
    # Cadeia de fallback, na ordem: OpenCode Zen deepseek-v4-flash-free ->
    # OpenCode Zen nemotron-3-ultra-free -> OpenRouter nemotron :free.
    # Slugs verificados em 2026-08-23 nos /models dos dois gateways: o Zen tem
    # "deepseek-v4-flash-free"; no OpenRouter o deepseek v4 flash NAO tem
    # variante ":free" (por isso o fallback la e o Nemotron gratuito).
    # Um gateway sem chave configurada e pulado na cadeia.
    OPENCODE_ZEN_API_KEY: Optional[str] = None
    OPENCODE_ZEN_MODEL: str = "deepseek-v4-flash-free"
    OPENCODE_ZEN_FALLBACK_MODEL: Optional[str] = "nemotron-3-ultra-free"
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    DAILY_READINGS_COLLECTION: str = "daily_readings"

    @field_validator(
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "SUPABASE_KEY",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_JWT_SECRET",
        "FIREBASE_CREDENTIALS_PATH",
        "FIREBASE_CREDENTIALS_JSON",
        "OPENCODE_ZEN_API_KEY",
        "OPENROUTER_API_KEY",
    )
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
