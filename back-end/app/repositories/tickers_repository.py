import pandas as pd
from app.repositories.base import BaseRepository
from app.services.binance_market_data_service import BinanceMarketService


class TickersRepository(BaseRepository):
    """Data access layer for liquidity and 24-hour summary tables."""

    def __init__(self):
        """Initialize the repository with a Binance market data service."""
        super().__init__()
        self.binance_service = BinanceMarketService()

    def get_latest_orderbook_tickers(self) -> pd.DataFrame:
        """Read retained order-book snapshots in chronological order."""
        response = (
            self.supabase.table("orderbook_tickers")
            .select("*")
            .order("symbol")
            .order("fetched_at")
            .execute()
        )
        return pd.DataFrame(response.data)

    def get_latest_ticker_24hr(self) -> pd.DataFrame:
        """Read retained 24-hour ticker snapshots in chronological order."""
        response = (
            self.supabase.table("ticker_24hr_history")
            .select("*")
            .order("symbol")
            .order("open_time")
            .execute()
        )
        return pd.DataFrame(response.data)
    def save_ticker_24hr(self):
        """Save 24-hour ticker data to Supabase.

        Fetches the 24-hour summaries from Binance, normalizes the column
        names and timestamps, and upserts them keyed on (symbol, open_time).

        Returns:
            Dict with the Supabase upsert response, or None on failure.
        """
        df = self.binance_service.get_ticker_24hr()
        if df.empty:
            return
        else:
            df_prep = df.copy()
            df_prep = df_prep.rename(
                columns={
                    "symbol": "symbol",
                    "priceChange": "price_change",
                    "priceChangePercent": "price_change_percent",
                    "weightedAvgPrice": "weighted_avg_price",
                    "prevClosePrice": "prev_close_price",
                    "lastPrice": "last_price",
                    "lastQty": "last_qty",
                    "bidPrice": "bid_price",
                    "bidQty": "bid_qty",
                    "askPrice": "ask_price",
                    "askQty": "ask_qty",
                    "openPrice": "open_price",
                    "highPrice": "high_price",
                    "lowPrice": "low_price",
                    "volume": "volume",
                    "quoteVolume": "quote_volume",
                    "openTime": "open_time",
                    "closeTime": "close_time",
                    "firstId": "first_id",
                    "lastId": "last_id",
                    "count": "count",
                }
            )

            if "open_time" in df_prep.columns:
                df_prep["open_time"] = df_prep["open_time"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            if "close_time" in df_prep.columns:
                df_prep["close_time"] = df_prep["close_time"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            dados_para_salvar = df_prep.to_dict(orient="records")
            try:
                response = (
                    self.supabase.table("ticker_24hr_history")
                    .upsert(dados_para_salvar, on_conflict="symbol,open_time")
                    .execute()
                )
                print(
                    f"Sucesso! {len(dados_para_salvar)} registros de tickers salvos/atualizados no Supabase."
                )
                return response

            except Exception as e:  # noqa: BLE001
                print(f"Erro ao salvar os tickers de 24h no Supabase: {e}")
                return None

    def save_orderbook_tickers(self):
        """Save order book ticker data to Supabase.

        Fetches the order book snapshot for the top 20 pairs, normalizes the
        column names, stamps the fetch time, and upserts them keyed on
        (symbol, fetched_at).

        Returns:
            Dict with the Supabase upsert response, or None on failure.
        """
        df = self.binance_service.get_orderbook_tickers()
        if df.empty:
            return
        else:
            df_prep = df.copy()
            df_prep = df_prep.rename(
                columns={
                    "symbol": "symbol",
                    "bidPrice": "bid_price",
                    "bidQty": "bid_qty",
                    "askPrice": "ask_price",
                    "askQty": "ask_qty",
                }
            )
            df_prep["fetched_at"] = pd.Timestamp.now(tz="UTC").strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            dados_para_salvar = df_prep.to_dict(orient="records")
            try:
                response = (
                    self.supabase.table("orderbook_tickers")
                    .upsert(dados_para_salvar, on_conflict="symbol,fetched_at")
                    .execute()
                )
                print(
                    f"Sucesso! {len(dados_para_salvar)} registros de orderbook salvos/atualizados no Supabase."
                )
                return response
            except Exception as e:  # noqa: BLE001
                print(f"Erro ao salvar os orderbook no Supabase: {e}")
                return None