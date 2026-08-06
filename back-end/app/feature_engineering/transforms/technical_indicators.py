import pandas as pd
import talib


class TechnicalIndicatorsTransform:
    """Stateless technical indicator calculations for feature engineering.

    Pure functions that receive DataFrames and return computed Series or
    tuples of Series, without producing side effects or making persistence
    calls.
    """

    @staticmethod
    def calculate_sma(
        df: pd.DataFrame, period: int, column: str = "close"
    ) -> pd.Series:
        """Calculate the Simple Moving Average (SMA).

        Args:
            df: DataFrame containing the price column.
            period: Rolling window size.
            column: Column to compute the average over.

        Returns:
            Series with the SMA values.
        """
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(
        df: pd.DataFrame, period: int, column: str = "close"
    ) -> pd.Series:
        """Calculate the Exponential Moving Average (EMA).

        Args:
            df: DataFrame containing the price column.
            period: EMA span.
            column: Column to compute the average over.

        Returns:
            Series with the EMA values.
        """
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame, period: int = 14, column: str = "close"
    ) -> pd.Series:
        """Calculate the Relative Strength Index (RSI).

        Args:
            df: DataFrame containing the price column.
            period: RSI lookback period.
            column: Column to compute the indicator over.

        Returns:
            Series with the RSI values.
        """
        return talib.RSI(df[column], timeperiod=period)

    @staticmethod
    def calculate_macd_signal(macd_line: pd.Series) -> pd.Series:
        """Calculate the MACD signal line (EMA 9 of the MACD line).

        Args:
            macd_line: Series with the MACD line values.

        Returns:
            Series with the MACD signal values.
        """
        return macd_line.ewm(span=9, adjust=False).mean()

    @staticmethod
    def calculate_avg_price_deviation(
        df: pd.DataFrame, period: int = 20, column: str = "close"
    ) -> pd.Series:
        """Calculate the relative price deviation from the SMA, as a percentage.

        Args:
            df: DataFrame containing the price column.
            period: Rolling window size for the SMA.
            column: Column used as the price reference.

        Returns:
            Series with the relative deviation values.
        """
        sma = df[column].rolling(window=period).mean()
        return (df[column] - sma) / sma

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        num_std: int = 2,
        column: str = "close",
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate the Upper, Middle, and Lower Bollinger Bands.

        Args:
            df: DataFrame containing the price column.
            period: Rolling window size.
            num_std: Number of standard deviations from the middle band.
            column: Column used as the price reference.

        Returns:
            Tuple with the upper, middle, and lower band Series.
        """
        middle_band = df[column].rolling(window=period).mean()
        rolling_std = df[column].rolling(window=period).std()

        upper_band = middle_band + (rolling_std * num_std)
        lower_band = middle_band - (rolling_std * num_std)

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate the Average True Range (ATR).

        Args:
            df: DataFrame with 'high', 'low', and 'close' columns.
            period: ATR lookback period.

        Returns:
            Series with the ATR values.
        """
        return talib.ATR(df["high"], df["low"], df["close"], timeperiod=period)

    @staticmethod
    def calculate_bid_ask_spread(df: pd.DataFrame) -> pd.Series:
        """Calculate the bid-ask spread.

        Args:
            df: DataFrame with 'bid_price' and 'ask_price' columns.

        Returns:
            Series with the bid-ask spread values.
        """
        return df["ask_price"] - df["bid_price"]

    @staticmethod
    def calculate_order_imbalance(df: pd.DataFrame) -> pd.Series:
        """Calculate the order imbalance, guarding against division by zero.

        Args:
            df: DataFrame with 'bid_qty' and 'ask_qty' columns.

        Returns:
            Series with the order imbalance values.
        """
        total_qty = df["bid_qty"] + df["ask_qty"]
        return (df["bid_qty"] - df["ask_qty"]) / total_qty.replace(0, pd.NA)

    @staticmethod
    def calculate_change_percent(
        df: pd.DataFrame, column: str = "close", period: int = 1
    ) -> pd.Series:
        """Calculate the percentage change of a column grouped by symbol.

        Args:
            df: DataFrame containing the data and a 'symbol' column.
            column: Column to compute the change for ('close', 'volume', etc.).
            period: Number of periods to look back (e.g., 1 for candle to
                candle, 24 for 24h in 1h candles).

        Returns:
            Series with the calculated percentage change.
        """
        return df.groupby("symbol")[column].pct_change(periods=period) * 100
