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
