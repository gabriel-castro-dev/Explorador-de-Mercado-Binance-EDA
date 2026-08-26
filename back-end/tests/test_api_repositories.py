"""Offline tests for the API read paths of the repositories."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.timeframe import Timeframe
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository
from app.repositories.symbols_repository import SymbolsRepository
from app.repositories.tickers_repository import TickersRepository


def _chainable(rows):
    """Supabase query-builder fake: every method chains, execute() returns rows."""
    builder = MagicMock()
    for method in ("select", "eq", "gte", "lte", "order", "limit", "range", "upsert"):
        getattr(builder, method).return_value = builder
    builder.execute.return_value.data = rows
    supabase = MagicMock()
    supabase.table.return_value = builder
    return supabase, builder


class QueryKlinesTests(unittest.TestCase):
    def test_targets_table_symbol_and_limit(self):
        supabase, builder = _chainable([{"symbol": "BTCUSDT"}])
        repo = KlinesRepository(supabase=supabase)
        rows = repo.query_klines(Timeframe.H1, symbol="BTCUSDT", limit=5)
        self.assertEqual(rows, [{"symbol": "BTCUSDT"}])
        supabase.table.assert_called_once_with("klines_1h")
        builder.eq.assert_called_once_with("symbol", "BTCUSDT")
        builder.order.assert_called_once_with("open_time", desc=True)
        builder.limit.assert_called_once_with(5)
        builder.gte.assert_not_called()

    def test_period_filters_use_iso_strings(self):
        supabase, builder = _chainable([])
        repo = KlinesRepository(supabase=supabase)
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 2, 1, tzinfo=timezone.utc)
        repo.query_klines(Timeframe.M15, symbol="ETHUSDT", start=start, end=end)
        builder.gte.assert_called_once_with("open_time", start.isoformat())
        builder.lte.assert_called_once_with("open_time", end.isoformat())


class QueryFeaturesTests(unittest.TestCase):
    def test_daily_timeframe_reads_features_24h(self):
        supabase, builder = _chainable([])
        repo = FeaturesRepository(supabase=supabase)
        repo.query_features(Timeframe.D1, symbol="BTCUSDT")
        supabase.table.assert_called_once_with("features_24h")
        builder.order.assert_called_once_with("timestamp", desc=True)


class Latest24hSnapshotsTests(unittest.TestCase):
    def test_single_symbol_limits_to_one(self):
        supabase, builder = _chainable([{"symbol": "BTCUSDT"}])
        repo = TickersRepository(supabase=supabase)
        rows = repo.get_latest_24h_snapshots(symbol="BTCUSDT")
        self.assertEqual(len(rows), 1)
        builder.eq.assert_called_once_with("symbol", "BTCUSDT")
        builder.limit.assert_called_once_with(1)

    def test_dedupes_keeping_newest_row_per_symbol(self):
        rows = [
            {"symbol": "BTCUSDT", "open_time": "2026-01-02 00:00:00"},
            {"symbol": "ETHUSDT", "open_time": "2026-01-02 00:00:00"},
            {"symbol": "BTCUSDT", "open_time": "2026-01-01 00:00:00"},
        ]
        supabase, _ = _chainable(rows)
        repo = TickersRepository(supabase=supabase)
        latest = repo.get_latest_24h_snapshots()
        self.assertEqual(len(latest), 2)
        btc = next(row for row in latest if row["symbol"] == "BTCUSDT")
        self.assertEqual(btc["open_time"], "2026-01-02 00:00:00")


class GetAllFeaturesTests(unittest.TestCase):
    def test_reads_feature_table_paginated(self):
        supabase, builder = _chainable([{"symbol": "BTCUSDT", "timestamp": "2026-01-01"}])
        repo = FeaturesRepository(supabase=supabase)
        frame = repo.get_all_features(Timeframe.D1)
        supabase.table.assert_called_with("features_24h")
        builder.range.assert_called_once_with(0, 999)
        self.assertEqual(len(frame), 1)

    def test_pages_until_short_page(self):
        full_page = [{"symbol": "BTCUSDT", "timestamp": str(i)} for i in range(1000)]
        supabase, builder = _chainable(full_page)
        # Primeira página cheia, segunda curta: o loop precisa parar na segunda.
        first = MagicMock()
        first.data = full_page
        second = MagicMock()
        second.data = full_page[:10]
        builder.execute.side_effect = [first, second]
        repo = FeaturesRepository(supabase=supabase)
        frame = repo.get_all_features(Timeframe.D1)
        self.assertEqual(len(frame), 1010)
        self.assertEqual(builder.range.call_count, 2)


class SymbolsRepositoryTests(unittest.TestCase):
    def test_lists_symbols_alphabetically(self):
        supabase, builder = _chainable([{"symbol": "ADAUSDT"}])
        repo = SymbolsRepository(supabase=supabase)
        self.assertEqual(repo.list_symbols(), [{"symbol": "ADAUSDT"}])
        supabase.table.assert_called_once_with("symbols")
        builder.order.assert_called_once_with("symbol")


if __name__ == "__main__":
    unittest.main()
