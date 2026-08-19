import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.timeframe import Timeframe


class TimeframeTests(unittest.TestCase):
    def test_24h_is_an_alias_for_daily(self):
        self.assertIs(Timeframe("24h"), Timeframe.D1)

    def test_table_mappings(self):
        self.assertEqual(Timeframe.M15.kline_table, "klines_15m")
        self.assertEqual(Timeframe.H1.kline_table, "klines_1h")
        self.assertEqual(Timeframe.D1.kline_table, "klines_1d")
        self.assertEqual(Timeframe.M15.feature_table, "features_15m")
        self.assertEqual(Timeframe.D1.feature_table, "features_24h")

    def test_pandas_freq_and_time_columns(self):
        self.assertEqual(Timeframe.M15.pandas_freq, "15min")
        self.assertEqual(Timeframe.D1.pandas_freq, "D")
        self.assertEqual(Timeframe.H1.time_column, "open_time")
        self.assertEqual(Timeframe.H1.feature_time_column, "timestamp")

    def test_unknown_value_raises(self):
        with self.assertRaises(ValueError):
            Timeframe("2h")


if __name__ == "__main__":
    unittest.main()
