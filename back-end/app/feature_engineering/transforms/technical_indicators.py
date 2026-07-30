import pandas as pd
import talib


class TechnicalIndicatorsTransform:
    """Base class for technical indicator calculations."""

    @staticmethod
    def calculate_sma(
        df: pd.DataFrame, period: int, column: str = "close"
    ) -> pd.Series:
        """Calculate Simple Moving Average (SMA)."""
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(
        df: pd.DataFrame, period: int, column: str = "close"
    ) -> pd.Series:
        """Calculate Exponential Moving Average (EMA)."""
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame, period: int = 14, column: str = "close"
    ) -> pd.Series:
        """Calculate Relative Strength Index (RSI)."""
        return talib.RSI(df[column], timeperiod=period)

    @staticmethod
    def calculate_macd_signal(macd_line: pd.Series) -> pd.Series:
        """Calculate MACD signal line (EMA 9 of MACD line)."""
        return macd_line.ewm(span=9, adjust=False).mean()

    @staticmethod
    def calculate_avg_price_deviation(
        df: pd.DataFrame, period: int = 20, column: str = "close"
    ) -> pd.Series:
        """Calculate relative price deviation from SMA (Percentage)."""
        sma = df[column].rolling(window=period).mean()
        return (df[column] - sma) / sma

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        num_std: int = 2,
        column: str = "close",
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Upper, Middle, and Lower Bollinger Bands."""
        middle_band = df[column].rolling(window=period).mean()
        rolling_std = df[column].rolling(window=period).std()

        upper_band = middle_band + (rolling_std * num_std)
        lower_band = middle_band - (rolling_std * num_std)

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (ATR)."""
        return talib.ATR(df["high"], df["low"], df["close"], timeperiod=period)

    @staticmethod
    def calculate_bid_ask_spread(df: pd.DataFrame) -> pd.Series:
        """Calculate the bid-ask spread."""
        return df["ask_price"] - df["bid_price"]

    @staticmethod
    def calculate_order_imbalance(df: pd.DataFrame) -> pd.Series:
        """Calculate order imbalance safely against division by zero."""
        total_qty = df["bid_qty"] + df["ask_qty"]
        return (df["bid_qty"] - df["ask_qty"]) / total_qty.replace(0, pd.NA)

    @staticmethod
    def calculate_price_change_percent(df: pd.DataFrame, period: int = 1) -> pd.Series:
        """Calculate price change percentage per symbol."""
        return df.groupby("symbol")["close"].pct_change(periods=period) * 100

    @staticmethod
    def calculate_volume_change_percent(
        df: pd.DataFrame, period: int = 24
    ) -> pd.Series:
        """Calculate volume change percentage per symbol."""
        return df.groupby("symbol")["volume"].pct_change(periods=period) * 100
