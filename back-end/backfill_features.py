"""In-memory historical feature backfill for the 500 MB free tier.

Streams historical klines from Binance one symbol at a time, computes the
configured indicators in memory and persists ONLY the feature rows. Raw 15m
and 1h candles never touch the database; raw daily candles ARE persisted
because ``klines_1d`` is permanent by design and the close price is the
training target for the ML milestone.

Warm-up handling: fetching starts ``_WARMUP_BARS`` before the requested
window so the earliest requested rows already have every indicator (the
longest window is sma_200; the extra margin lets the EMAs converge). Rows
outside the requested window or still inside the warm-up are discarded
before upload, so no NULL-indicator rows are ever written.

Replaces the old ``historical_charge.py``, which persisted raw candles for
every timeframe (they clashed with the retention windows and inflated the
database with data the ML model never reads).

Usage:
    uv run python backfill_features.py --timeframe 1d
    uv run python backfill_features.py --timeframe 1h --start-days 720
    uv run python backfill_features.py --timeframe 15m --symbols BTCUSDT ETHUSDT
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

from app.feature_engineering.pipelines.klines_pipeline import KlinesPipeline
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository
from app.services.binance_market_data_service import BinanceMarketService
from config import setup_logging

logger = logging.getLogger(__name__)

_WARMUP_BARS = 300  # sma_200 window + margin for the EMAs to converge
_BAR_MINUTES = {"15m": 15, "1h": 60, "1d": 1440}
_FEATURE_TIMEFRAMES = {"15m": "15m", "1h": "1h", "1d": "24h"}
# Horizons chosen to fit the retention windows (180d / 730d / permanent)
# with a safety margin, and the 500 MB storage budget.
_DEFAULT_START_DAYS = {"15m": 175, "1h": 720, "1d": 1825}


def backfill_symbol(
    symbol: str,
    interval: str,
    target_start: datetime,
    market_service: BinanceMarketService,
    klines_repo: KlinesRepository,
    features_repo: FeaturesRepository,
    pipeline: KlinesPipeline,
) -> int:
    """Backfill one symbol: fetch, compute in memory, persist features only.

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT').
        interval: Candlestick interval ('15m', '1h' or '1d').
        target_start: Earliest timestamp the persisted features should cover.
        market_service: Source of historical candles.
        klines_repo: Used to normalize candles (and persist them for '1d').
        features_repo: Destination for the computed feature rows.
        pipeline: Pipeline providing the pure feature computation.

    Returns:
        Number of feature rows persisted.
    """
    fetch_start = target_start - timedelta(minutes=_BAR_MINUTES[interval] * _WARMUP_BARS)
    start_str = fetch_start.strftime("%Y-%m-%d %H:%M:%S UTC")
    batches = [
        batch
        for _, batch in market_service.iter_historical_klines(interval, start_str, symbols=[symbol])
    ]
    if not batches:
        logger.warning("Sem histórico na Binance para %s (%s).", symbol, interval)
        return 0
    raw = pd.concat(batches, ignore_index=True)
    if interval == "1d":
        # klines_1d is permanent: raw daily candles are the ML target and the
        # lookback the daily feature pipeline needs to compute sma_200.
        klines_repo.upsert_klines("1d", raw)
    candles = KlinesRepository.normalize_klines(raw)
    features = pipeline.build_features(candles, _FEATURE_TIMEFRAMES[interval])
    features = features[features["timestamp"] >= target_start]
    features_repo.save_features(_FEATURE_TIMEFRAMES[interval], features)
    return len(features)


def run(
    interval: str,
    start_days: int | None = None,
    symbols: list[str] | None = None,
    market_service: BinanceMarketService | None = None,
    klines_repo: KlinesRepository | None = None,
    features_repo: FeaturesRepository | None = None,
    now: datetime | None = None,
) -> list[str]:
    """Backfill features for every symbol, isolating per-symbol failures.

    Args:
        interval: Candlestick interval ('15m', '1h' or '1d').
        start_days: Days of history to cover; defaults per interval.
        symbols: Symbols to backfill; defaults to the tracked list.
        market_service: Injectable service (tests).
        klines_repo: Injectable repository (tests).
        features_repo: Injectable repository (tests).
        now: Injectable clock (tests).

    Returns:
        List of symbols that failed (empty when everything succeeded).
    """
    if interval not in _DEFAULT_START_DAYS:
        raise ValueError(f"Intervalo não suportado: {interval!r}.")
    market_service = market_service or BinanceMarketService()
    klines_repo = klines_repo or KlinesRepository()
    features_repo = features_repo or FeaturesRepository()
    pipeline = KlinesPipeline(klines_repo, features_repo)
    reference = now or datetime.now(timezone.utc)
    target_start = reference - timedelta(days=start_days or _DEFAULT_START_DAYS[interval])
    symbols = symbols or market_service.get_tracked_symbols()

    failed: list[str] = []
    for position, symbol in enumerate(symbols, start=1):
        try:
            saved = backfill_symbol(
                symbol, interval, target_start, market_service, klines_repo, features_repo, pipeline
            )
            logger.info(
                "[%s/%s] %s (%s): %s features persistidas.",
                position,
                len(symbols),
                symbol,
                interval,
                saved,
            )
        except Exception:
            logger.exception("Backfill falhou para %s (%s).", symbol, interval)
            failed.append(symbol)
    if failed:
        logger.error("Backfill incompleto (%s): %s", interval, ", ".join(failed))
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timeframe", required=True, choices=sorted(_DEFAULT_START_DAYS))
    parser.add_argument(
        "--start-days",
        type=int,
        default=None,
        help="Days of history to cover (defaults: 15m=175, 1h=720, 1d=1825).",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="Explicit symbols (default: the tracked list). Useful to resume.",
    )
    args = parser.parse_args(argv)
    setup_logging()
    try:
        failed = run(args.timeframe, start_days=args.start_days, symbols=args.symbols)
    except Exception:
        logger.exception("Backfill abortado.")
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
