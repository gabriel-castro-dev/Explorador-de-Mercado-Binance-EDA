import logging
import time
from collections.abc import Callable, Iterator
from typing import Optional

from binance.client import Client

from config import get_settings

logger = logging.getLogger(__name__)


class BinanceUnauthorizedError(PermissionError):
    """The API key lacks permission for the requested endpoint (code -2015)."""


class BinanceInvalidSymbolError(KeyError):
    """An invalid symbol or parameter was sent to the API (codes -1100/-1121)."""


def _raise_if_fatal(error: Exception, context: str) -> None:
    """Convert non-retryable API errors into typed exceptions.

    Args:
        error: Exception raised by the Binance SDK.
        context: Human-readable description of the failed request.

    Raises:
        BinanceUnauthorizedError: For permission errors (code -2015).
        BinanceInvalidSymbolError: For invalid symbols/parameters (-1100/-1121).
    """
    error_msg = str(error)
    if "APIError(code=-2015)" in error_msg:
        logger.error("Erro de permissão: %s", context)
        raise BinanceUnauthorizedError(
            f"Failed request ({context}): user doesn't have permission to do this request."
        )
    if "APIError(code=-1100)" in error_msg or "APIError(code=-1121)" in error_msg:
        logger.error("Símbolo/parâmetro inválido: %s", context)
        raise BinanceInvalidSymbolError(
            f"Failed request ({context}): invalid symbol or parameter provided."
        )


def call_with_retry(
    fn: Callable[[], object],
    *,
    retries: int,
    delay: float,
    context: str,
    validate: Callable[[object], bool] = bool,
    empty: object = None,
    sleep: Callable[[float], None] = time.sleep,
):
    """Call ``fn`` with retries, typed fatal errors, and a silent-empty fallback.

    Args:
        fn: Zero-argument callable performing the API request.
        retries: Maximum number of attempts.
        delay: Seconds to wait between attempts.
        context: Human-readable description used in log messages.
        validate: Predicate deciding whether a result is acceptable.
        empty: Value returned after exhausting all retries.
        sleep: Injectable sleep function (for tests).

    Returns:
        The first result accepted by ``validate``, or ``empty`` on exhaustion.

    Raises:
        BinanceUnauthorizedError: For permission errors (code -2015).
        BinanceInvalidSymbolError: For invalid symbols/parameters (-1100/-1121).
    """
    for attempt in range(retries):
        try:
            data = fn()
            if validate(data):
                return data
        except Exception as error:  # noqa: BLE001
            _raise_if_fatal(error, context)
            logger.warning("[Tentativa %s/%s] %s: %s", attempt + 1, retries, context, error)
        if attempt < retries - 1:
            sleep(delay)
    logger.error("Falha após %s tentativas: %s", retries, context)
    return empty


class BinanceClient:
    """Client for the Binance REST market data API.

    Encapsulates all HTTP calls to the Binance REST API, including
    retry logic with connectivity validation. The number of attempts
    and the delay between them are driven by the ``MAX_RETRIES`` and
    ``RETRY_DELAY`` settings.

    Attributes:
        client: Authenticated Binance SDK client.
        api_key: Binance API key.
        api_secret: Binance API secret.
        test_net: Whether the testnet environment is enabled.
    """

    def __init__(self) -> None:
        """Initialize the Binance client and validate the connection.

        Raises:
            RuntimeError: If the connection to the Binance API cannot be established.
        """
        try:
            settings = get_settings()
            self.api_key: str = settings.BINANCE_API_KEY
            self.api_secret: str = settings.BINANCE_API_SECRET
            self.test_net: bool = settings.USE_TESTNET

            requests_params = None
            if settings.BINANCE_PROXY:
                requests_params = {
                    "proxies": {
                        "http": settings.BINANCE_PROXY,
                        "https": settings.BINANCE_PROXY,
                    }
                }

            self.client: Client = Client(
                self.api_key,
                self.api_secret,
                testnet=self.test_net,
                requests_params=requests_params,
            )
            self.MAX_RETRIES = settings.MAX_RETRIES
            self.RETRY_DELAY = settings.RETRY_DELAY
            logger.info("BinanceClient inicializado com sucesso")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Falha crítica ao conectar na API: {e}")
            raise RuntimeError(f"Falha crítica: Não foi possível conectar à API. Erro: {e}")

    def ping(self) -> bool:
        """Check connectivity with the Binance API.

        Returns:
            True if the API is reachable, False otherwise.
        """
        try:
            resultado = self.client.ping()
            if resultado == {}:
                logger.debug("API Binance está acessível")
                return True

            logger.warning(f"Erro inesperado ao fazer ping: {resultado}")
            return False

        except Exception as e:  # noqa: BLE001
            logger.error(f"Erro ao fazer ping na API: {e}")
            return False

    def server_time(self) -> dict | None:
        """Fetch the current Binance server time.

        Returns:
            Dict containing the server timestamp, or None on failure.
        """
        try:
            data = self.client.get_server_time()
            return data
        except Exception as e:  # noqa: BLE001
            logger.error(f"Erro ao obter tempo do servidor: {e}")
            return None

    def system_status(self) -> dict | None:
        """Fetch the current Binance system status.

        Returns:
            Dict containing the system status, or None on failure.
        """
        try:
            data = self.client.get_system_status()
            return data
        except Exception as e:  # noqa: BLE001
            logger.error(f"Erro ao obter status do sistema: {e}")
            return None

    def get_tickers(self) -> list:
        """Fetch all market tickers, ordered by price.

        Returns:
            List of ticker dicts, or an empty list after exhausting all retries.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
        """
        return call_with_retry(
            self.client.get_all_tickers,
            retries=self.MAX_RETRIES,
            delay=self.RETRY_DELAY,
            context="tickers",
            validate=lambda data: isinstance(data, list) and len(data) > 0,
            empty=[],
        )

    def get_ticker_24hr(self, symbol: str) -> dict:
        """Fetch 24-hour ticker data for a trading pair.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').

        Returns:
            Dict with 24-hour ticker data, or an empty dict after exhausting all retries.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
            BinanceInvalidSymbolError: If the provided symbol is invalid.
        """
        return call_with_retry(
            lambda: self.client.get_ticker(symbol=symbol),
            retries=self.MAX_RETRIES,
            delay=self.RETRY_DELAY,
            context=f"ticker 24hr de {symbol}",
            validate=lambda data: isinstance(data, dict),
            empty={},
        )

    def get_orderbook_tickers(self, symbol: str | list) -> list | dict:
        """Fetch order book ticker information for one or more pairs.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT') or a list of pairs.

        Returns:
            List or dict with order book data, or an empty list after
            exhausting all retries.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
            BinanceInvalidSymbolError: If the provided symbol is invalid.
        """
        return call_with_retry(
            lambda: self.client.get_orderbook_tickers(symbol=symbol),
            retries=self.MAX_RETRIES,
            delay=self.RETRY_DELAY,
            context=f"orderbook de {symbol}",
            validate=lambda data: isinstance(data, (list, dict)),
            empty=[],
        )

    def get_klines(self, symbol: str, interval: str) -> list:
        """Fetch real-time kline (candlestick) data for a trading pair.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            interval: Candlestick interval (e.g., '1m', '1h', '1d').

        Returns:
            List of kline rows, or an empty list after exhausting all retries.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
            BinanceInvalidSymbolError: If an invalid parameter is provided.
        """
        return call_with_retry(
            lambda: self.client.get_klines(symbol=symbol, interval=interval),
            retries=self.MAX_RETRIES,
            delay=self.RETRY_DELAY,
            context=f"k-lines de {symbol}",
            validate=lambda data: isinstance(data, list) and len(data) > 0,
            empty=[],
        )

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_str: str,
        end_str: Optional[str] = None,  # noqa: UP045
        limit: int = 1000,
    ) -> list:
        """Fetch historical klines for a specific period.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            interval: Candlestick interval (e.g., '1h', '1d').
            start_str: Start date (e.g., '10 days ago UTC').
            end_str: End date (optional).
            limit: Maximum number of records to fetch.

        Returns:
            List of kline rows, or an empty list after exhausting all retries.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
            BinanceInvalidSymbolError: If an invalid parameter is provided.
        """
        return call_with_retry(
            lambda: self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit,
            ),
            retries=self.MAX_RETRIES,
            delay=self.RETRY_DELAY,
            context=f"k-lines históricas de {symbol}",
            validate=lambda data: isinstance(data, list) and len(data) > 0,
            empty=[],
        )

    def get_historical_klines_generator(
        self,
        symbol: str,
        interval: str,
        start_str: Optional[str] = None,
        end_str: Optional[str] = None,  # noqa: UP045
    ) -> Iterator[list]:
        """Stream historical klines with retry that covers the iteration.

        On a transient failure mid-stream, the generator is recreated from
        the last kline already yielded (open_time + 1ms), so no rows are
        duplicated or lost. The retry budget resets whenever progress is
        made.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            interval: Candlestick interval (e.g., '1h', '1d').
            start_str: Start date (e.g., '100 days ago UTC').
            end_str: Optional end date.

        Yields:
            Raw kline rows.

        Raises:
            BinanceUnauthorizedError: If the API key lacks permission.
            BinanceInvalidSymbolError: If an invalid parameter is provided.
        """
        context = f"generator de k-lines históricas de {symbol}"
        start: str | int = start_str
        failures = 0
        while True:
            try:
                for row in self.client.get_historical_klines_generator(
                    symbol=symbol, interval=interval, start_str=start, end_str=end_str
                ):
                    failures = 0
                    start = row[0] + 1
                    yield row
                return
            except Exception as error:  # noqa: BLE001
                _raise_if_fatal(error, context)
                failures += 1
                if failures >= self.MAX_RETRIES:
                    logger.error("Falha após %s tentativas: %s", failures, context)
                    return
                logger.warning(
                    "[Tentativa %s/%s] %s: %s",
                    failures,
                    self.MAX_RETRIES,
                    context,
                    error,
                )
                time.sleep(self.RETRY_DELAY)
