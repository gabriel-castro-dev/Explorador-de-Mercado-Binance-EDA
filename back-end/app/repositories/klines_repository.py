from typing import Optional

import pandas as pd

from app.repositories.base import BaseRepository
from app.services.binance_market_data_service import BinanceMarketService


class KlinesRepository(BaseRepository):
    """Data access layer for candlestick (klines) tables."""

    def __init__(self):
        """Initialize the repository with a Supabase client and Binance service."""
        super().__init__()
        self.binance_service = BinanceMarketService()

    def get_latest_klines(self, timeframe: str) -> pd.DataFrame:
        """Read persisted candles ordered for rolling indicator calculations.

        Args:
            timeframe: Klines timeframe (e.g., '15m', '1h', '1d').

        Returns:
            DataFrame with candles ordered by symbol and open time.
        """
        response = (
            self.supabase.table(f"klines_{timeframe}")
            .select("*")
            .order("symbol")
            .order("open_time")
            .execute()
        )
        return pd.DataFrame(response.data)

    def save_klines(self, interval: str, start_str: Optional[str] = None):  # noqa: UP045
        """Save klines data to the Supabase table for the given interval.

        If ``start_str`` is provided, historical klines (backfill) are used;
        otherwise real-time klines are fetched. Rows are upserted in batches
        keyed on (symbol, open_time).

        Args:
            interval: Candlestick interval (e.g., '15m', '1h', '1d').
            start_str: Start date for backfill (e.g., '30 days ago UTC').

        Returns:
            Dict with processing status and total rows, or None if nothing
            was saved.
        """
        if start_str:
            df = self.binance_service.get_historical_klines(interval, start_str)
        else:
            df = self.binance_service.get_klines(interval)
        if df.empty:
            return
        else:
            df_prep = df.copy()
            df_prep = df_prep.rename(
                columns={
                    "symbol": "symbol",
                    "Open_Time": "open_time",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                    "Close_Time": "close_time",
                    "Quote_Asset_Volume": "quote_asset_volume",
                    "Number_of_Trades": "number_of_trades",
                    "Taker_Buy_Base_Asset_Volume": "taker_buy_base_asset_volume",
                    "Taker_Buy_Quote_Asset_Volume": "taker_buy_quote_asset_volume",
                }
            )
            if "interval" in df_prep.columns:
                df_prep = df_prep.drop(columns=["interval"])
            if "open_time" in df_prep.columns:
                df_prep["open_time"] = df_prep["open_time"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if "close_time" in df_prep.columns:
                df_prep["close_time"] = df_prep["close_time"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            dados_para_salvar = df_prep.to_dict(orient="records")
            batch_size = 200
            total = len(dados_para_salvar)
            for i in range(0, total, batch_size):
                batch = dados_para_salvar[i : i + batch_size]
                try:
                    self.supabase.table(f"klines_{interval}").upsert(
                        batch, on_conflict="symbol,open_time"
                    ).execute()
                    print(
                        f"Lote {i // batch_size + 1}/{(total - 1) // batch_size + 1}: "
                        f"{len(batch)} registros de klines salvos/atualizados no Supabase."
                    )
                except Exception as e:  # noqa: BLE001
                    print(f"Erro ao salvar lote de klines no Supabase: {e}")
            print(f"Total: {total} registros de klines processados.")
            return {"status": "processed", "total": total}