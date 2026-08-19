"""API response schemas mirroring the Supabase table columns."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class _Row(BaseModel):
    # extra="ignore": ids surrogate do banco / colunas futuras nunca quebram a resposta
    model_config = ConfigDict(extra="ignore")


class KlineOut(_Row):
    """One candlestick row from klines_{15m,1h,1d}."""

    symbol: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: Optional[datetime] = None
    quote_asset_volume: Optional[float] = None
    number_of_trades: Optional[int] = None
    taker_buy_base_asset_volume: Optional[float] = None
    taker_buy_quote_asset_volume: Optional[float] = None


class FeatureRowOut(_Row):
    """One indicator row from features_{15m,1h,24h}.

    Field names mirror the output columns produced by
    app/feature_engineering/config/features.yml (macd, macd_histogram
    and bb_width are Postgres GENERATED columns). Indicators are
    nullable: warm-up windows legitimately produce NULLs.
    """

    symbol: str
    timestamp: datetime
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    avg_price_deviation_sma20: Optional[float] = None
    avg_price_deviation_sma50: Optional[float] = None
    avg_price_deviation_sma200: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    atr_14: Optional[float] = None
    bid_ask_spread: Optional[float] = None
    order_imbalance: Optional[float] = None
    price_change_percent: Optional[float] = None
    volume_change_24h: Optional[float] = None
    volume_sma_20: Optional[float] = None


class Ticker24hOut(_Row):
    """Latest 24-hour market snapshot from ticker_24hr_history."""

    symbol: str
    open_time: datetime
    close_time: Optional[datetime] = None
    last_price: Optional[float] = None
    price_change: Optional[float] = None
    price_change_percent: Optional[float] = None
    weighted_avg_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    volume: Optional[float] = None
    quote_volume: Optional[float] = None
    count: Optional[int] = None


class SymbolOut(_Row):
    """One tracked symbol from the symbols reference table."""

    symbol: str
    created_at: Optional[datetime] = None


class HealthOut(BaseModel):
    """Service liveness response."""

    status: str
    version: str
