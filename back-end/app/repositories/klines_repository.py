"""Persistence and reads for candlestick tables."""

import logging
from typing import Optional

import pandas as pd
from app.repositories.base import BaseRepository
from app.services.binance_market_data_service import BinanceMarketService

logger = logging.getLogger(__name__)


class KlinesRepository(BaseRepository):
    _BATCH_SIZE = 500
    _COLUMN_MAP = {
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
    _COLUMNS = (
        "symbol",
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
    )
    _NUMERIC_COLUMNS = (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
    )

    def __init__(self) -> None:
        super().__init__()
        self.binance_service = BinanceMarketService()

    def get_latest_klines(self, timeframe: str) -> pd.DataFrame:
        response = (
            self.supabase.table(f"klines_{timeframe}")
            .select("*")
            .order("symbol")
            .order("open_time")
            .execute()
        )
        return pd.DataFrame(response.data)

    def upsert_klines(self, interval: str, df: pd.DataFrame) -> int:
        prepared = self._prepare_klines(df)
        for start in range(0, len(prepared), self._BATCH_SIZE):
            self.supabase.table(f"klines_{interval}").upsert(
                self._to_records(prepared.iloc[start : start + self._BATCH_SIZE]),
                on_conflict="symbol,open_time",
            ).execute()
        logger.info("%s klines persistidos em klines_%s.", len(prepared), interval)
        return len(prepared)

    def save_klines(self, interval: str, start_str: Optional[str] = None):
        df = (
            self.binance_service.get_historical_klines(interval, start_str)
            if start_str
            else self.binance_service.get_klines(interval)
        )
        if df.empty:
            return None
        return {"status": "processed", "total": self.upsert_klines(interval, df)}

    def _prepare_klines(self, df: pd.DataFrame) -> pd.DataFrame:
        prepared = (
            df.rename(columns=self._COLUMN_MAP)
            .drop(columns=["Ignore", "interval"], errors="ignore")
            .copy()
        )
        missing = {
            "symbol",
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        } - set(prepared.columns)
        if missing:
            raise ValueError(
                f"Klines sem colunas obrigatórias: {', '.join(sorted(missing))}."
            )
        for column in ("open_time", "close_time"):
            if column in prepared.columns:
                prepared[column] = pd.to_datetime(
                    prepared[column], errors="coerce", utc=True
                )
        for column in self._NUMERIC_COLUMNS:
            if column in prepared.columns:
                prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
        if "number_of_trades" in prepared.columns:
            prepared["number_of_trades"] = pd.to_numeric(
                prepared["number_of_trades"], errors="coerce"
            ).astype("Int64")
        prepared = prepared.dropna(
            subset=["symbol", "open_time", "open", "high", "low", "close", "volume"]
        )
        return prepared.reindex(
            columns=[column for column in self._COLUMNS if column in prepared.columns]
        )

    @staticmethod
    def _to_records(df: pd.DataFrame) -> list[dict]:
        normalized = df.astype(object).where(pd.notna(df), None)
        records = normalized.to_dict(orient="records")
        for record in records:
            for column, value in record.items():
                if isinstance(value, pd.Timestamp):
                    record[column] = value.isoformat()
        return records
