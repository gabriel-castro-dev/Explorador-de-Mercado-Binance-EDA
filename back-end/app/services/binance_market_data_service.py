import logging
from typing import Optional

import pandas as pd
from app.clients.binance_client import BinanceClient

logger = logging.getLogger(__name__)


class BinanceMarketService:
    """Service for requesting and transforming market data from the Binance API.

    Encapsulates all transformations of the data returned by the Binance API,
    including:
    - Retry logic with connectivity validation
    - Transformation of raw data into structured DataFrames
    - Appropriate type casting (int, float, datetime)
    - Data validation and specific error handling

    Attributes:
        client: Authenticated BinanceClient used for market data requests.
    """

    def __init__(self, client: BinanceClient | None = None) -> None:
        """Initialize the market data service.

        Args:
            client: Optional pre-built Binance client; defaults to a new
                authenticated connection.

        Raises:
            RuntimeError: If the connection to the Binance API cannot be established.
        """
        if client is not None:
            self.client = client
            return
        try:
            self.client = BinanceClient()
            logger.info("BinanceMarketService inicializado com sucesso")
        except Exception as e:  # noqa: BLE001
            logger.error("Falha crítica ao iniciar cliente Binance")
            raise RuntimeError(f"{e}")

    def ping(self) -> str:
        """Check connectivity with the Binance API.

        Returns:
            Message describing the connection status.
        """
        resultado = self.client.ping()
        if resultado:
            return "Binance API is reachable."

        return "Error pinging Binance API"

    def server_time(self) -> dict:
        """Fetch the current Binance server time.

        Returns:
            Dict with the server timestamp, or an error dict on failure.
        """
        result = self.client.server_time()

        if result is None:
            return {
                "status": "error",
                "message": "Não foi possível obter o horário do servidor.",
            }

        return result

    def system_status(self) -> dict:
        """Fetch the current Binance system status.

        Returns:
            Dict with the system status, or an error dict on failure.
        """
        result = self.client.system_status()

        if result is None:
            return {
                "status": "error",
                "message": "Não foi possível obter o status do sistema.",
            }

        return result

    def get_tickers(self) -> pd.DataFrame:
        """Fetch all USDT trading pairs sorted by price.

        Returns:
            DataFrame with USDT tickers sorted by price, or an empty
            DataFrame on failure.
        """
        data = self.client.get_tickers()
        if data:
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                usdt_tickers = df[df["symbol"].str.endswith("USDT")].copy()
                usdt_tickers["price"] = pd.to_numeric(
                    usdt_tickers["price"], errors="coerce"
                )
                usdt_tickers["price"] = usdt_tickers["price"].round(2)
                usdt_tickers = usdt_tickers.dropna(subset=["price"])
                usdt_tickers = usdt_tickers.sort_values(
                    by="price", ascending=False
                ).reset_index(drop=True)
                logger.info(f"Obtidos {len(usdt_tickers)} tickers USDT")
                return usdt_tickers
        else:
            logger.error("Falha ao transformar tickers")
            return pd.DataFrame()

    def get_ticker_24hr(self) -> pd.DataFrame:
        """Fetch 24-hour data for the USDT trading pairs.

        Returns:
            DataFrame with 24-hour data, or an empty DataFrame on failure.
        """
        df_tickers = self.get_tickers()
        symbols = df_tickers["symbol"].tolist()
        all_data = []

        if not df_tickers.empty:
            for symbol in symbols:
                data = self.client.get_ticker_24hr(symbol=symbol)
                if isinstance(data, dict) and data:
                    all_data.append(data)

            if all_data:
                df = pd.DataFrame(all_data)
                ignorar_colunas = [
                    "symbol",
                    "openTime",
                    "closeTime",
                    "firstId",
                    "lastId",
                    "count",
                ]
                cols_to_numeric = [
                    col for col in df.columns if col not in ignorar_colunas
                ]
                df[cols_to_numeric] = df[cols_to_numeric].apply(
                    pd.to_numeric, errors="coerce"
                )
                df[cols_to_numeric] = df[cols_to_numeric].round(8)
                df = df.dropna(subset=cols_to_numeric)
                df["openTime"] = pd.to_datetime(df["openTime"], unit="ms")
                df["closeTime"] = pd.to_datetime(df["closeTime"], unit="ms")
                df[["symbol", "firstId", "lastId"]] = df[
                    ["symbol", "firstId", "lastId"]
                ].astype(str)
                df["count"] = df["count"].astype(int)
                logger.info(f"Dados 24h obtidos para {len(symbols)} símbolos")
                return df
            else:
                logger.error("Falha ao obter dados 24h para os tickers USDT")
                return pd.DataFrame()
        else:
            logger.error("Falha ao obter lista de tickers USDT")
            return pd.DataFrame()

    def get_top_20_tickers(self) -> pd.DataFrame:
        """Fetch the top 20 USDT tickers ranked by quote volume.

        Returns:
            DataFrame with the top 20 tickers, or an empty DataFrame on failure.
        """
        df_tickers = self.get_ticker_24hr()
        if not df_tickers.empty:
            sorted_df = df_tickers.sort_values(by="quoteVolume", ascending=False)
            top_20 = sorted_df.head(20).reset_index(drop=True)
            logger.info("Obtidos os 20 principais tickers USDT")
            return top_20
        else:
            logger.error("Falha ao obter os 20 principais tickers USDT")
            return pd.DataFrame(columns=["symbol"])

    def get_orderbook_tickers(self) -> pd.DataFrame:
        """Fetch order book information for the top 20 USDT pairs.

        Returns:
            DataFrame with order book data, or an empty DataFrame on failure.
        """

        df_tickers = self.get_top_20_tickers()
        symbols = df_tickers["symbol"].tolist()
        all_data = []

        if not df_tickers.empty:
            for symbol in symbols:
                data = self.client.get_orderbook_tickers(symbol=symbol)
                if isinstance(data, dict) and data:
                    all_data.append(data)
                    logger.info(f"Order book obtido para {symbol}")
                else:
                    logger.error(f"Falha ao obter order book para {symbol}")
        if all_data:
            df = pd.DataFrame(all_data)
            df["symbol"] = df["symbol"].astype(str)
            cols = ["bidPrice", "bidQty", "askPrice", "askQty"]

            df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")
            df[cols] = df[cols].round(8)
            df = df.dropna(subset=cols)

            logger.info(f"Order book obtido para {len(symbols)} símbolos")
            return df
        else:
            logger.error(f"Falha ao obter order book para {len(symbols)} símbolos")
            return pd.DataFrame()

    def get_klines(self, interval: str) -> pd.DataFrame:
        """Fetch real-time klines for all top 20 USDT pairs.

        Args:
            interval: Candlestick interval (e.g., '1m', '1h', '1d').

        Returns:
            DataFrame with OHLCV data, or an empty DataFrame on failure.
        """
        df_tickers = self.get_top_20_tickers()
        symbols = df_tickers["symbol"].tolist()
        all_data = []

        if not df_tickers.empty:
            for symbol in symbols:
                data = self.client.get_klines(symbol=symbol, interval=interval)
                if isinstance(data, list) and data:
                    for kline in data:
                        all_data.append(kline + [symbol])
                    logger.info(f"K-lines obtidas para {symbol} ({interval})")
                else:
                    logger.error(f"Falha ao obter k-lines para {symbol}")

        if all_data:
            columns = [
                "Open_Time",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Close_Time",
                "Quote_Asset_Volume",
                "Number_of_Trades",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
                "Ignore",
                "symbol",
            ]
            df = pd.DataFrame(data=all_data, columns=columns)
            df = df.drop(columns=["Ignore"])
            df["Open_Time"] = pd.to_datetime(df["Open_Time"], unit="ms")
            df["Close_Time"] = pd.to_datetime(df["Close_Time"], unit="ms")
            df["Number_of_Trades"] = df["Number_of_Trades"].astype(int)

            numeric_cols = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Quote_Asset_Volume",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
            ]

            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            df[numeric_cols] = df[numeric_cols].round(8)
            df = df.dropna(subset=numeric_cols)

            logger.info(
                f"Obtidas {len(df)} k-lines para {len(symbols)} símbolos ({interval})"
            )
            return df
        else:
            logger.error("Falha ao obter k-lines para os tickers USDT")
            return pd.DataFrame()

    def get_historical_klines(
        self,
        interval: str,
        start_str: str,
        end_str: Optional[str] = None,  # noqa: UP045
        limit: int = 1000,
    ) -> pd.DataFrame:
        """Fetch historical klines for a period across all top 20 USDT pairs.

        Args:
            interval: Candlestick interval (e.g., '1h', '1d').
            start_str: Start date (e.g., '10 days ago UTC').
            end_str: End date (optional).
            limit: Maximum number of records.

        Returns:
            DataFrame with historical klines, or an empty DataFrame on failure.
        """
        df_tickers = self.get_top_20_tickers()
        symbols = df_tickers["symbol"].tolist()
        all_data = []

        if not df_tickers.empty:
            for symbol in symbols:
                data = self.client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=start_str,
                    end_str=end_str,
                    limit=limit,
                )
                if isinstance(data, list) and data:
                    for kline in data:
                        all_data.append(kline + [symbol])
                    logger.info(f"K-lines históricas obtidas para {symbol}")
                else:
                    logger.error(f"Falha ao obter k-lines históricas para {symbol}")

        if all_data:
            columns = [
                "Open_Time",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Close_Time",
                "Quote_Asset_Volume",
                "Number_of_Trades",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
                "Ignore",
                "symbol",
            ]
            df = pd.DataFrame(data=all_data, columns=columns)
            df = df.drop(columns=["Ignore"])
            df["Open_Time"] = pd.to_datetime(df["Open_Time"], unit="ms")
            df["Close_Time"] = pd.to_datetime(df["Close_Time"], unit="ms")
            df["Number_of_Trades"] = df["Number_of_Trades"].astype(int)

            numeric_cols = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Quote_Asset_Volume",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
            ]

            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            df[numeric_cols] = df[numeric_cols].round(8)
            df = df.dropna(subset=numeric_cols)

            logger.info(
                f"Obtidas {len(df)} k-lines históricas para {len(symbols)} símbolos"
            )
            return df
        else:
            logger.error("Falha ao obter k-lines históricas para os tickers USDT")
            return pd.DataFrame()

    def get_historical_klines_generator(
        self, interval: str, timestamp: str
    ) -> pd.DataFrame:
        """Fetch historical klines via the generator API for the top 20 USDT pairs.

        Efficient for large volumes of data.

        Args:
            interval: Candlestick interval (e.g., '1h', '1d').
            timestamp: Start date (e.g., '100 days ago UTC').

        Returns:
            DataFrame with generated klines, or an empty DataFrame on failure.
        """
        df_tickers = self.get_top_20_tickers()
        symbols = df_tickers["symbol"].tolist()
        all_data = []

        if not df_tickers.empty:
            for symbol in symbols:
                data = list(
                    self.client.get_historical_klines_generator(
                        symbol=symbol, interval=interval, start_str=timestamp
                    )
                )
                if isinstance(data, list) and data:
                    for kline in data:
                        all_data.append(kline + [symbol])
                    logger.info(
                        f"K-lines históricas geradas para {symbol} via generator"
                    )
                else:
                    logger.error(f"Falha ao gerar k-lines históricas para {symbol}")

        if all_data:
            columns = [
                "Open_Time",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Close_Time",
                "Quote_Asset_Volume",
                "Number_of_Trades",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
                "Ignore",
                "symbol",
            ]
            df = pd.DataFrame(data=all_data, columns=columns)
            df = df.drop(columns=["Ignore"])
            df["Open_Time"] = pd.to_datetime(df["Open_Time"], unit="ms")
            df["Close_Time"] = pd.to_datetime(df["Close_Time"], unit="ms")
            df["Number_of_Trades"] = df["Number_of_Trades"].astype(int)

            numeric_cols = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "Quote_Asset_Volume",
                "Taker_Buy_Base_Asset_Volume",
                "Taker_Buy_Quote_Asset_Volume",
            ]

            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            df[numeric_cols] = df[numeric_cols].round(8)
            df = df.dropna(subset=numeric_cols)

            logger.info(
                f"Geradas {len(df)} k-lines históricas para {len(symbols)} símbolos via generator"
            )
            return df
        else:
            logger.error("Falha ao gerar k-lines históricas para os tickers USDT")
            return pd.DataFrame()
    def iter_historical_klines(self, interval: str, timestamp: str, batch_size: int = 500):
        """Yield normalized historical candles per symbol and batch."""
        symbols = self.get_top_20_tickers()["symbol"].tolist()
        for symbol in symbols:
            rows: list[list] = []
            try:
                for kline in self.client.get_historical_klines_generator(
                    symbol=symbol, interval=interval, timestamp=timestamp
                ):
                    rows.append(kline + [symbol])
                    if len(rows) == batch_size:
                        yield symbol, self._historical_rows_to_frame(rows)
                        rows = []
                if rows:
                    yield symbol, self._historical_rows_to_frame(rows)
            except Exception:
                logger.exception("Falha ao obter histórico para %s (%s).", symbol, interval)
                raise

    @staticmethod
    def _historical_rows_to_frame(rows: list[list]) -> pd.DataFrame:
        columns = ["Open_Time", "Open", "High", "Low", "Close", "Volume", "Close_Time", "Quote_Asset_Volume", "Number_of_Trades", "Taker_Buy_Base_Asset_Volume", "Taker_Buy_Quote_Asset_Volume", "Ignore", "symbol"]
        df = pd.DataFrame(rows, columns=columns).drop(columns=["Ignore"])
        df["Open_Time"] = pd.to_datetime(df["Open_Time"], unit="ms", utc=True)
        df["Close_Time"] = pd.to_datetime(df["Close_Time"], unit="ms", utc=True)
        numeric_columns = ["Open", "High", "Low", "Close", "Volume", "Quote_Asset_Volume", "Taker_Buy_Base_Asset_Volume", "Taker_Buy_Quote_Asset_Volume"]
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="coerce")
        df["Number_of_Trades"] = pd.to_numeric(df["Number_of_Trades"], errors="coerce").astype("Int64")
        return df.dropna(subset=["Open_Time", "Open", "High", "Low", "Close", "Volume"])