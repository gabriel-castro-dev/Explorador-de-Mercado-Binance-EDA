import pandas as pd


class DataResampler:
    """Resample market data into fixed temporal windows."""

    @staticmethod
    def resample_orderbook(df: pd.DataFrame, timeframe: str = "15min") -> pd.DataFrame:
        """Aggregate order book data into time windows (e.g., 15min, 1h).

        Args:
            df: DataFrame with order book data including a 'fetched_at' column.
            timeframe: Target resampling frequency (e.g., '15min').

        Returns:
            DataFrame resampled per symbol and time window.
        """
        if df.empty:
            return df

        # Garante o tipo datetime e ordena
        df["fetched_at"] = pd.to_datetime(df["fetched_at"])
        df = df.sort_values("fetched_at")

        # Reamostra por símbolo e por janela de tempo
        resampled = (
            df.groupby(["symbol", pd.Grouper(key="fetched_at", freq=timeframe)])
            .agg(
                {
                    "bid_price": "last",
                    "bid_qty": "mean",
                    "ask_price": "last",
                    "ask_qty": "mean",
                }
            )
            .reset_index()
        )

        return resampled
