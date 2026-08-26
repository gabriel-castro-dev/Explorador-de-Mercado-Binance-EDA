"""Comando backtest: relatório determinístico anexado ao log de experimentos."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from app.ml.main import run_backtest_report
from app.ml.models.baselines import DriftBaseline, NaiveZeroReturn
from tests.ml.synthetic import make_drift_market, ml_config

_NOW = pd.Timestamp("2026-08-23T00:10:00", tz="UTC")


class _StubFeaturesRepo:
    def __init__(self, frame):
        self.frame = frame

    def get_all_features(self, timeframe):
        return self.frame


class _StubKlinesRepo:
    def __init__(self, frame):
        self.frame = frame

    def get_latest_klines(self, timeframe):
        return self.frame


class BacktestReportTests(unittest.TestCase):
    def test_appends_deterministic_report(self):
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "experiments.md"
            report.write_text("# log\n", encoding="utf-8")
            kwargs = dict(
                features_repo=_StubFeaturesRepo(features),
                klines_repo=_StubKlinesRepo(klines),
                config=ml_config(min_history_days=10),
                report_path=report,
                now=_NOW,
                factories={"naive": NaiveZeroReturn, "drift": DriftBaseline},
            )
            self.assertEqual(run_backtest_report(**kwargs), 0)
            first = report.read_text(encoding="utf-8")
            self.assertIn("## BT-20260823 — backtest do campeão `drift`", first)
            self.assertIn("Skill h1 por fold:", first)
            self.assertIn("Buy-and-hold:", first)
            # Determinístico: rodar de novo anexa um bloco idêntico.
            run_backtest_report(**kwargs)
            second = report.read_text(encoding="utf-8")
            block = first[len("# log\n") :]
            self.assertEqual(second, "# log\n" + block + block)


if __name__ == "__main__":
    unittest.main()
