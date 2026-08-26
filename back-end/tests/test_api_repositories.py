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
    def test_single_symbol_reads_the_latest_view(self):
        supabase, builder = _chainable([{"symbol": "BTCUSDT"}])
        repo = TickersRepository(supabase=supabase)
        rows = repo.get_latest_24h_snapshots(symbol="BTCUSDT")
        self.assertEqual(rows, [{"symbol": "BTCUSDT"}])
        supabase.table.assert_called_once_with("ticker_24hr_latest")
        builder.eq.assert_called_once_with("symbol", "BTCUSDT")

    def test_every_symbol_of_a_large_batch_is_returned(self):
        # Regressão: o job grava ~480–735 símbolos por lote; o símbolo mais
        # antigo do lote (fora das 200 linhas mais novas) precisa vir na resposta.
        rows = [{"symbol": f"S{i:03d}USDT", "open_time": "2026-01-02 00:00:00"} for i in range(735)]
        rows[0]["symbol"] = "BTCUSDT"
        rows.reverse()  # BTCUSDT é a última das 735 linhas
        supabase, builder = _chainable(rows)
        repo = TickersRepository(supabase=supabase)
        latest = repo.get_latest_24h_snapshots()
        self.assertEqual(len(latest), 735)
        self.assertIn("BTCUSDT", {row["symbol"] for row in latest})
        supabase.table.assert_called_once_with("ticker_24hr_latest")
        builder.limit.assert_not_called()
        builder.order.assert_called_once_with("symbol")

    def test_tracked_filter_is_pushed_to_the_view(self):
        supabase, builder = _chainable([])
        repo = TickersRepository(supabase=supabase)
        repo.get_latest_24h_snapshots(tracked=True)
        builder.eq.assert_called_once_with("tracked", True)

    def test_no_filter_by_default(self):
        supabase, builder = _chainable([])
        TickersRepository(supabase=supabase).get_latest_24h_snapshots()
        builder.eq.assert_not_called()


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
    def test_lists_symbols_alphabetically_with_tracking_flag(self):
        rows = [
            {"symbol": "ACEUSDT", "created_at": None, "tracked": True},
            {"symbol": "ADAUSDT", "created_at": None, "tracked": False},
        ]
        supabase, builder = _chainable(rows)
        repo = SymbolsRepository(supabase=supabase)
        self.assertEqual(repo.list_symbols(), rows)
        supabase.table.assert_called_once_with("symbols_with_tracking")
        builder.order.assert_called_once_with("symbol")
        builder.eq.assert_not_called()

    def test_tracked_filter_is_pushed_to_the_view(self):
        supabase, builder = _chainable([])
        SymbolsRepository(supabase=supabase).list_symbols(tracked=True)
        builder.eq.assert_called_once_with("tracked", True)

    def test_ensure_symbols_still_writes_to_the_base_table(self):
        supabase, builder = _chainable([])
        SymbolsRepository(supabase=supabase).ensure_symbols(["BTCUSDT"])
        supabase.table.assert_called_once_with("symbols")
        builder.upsert.assert_called_once()


if __name__ == "__main__":
    unittest.main()
