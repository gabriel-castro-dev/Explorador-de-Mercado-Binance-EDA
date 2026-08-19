import json
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import historical_charge
from config import get_settings
from app.feature_engineering.pipelines.klines_pipeline import KlinesPipeline
from app.feature_engineering.transforms.technical_indicators import (
    TechnicalIndicatorsTransform,
)
from app.repositories.features_repository import FeaturesRepository
from app.services.binance_market_data_service import BinanceMarketService


class TechnicalIndicatorsTests(unittest.TestCase):
    def test_candle_indicators_do_not_cross_symbol_boundaries(self):
        df = pd.DataFrame(
            {
                "symbol": ["A", "A", "A", "B"],
                "close": [1.0, 2.0, 3.0, 100.0],
                "high": [2.0, 3.0, 4.0, 101.0],
                "low": [0.0, 1.0, 2.0, 99.0],
            }
        )
        sma = TechnicalIndicatorsTransform.calculate_sma(df, 2)
        ema = TechnicalIndicatorsTransform.calculate_ema(df, 2)
        rsi = TechnicalIndicatorsTransform.calculate_rsi(df, 2)
        atr = TechnicalIndicatorsTransform.calculate_atr(df, 2)
        deviation = TechnicalIndicatorsTransform.calculate_avg_price_deviation(df, 2)
        upper, middle, lower = TechnicalIndicatorsTransform.calculate_bollinger_bands(
            df, 2
        )

        self.assertTrue(pd.isna(sma.iloc[3]))
        self.assertEqual(ema.iloc[3], 100.0)
        self.assertTrue(pd.isna(rsi.iloc[3]))
        self.assertTrue(pd.isna(atr.iloc[3]))
        self.assertTrue(pd.isna(deviation.iloc[3]))
        self.assertTrue(pd.isna(upper.iloc[3]))
        self.assertTrue(pd.isna(middle.iloc[3]))
        self.assertTrue(pd.isna(lower.iloc[3]))


class KlinesPipelineTests(unittest.TestCase):
    def test_macd_signal_is_calculated_per_symbol_and_is_persisted(self):
        candles = pd.DataFrame(
            {
                "symbol": ["A"] * 3 + ["B"] * 3,
                "open_time": pd.date_range("2026-01-01", periods=6, freq="h", tz="UTC"),
                "open": [1.0] * 6,
                "high": [2.0] * 6,
                "low": [0.5] * 6,
                "close": [1.0, 2.0, 3.0, 100.0, 101.0, 102.0],
                "volume": [1.0] * 6,
            }
        )
        klines_repo = MagicMock()
        klines_repo.get_latest_klines.return_value = candles
        features_repo = MagicMock()
        KlinesPipeline(klines_repo, features_repo).run("15m")
        saved = features_repo.save_features.call_args.args[1]
        self.assertTrue(saved["macd_signal"].notna().all())
        self.assertNotIn("macd", saved.columns)
        self.assertNotIn("macd_histogram", saved.columns)
        expected = (
            (saved["ema_12"] - saved["ema_26"])
            .groupby(saved["symbol"], sort=False)
            .transform(lambda values: values.ewm(span=9, adjust=False).mean())
        )
        pd.testing.assert_series_equal(
            saved["macd_signal"], expected, check_names=False
        )


class FeaturesRepositoryTests(unittest.TestCase):
    def test_serialization_replaces_nan_and_infinities(self):
        records = FeaturesRepository._to_records(
            pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2026-01-01", tz="UTC")] * 3,
                    "value": [np.nan, np.inf, -np.inf],
                }
            )
        )
        self.assertEqual([record["value"] for record in records], [None, None, None])
        json.dumps(records, allow_nan=False)

    def test_upsert_is_split_into_500_row_batches(self):
        builder = MagicMock()
        builder.upsert.return_value = builder
        supabase = MagicMock()
        supabase.table.return_value = builder
        repository = FeaturesRepository(supabase=supabase)
        df = pd.DataFrame(
            {
                "symbol": ["BTCUSDT"] * 1001,
                "timestamp": pd.date_range(
                    "2026-01-01", periods=1001, freq="min", tz="UTC"
                ),
                "macd": [1.0] * 1001,
                "bb_width": [1.0] * 1001,
            }
        )
        repository.save_features("15m", df)
        self.assertEqual(builder.upsert.call_count, 3)
        self.assertEqual(
            [len(call.args[0]) for call in builder.upsert.call_args_list], [500, 500, 1]
        )
        self.assertTrue(
            all(
                call.kwargs["on_conflict"] == "symbol,timestamp"
                for call in builder.upsert.call_args_list
            )
        )
        self.assertTrue(
            all(
                "macd" not in call.args[0][0] and "bb_width" not in call.args[0][0]
                for call in builder.upsert.call_args_list
            )
        )


class HistoricalChargeTests(unittest.TestCase):
    def test_historical_charge_streams_batches_then_runs_features(self):
        batch = pd.DataFrame(
            {
                "symbol": ["BTCUSDT"],
                "Open_Time": [pd.Timestamp("2026-01-01", tz="UTC")],
                "Open": [1.0],
                "High": [2.0],
                "Low": [0.5],
                "Close": [1.5],
                "Volume": [3.0],
            }
        )
        service = MagicMock()
        service.iter_historical_klines.side_effect = lambda interval, start: iter(
            [("BTCUSDT", batch)]
        )
        klines_repo = MagicMock()
        features_repo = MagicMock()
        with patch.object(historical_charge, "KlinesPipeline") as pipeline_class:
            historical_charge.run(
                service,
                klines_repo,
                features_repo,
                datetime(2026, 8, 9, tzinfo=timezone.utc),
            )
        self.assertEqual(klines_repo.upsert_klines.call_count, 3)
        self.assertEqual(
            pipeline_class.return_value.run.call_args_list[0].args, ("15m",)
        )
        self.assertEqual(
            pipeline_class.return_value.run.call_args_list[1].args, ("1h",)
        )
        self.assertEqual(
            pipeline_class.return_value.run.call_args_list[2].args, ("24h",)
        )


class HistoricalServiceTests(unittest.TestCase):
    def test_historical_batch_keeps_datetime_values(self):
        row = [
            1704067200000,
            "1",
            "2",
            "0.5",
            "1.5",
            "3",
            1704068100000,
            "4",
            5,
            "1",
            "2",
            "0",
            "BTCUSDT",
        ]
        df = BinanceMarketService._historical_rows_to_frame([row])
        self.assertTrue(isinstance(df["Open_Time"].dtype, pd.DatetimeTZDtype))
        self.assertEqual(df.iloc[0]["symbol"], "BTCUSDT")


class SettingsTests(unittest.TestCase):
    _ENV = {
        "SUPABASE_URL": "http://localhost",
        "SUPABASE_KEY": "test-key",
        "BINANCE_API_KEY": "test-key",
        "BINANCE_API_SECRET": "test-secret",
    }

    def setUp(self):
        get_settings.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()

    def test_get_settings_is_cached(self):
        with patch.dict(os.environ, self._ENV):
            first = get_settings()
            second = get_settings()
        self.assertIs(first, second)
        self.assertEqual(first.SUPABASE_KEY, "test-key")


if __name__ == "__main__":
    unittest.main()


class JobsTests(unittest.TestCase):
    def _run(self, argv):
        import jobs

        with (
            patch.object(sys, "argv", argv),
            patch.object(jobs, "setup_logging"),
            patch.object(jobs, "BinanceMarketService") as service_cls,
            patch.object(jobs, "KlinesRepository") as klines_cls,
            patch.object(jobs, "TickersRepository") as tickers_cls,
            patch.object(jobs, "ingest_klines") as ingest_klines,
            patch.object(jobs, "ingest_ticker_24hr") as ingest_ticker,
            patch.object(jobs, "ingest_orderbook_tickers") as ingest_orderbook,
        ):
            code = jobs.main()
        return code, {
            "service_cls": service_cls,
            "klines_cls": klines_cls,
            "tickers_cls": tickers_cls,
            "ingest_klines": ingest_klines,
            "ingest_ticker": ingest_ticker,
            "ingest_orderbook": ingest_orderbook,
        }

    def test_daily_dispatches_all_intervals_in_order(self):
        code, mocks = self._run(["jobs.py", "daily"])
        self.assertEqual(code, 0)
        intervals = [call.args[2] for call in mocks["ingest_klines"].call_args_list]
        self.assertEqual(intervals, ["15m", "1h", "1d"])
        mocks["ingest_ticker"].assert_not_called()
        mocks["ingest_orderbook"].assert_not_called()

    def test_failure_returns_exit_code_1(self):
        import jobs

        with (
            patch.object(sys, "argv", ["jobs.py", "five-minutes"]),
            patch.object(jobs, "setup_logging"),
            patch.object(jobs, "BinanceMarketService"),
            patch.object(jobs, "TickersRepository"),
            patch.object(
                jobs, "ingest_orderbook_tickers", side_effect=RuntimeError("boom")
            ),
        ):
            self.assertEqual(jobs.main(), 1)

    def test_unknown_job_returns_exit_code_2_without_connecting(self):
        code, mocks = self._run(["jobs.py", "bogus"])
        self.assertEqual(code, 2)
        mocks["service_cls"].assert_not_called()


class TickersIngestionTests(unittest.TestCase):
    def test_ticker_24hr_rows_are_normalized_and_persisted(self):
        from app.ingestion.tickers import ingest_ticker_24hr

        service = MagicMock()
        service.get_ticker_24hr.return_value = pd.DataFrame(
            {
                "symbol": ["BTCUSDT"],
                "priceChange": [1.0],
                "openTime": [pd.Timestamp("2026-01-01 10:20:30")],
                "closeTime": [pd.Timestamp("2026-01-02 10:20:30")],
            }
        )
        repo = MagicMock()
        repo.upsert_ticker_24hr.return_value = 1
        self.assertEqual(ingest_ticker_24hr(service, repo), 1)
        persisted = repo.upsert_ticker_24hr.call_args.args[0]
        self.assertIn("price_change", persisted.columns)
        self.assertEqual(persisted["open_time"].iloc[0], "2026-01-01 10:20:30")
        self.assertEqual(persisted["close_time"].iloc[0], "2026-01-02 10:20:30")

    def test_orderbook_rows_are_normalized_and_stamped(self):
        from app.ingestion.tickers import ingest_orderbook_tickers

        service = MagicMock()
        service.get_orderbook_tickers.return_value = pd.DataFrame(
            {"symbol": ["BTCUSDT"], "bidPrice": [1.0], "askPrice": [2.0]}
        )
        repo = MagicMock()
        repo.upsert_orderbook_tickers.return_value = 1
        self.assertEqual(ingest_orderbook_tickers(service, repo), 1)
        persisted = repo.upsert_orderbook_tickers.call_args.args[0]
        self.assertIn("bid_price", persisted.columns)
        import re

        self.assertRegex(
            persisted["fetched_at"].iloc[0], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
        )

    def test_repository_errors_propagate(self):
        from app.ingestion.tickers import ingest_orderbook_tickers

        service = MagicMock()
        service.get_orderbook_tickers.return_value = pd.DataFrame(
            {"symbol": ["BTCUSDT"], "bidPrice": [1.0]}
        )
        repo = MagicMock()
        repo.upsert_orderbook_tickers.side_effect = RuntimeError("db down")
        with self.assertRaises(RuntimeError):
            ingest_orderbook_tickers(service, repo)


class TickersRepositoryTests(unittest.TestCase):
    def _repo(self):
        from app.repositories.tickers_repository import TickersRepository

        builder = MagicMock()
        builder.upsert.return_value = builder
        supabase = MagicMock()
        supabase.table.return_value = builder
        return TickersRepository(supabase=supabase), supabase, builder

    def test_upsert_ticker_24hr_uses_conflict_key(self):
        repo, supabase, builder = self._repo()
        count = repo.upsert_ticker_24hr(
            pd.DataFrame({"symbol": ["BTCUSDT"], "open_time": ["2026-01-01 00:00:00"]})
        )
        self.assertEqual(count, 1)
        supabase.table.assert_called_once_with("ticker_24hr_history")
        self.assertEqual(
            builder.upsert.call_args.kwargs["on_conflict"], "symbol,open_time"
        )

    def test_upsert_orderbook_uses_conflict_key_and_propagates_errors(self):
        repo, supabase, builder = self._repo()
        repo.upsert_orderbook_tickers(
            pd.DataFrame({"symbol": ["BTCUSDT"], "fetched_at": ["2026-01-01 00:00:00"]})
        )
        supabase.table.assert_called_once_with("orderbook_tickers")
        self.assertEqual(
            builder.upsert.call_args.kwargs["on_conflict"], "symbol,fetched_at"
        )
        builder.execute.side_effect = RuntimeError("db down")
        with self.assertRaises(RuntimeError):
            repo.upsert_orderbook_tickers(pd.DataFrame({"symbol": ["X"]}))


class KlinesRepositoryTests(unittest.TestCase):
    def test_upsert_klines_batches_and_uses_conflict_key(self):
        from app.repositories.klines_repository import KlinesRepository

        builder = MagicMock()
        builder.upsert.return_value = builder
        supabase = MagicMock()
        supabase.table.return_value = builder
        repo = KlinesRepository(supabase=supabase)
        rows = 501
        df = pd.DataFrame(
            {
                "symbol": ["BTCUSDT"] * rows,
                "Open_Time": pd.date_range("2026-01-01", periods=rows, freq="min"),
                "Open": [1.0] * rows,
                "High": [2.0] * rows,
                "Low": [0.5] * rows,
                "Close": [1.5] * rows,
                "Volume": [10.0] * rows,
            }
        )
        self.assertEqual(repo.upsert_klines("15m", df), rows)
        supabase.table.assert_called_with("klines_15m")
        self.assertEqual(builder.upsert.call_count, 2)
        self.assertEqual(
            builder.upsert.call_args.kwargs["on_conflict"], "symbol,open_time"
        )


class RetryHelperTests(unittest.TestCase):
    def test_returns_value_after_transient_failures_and_sleeps(self):
        from app.clients.binance_client import call_with_retry

        fn = MagicMock(side_effect=[RuntimeError("net"), RuntimeError("net"), [1]])
        sleep = MagicMock()
        result = call_with_retry(
            fn, retries=3, delay=5, context="teste", empty=[], sleep=sleep
        )
        self.assertEqual(result, [1])
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(5)

    def test_permission_error_raises_immediately(self):
        from app.clients.binance_client import (
            BinanceUnauthorizedError,
            call_with_retry,
        )

        fn = MagicMock(side_effect=RuntimeError("APIError(code=-2015): denied"))
        with self.assertRaises(BinanceUnauthorizedError) as ctx:
            call_with_retry(
                fn, retries=3, delay=0, context="teste", sleep=MagicMock()
            )
        self.assertIsInstance(ctx.exception, PermissionError)
        self.assertEqual(fn.call_count, 1)

    def test_invalid_symbol_raises_typed_key_error(self):
        from app.clients.binance_client import (
            BinanceInvalidSymbolError,
            call_with_retry,
        )

        fn = MagicMock(side_effect=RuntimeError("APIError(code=-1121): bad symbol"))
        with self.assertRaises(BinanceInvalidSymbolError) as ctx:
            call_with_retry(
                fn, retries=3, delay=0, context="teste", sleep=MagicMock()
            )
        self.assertIsInstance(ctx.exception, KeyError)

    def test_exhaustion_returns_empty_sentinel(self):
        from app.clients.binance_client import call_with_retry

        fn = MagicMock(side_effect=RuntimeError("net"))
        result = call_with_retry(
            fn, retries=3, delay=0, context="teste", empty={}, sleep=MagicMock()
        )
        self.assertEqual(result, {})
        self.assertEqual(fn.call_count, 3)

    def test_invalid_result_is_retried_until_valid(self):
        from app.clients.binance_client import call_with_retry

        fn = MagicMock(side_effect=[[], [], [7]])
        result = call_with_retry(
            fn,
            retries=3,
            delay=0,
            context="teste",
            validate=lambda data: isinstance(data, list) and len(data) > 0,
            empty=[],
            sleep=MagicMock(),
        )
        self.assertEqual(result, [7])
