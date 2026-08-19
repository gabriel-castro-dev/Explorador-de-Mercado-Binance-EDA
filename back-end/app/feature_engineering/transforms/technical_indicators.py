import pandas as pd
import talib


class TechnicalIndicatorsTransform:
    """Stateless technical indicator calculations for feature engineering."""

    @staticmethod
    def _by_symbol(df: pd.DataFrame, column: str, calculation: object) -> pd.Series:
        """Apply a one-dimensional calculation independently per symbol."""
        if "symbol" not in df.columns:
            raise ValueError("Indicadores de candle requerem a coluna 'symbol'.")
        return df.groupby("symbol", sort=False)[column].transform(calculation)

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        return TechnicalIndicatorsTransform._by_symbol(
            df, column, lambda values: values.rolling(window=period).mean()
        )

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
        return TechnicalIndicatorsTransform._by_symbol(
            df, column, lambda values: values.ewm(span=period, adjust=False).mean()
        )

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        return TechnicalIndicatorsTransform._by_symbol(
            df,
            column,
            lambda values: pd.Series(
                talib.RSI(values.to_numpy(dtype=float), timeperiod=period), index=values.index
            ),
        )

    @staticmethod
    def calculate_macd_signal(macd_line: pd.Series) -> pd.Series:
        return macd_line.ewm(span=9, adjust=False).mean()

    @staticmethod
    def calculate_avg_price_deviation(
        df: pd.DataFrame, period: int = 20, column: str = "close"
    ) -> pd.Series:
        sma = TechnicalIndicatorsTransform.calculate_sma(df, period, column)
        return (df[column] - sma) / sma

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame, period: int = 20, num_std: int = 2, column: str = "close"
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        middle_band = TechnicalIndicatorsTransform.calculate_sma(df, period, column)
        rolling_std = TechnicalIndicatorsTransform._by_symbol(
            df, column, lambda values: values.rolling(window=period).std()
        )
        return (
            middle_band + (rolling_std * num_std),
            middle_band,
            middle_band - (rolling_std * num_std),
        )

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        if "symbol" not in df.columns:
            raise ValueError("Indicadores de candle requerem a coluna 'symbol'.")
        result = pd.Series(float("nan"), index=df.index, dtype=float)
        for positions in df.groupby("symbol", sort=False).indices.values():
            candles = df.iloc[positions]
            result.iloc[positions] = talib.ATR(
                candles["high"].to_numpy(dtype=float),
                candles["low"].to_numpy(dtype=float),
                candles["close"].to_numpy(dtype=float),
                timeperiod=period,
            )
        return result

    @staticmethod
    def calculate_bid_ask_spread(df: pd.DataFrame) -> pd.Series:
        return df["ask_price"] - df["bid_price"]

    @staticmethod
    def calculate_order_imbalance(df: pd.DataFrame) -> pd.Series:
        total_qty = df["bid_qty"] + df["ask_qty"]
        return (df["bid_qty"] - df["ask_qty"]) / total_qty.replace(0, pd.NA)

    @staticmethod
    def calculate_change_percent(
        df: pd.DataFrame, column: str = "close", period: int = 1
    ) -> pd.Series:
        return df.groupby("symbol")[column].pct_change(periods=period) * 100
