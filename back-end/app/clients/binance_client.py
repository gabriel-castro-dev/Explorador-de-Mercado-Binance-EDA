import logging
import time
from collections.abc import Iterator
from typing import Optional

from binance.client import Client
from config import settings

logger = logging.getLogger(__name__)


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
            raise RuntimeError(
                f"Falha crítica: Não foi possível conectar à API. Erro: {e}"
            )

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
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                data = self.client.get_all_tickers()
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error("Erro de permissão ao obter tickers")
                    raise PermissionError(
                        "Failed to retrieve tickers, user doesn't have permission to do this request."
                    )
                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Aguardando {self.RETRY_DELAY}s para retry...")
                    time.sleep(self.RETRY_DELAY)

        logger.error("Falha ao obter tickers após todas as tentativas")
        return []

    def get_ticker_24hr(self, symbol: str) -> dict:
        """Fetch 24-hour ticker data for a trading pair.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').

        Returns:
            Dict with 24-hour ticker data, or an empty dict after exhausting all retries.

        Raises:
            PermissionError: If the API key lacks permission for this request.
            KeyError: If the provided symbol is invalid.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                data = self.client.get_ticker(symbol=symbol)
                if isinstance(data, dict):
                    return data
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error(f"Erro de permissão para {symbol}")
                    raise PermissionError(
                        f"Failed to retrieve last 24hrs ticker for {symbol}, user doesn't have permission to do this request."
                    )
                if (
                    "APIError(code=-1100)" in error_msg
                    or "APIError(code=-1121)" in error_msg
                ):
                    logger.error(f"Símbolo inválido: {symbol}")
                    raise KeyError(
                        f"Failed to get ticker 24hr for {symbol}, invalid symbol provided."
                    )

                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] Erro para {symbol}: {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        logger.error("Falha ao obter dados 24h após todas as tentativas")
        return {}

    def get_orderbook_tickers(self, symbol: str | list) -> list | dict:
        """Fetch order book ticker information for one or more pairs.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT') or a list of pairs
                (e.g., ['BTCUSDT', 'ETHUSDT']).

        Returns:
            List or dict with order book data, or an empty list after
            exhausting all retries.

        Raises:
            PermissionError: If the API key lacks permission for this request.
            KeyError: If the provided symbol is invalid.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                data = self.client.get_orderbook_tickers(symbol=symbol)
                if isinstance(data, (list, dict)):
                    return data
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error(f"Erro de permissão para {symbol}")
                    raise PermissionError(
                        f"Failed to retrieve orderbook tickers for {symbol}, user doesn't have permission to do this request."
                    )
                if (
                    "APIError(code=-1100)" in error_msg
                    or "APIError(code=-1121)" in error_msg
                ):
                    logger.error(f"Símbolo inválido: {symbol}")
                    raise KeyError(
                        f"Failed to retrieve orderbook tickers for {symbol}, invalid symbol provided."
                    )
                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        logger.error(f"Falha ao obter order book para {symbol}")
        return []

    def get_klines(self, symbol: str, interval: str) -> list:
        """Fetch real-time kline (candlestick) data for a trading pair.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            interval: Candlestick interval (e.g., '1m', '1h', '1d').

        Returns:
            List of kline rows, or an empty list after exhausting all retries.

        Raises:
            PermissionError: If the API key lacks permission for this request.
            KeyError: If an invalid parameter is provided.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                data = self.client.get_klines(symbol=symbol, interval=interval)
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error(f"Erro de permissão para {symbol}")
                    raise PermissionError(
                        f"Failed to retrieve last klines for {symbol}, user doesn't have permission to do this request."
                    )
                if (
                    "APIError(code=-1100)" in error_msg
                    or "APIError(code=-1121)" in error_msg
                ):
                    logger.error(f"Parâmetro inválido para {symbol}")
                    raise KeyError(
                        f"Failed to retrieve klines for {symbol}, invalid parameter provided."
                    )
                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        logger.error(f"Falha ao obter k-lines para {symbol}")
        return []

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
            PermissionError: If the API key lacks permission for this request.
            KeyError: If an invalid parameter is provided.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                data = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_str,
                    end_str=end_str,
                    limit=limit,
                )
                if isinstance(data, list) and len(data) > 0:
                    return data
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error(f"Erro de permissão para {symbol}")
                    raise PermissionError(
                        f"Failed to retrieve historical klines for {symbol}, user doesn't have permission to do this request."
                    )
                if (
                    "APIError(code=-1100)" in error_msg
                    or "APIError(code=-1121)" in error_msg
                ):
                    logger.error("Parâmetro inválido em k-lines históricas")
                    raise KeyError(
                        "Failed to retrieve historical klines, invalid parameter provided."
                    )
                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        logger.error(f"Falha ao obter k-lines históricas para {symbol}")
        return []

    def get_historical_klines_generator(
        self, symbol: str, interval: str, timestamp: str
    ) -> Iterator[list]:
        """Fetch historical klines efficiently via the generator API.

        Efficient for large volumes of data.

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT').
            interval: Candlestick interval (e.g., '1h', '1d').
            timestamp: Start date (e.g., '100 days ago UTC').

        Returns:
            List of kline rows, or an empty list after exhausting all retries.

        Raises:
            PermissionError: If the API key lacks permission for this request.
            KeyError: If an invalid parameter is provided.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                return self.client.get_historical_klines_generator(
                    symbol=symbol, interval=interval, start_str=timestamp
                )
            except Exception as e:  # noqa: BLE001
                error_msg = str(e)
                if "APIError(code=-2015)" in error_msg:
                    logger.error(f"Erro de permissão para {symbol}")
                    raise PermissionError(
                        f"Failed to retrieve historical klines generator for {symbol}, user doesn't have permission to do this request."
                    )
                if (
                    "APIError(code=-1100)" in error_msg
                    or "APIError(code=-1121)" in error_msg
                ):
                    logger.error("Parâmetro inválido em generator de k-lines")
                    raise KeyError(
                        "Failed to retrieve historical klines generator, invalid parameter provided."
                    )
                logger.warning(
                    f"[Tentativa {attempt + 1}/{self.MAX_RETRIES}] {error_msg}"
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)

        logger.error(f"Falha ao gerar k-lines históricas para {symbol}")
        return []
