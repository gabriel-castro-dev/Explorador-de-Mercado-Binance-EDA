"""Treino diário + inferência: gate, fallback, bandas e CLI com repos fake."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.config import GateConfig, MLConfig
from app.ml.inference import build_fallback_rows, build_forecast_rows, build_metrics_record
from app.ml.main import run_train_predict
from app.ml.models.baselines import DriftBaseline, NaiveZeroReturn
from app.ml.training import run_training
from tests.ml.synthetic import make_drift_market, ml_config

_RUN_AT = pd.Timestamp("2026-08-23T00:10:00", tz="UTC")
_FAST_FACTORIES = {"naive": NaiveZeroReturn, "drift": DriftBaseline}


def _drift_outcome(config: MLConfig | None = None):
    config = config or ml_config(min_history_days=10)
    features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
    outcome = run_training(
        features,
        klines,
        config,
        git_sha="abc1234def",
        run_date=_RUN_AT,
        factories=_FAST_FACTORIES,
    )
    return outcome, features, klines


class RunTrainingTests(unittest.TestCase):
    def test_drift_champion_passes_gate_with_traceable_version(self):
        outcome, _, _ = _drift_outcome()
        self.assertEqual(outcome.champion.name, "drift")
        self.assertTrue(outcome.gate.passed)
        self.assertEqual(outcome.model_version, "20260823-abc1234-drift")
        self.assertLess(outcome.train_start, outcome.train_end)

    def test_residual_band_width_never_shrinks_with_horizon(self):
        outcome, _, _ = _drift_outcome()
        widths = outcome.residual_quantiles["upper"] - outcome.residual_quantiles["lower"]
        self.assertTrue((widths.diff().dropna() >= -1e-15).all())

    def test_missing_naive_candidate_is_rejected(self):
        features, klines = make_drift_market({"AAAUSDT": 0.01})
        with self.assertRaises(ValueError):
            run_training(
                features,
                klines,
                ml_config(min_history_days=10),
                git_sha="abc1234",
                run_date=_RUN_AT,
                factories={"drift": DriftBaseline},
            )


class ForecastRowsTests(unittest.TestCase):
    def test_curve_shape_prices_and_band(self):
        outcome, _, klines = _drift_outcome()
        rows = build_forecast_rows(outcome, run_at=_RUN_AT)
        # 2 símbolos × 2 horizontes.
        self.assertEqual(len(rows), 4)
        last_close = klines[klines["symbol"] == "AAAUSDT"]["close"].iloc[-1]
        for row in rows:
            self.assertFalse(row["is_fallback"])
            self.assertEqual(row["model_version"], outcome.model_version)
            self.assertLessEqual(row["pred_lower"], row["predicted_close"] + 1e-9)
            self.assertLessEqual(row["predicted_close"], row["pred_upper"] + 1e-9)
        aaa_h1 = next(r for r in rows if r["symbol"] == "AAAUSDT" and r["horizon_days"] == 1)
        expected = last_close * np.exp(aaa_h1["predicted_log_return"])
        self.assertAlmostEqual(aaa_h1["predicted_close"], expected, places=9)
        # target_time = origem + h dias.
        origin = pd.Timestamp(aaa_h1["target_time"]) - pd.Timedelta(days=1)
        self.assertEqual(origin, klines["open_time"].max())

    def test_fallback_rows_are_flagged_random_walk(self):
        # Gate impossível: skill máximo é 1.0 — força o caminho de fallback.
        outcome, _, klines = _drift_outcome(
            ml_config(min_history_days=10).model_copy(
                update={"gate": GateConfig(min_skill_score=2.0)}
            )
        )
        self.assertFalse(outcome.gate.passed)
        rows = build_fallback_rows(outcome, run_at=_RUN_AT)
        last_close = klines[klines["symbol"] == "AAAUSDT"]["close"].iloc[-1]
        for row in rows:
            self.assertTrue(row["is_fallback"])
            self.assertTrue(row["model_version"].endswith("-fallback-naive"))
            self.assertEqual(row["predicted_log_return"], 0.0)
        aaa_rows = [r for r in rows if r["symbol"] == "AAAUSDT"]
        for row in aaa_rows:  # random walk: preço previsto = último close
            self.assertAlmostEqual(row["predicted_close"], last_close, places=9)


class MetricsRecordTests(unittest.TestCase):
    def test_record_is_json_serializable_and_traceable(self):
        outcome, _, _ = _drift_outcome()
        record = build_metrics_record(
            outcome, _RUN_AT, git_sha="abc1234def", published_fallback=False
        )
        json.dumps(record)  # jsonb do Supabase exige serialização limpa
        self.assertEqual(record["model_version"], outcome.model_version)
        self.assertEqual(record["model_type"], "drift")
        self.assertFalse(record["is_fallback"])
        self.assertIn("y_1", record["baseline_mae"])
        self.assertTrue(record["hyperparams"]["gate"]["passed"])
        self.assertEqual(record["hyperparams"]["n_folds"], 2)
        self.assertEqual(len(record["metrics"]["per_fold_skill_h1"]), 2)
        self.assertIn("per_symbol", record["metrics"])

    def test_fallback_record_uses_fallback_version(self):
        outcome, _, _ = _drift_outcome()
        record = build_metrics_record(
            outcome, _RUN_AT, git_sha="abc1234def", published_fallback=True
        )
        self.assertTrue(record["model_version"].endswith("-fallback-naive"))
        self.assertEqual(record["model_type"], "naive-fallback")
        self.assertTrue(record["is_fallback"])
        # Métricas publicadas são as do naive (skill 0), não as do campeão reprovado.
        self.assertEqual(record["metrics"]["skill_score_h1"], 0.0)
        self.assertEqual(record["hyperparams"]["champion"], "drift")


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


class _StubForecastRepo:
    def __init__(self):
        self.predictions: list[list[dict]] = []
        self.metrics: list[dict] = []

    def upsert_predictions(self, rows):
        self.predictions.append(rows)
        return len(rows)

    def upsert_model_metrics(self, record):
        self.metrics.append(record)

    def upsert_monte_carlo(self, rows):
        return len(rows)


class TrainPredictCliTests(unittest.TestCase):
    def test_publishes_champion_and_metrics_with_exit_zero(self):
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        forecast_repo = _StubForecastRepo()
        exit_code = run_train_predict(
            features_repo=_StubFeaturesRepo(features),
            klines_repo=_StubKlinesRepo(klines),
            forecast_repo=forecast_repo,
            config=ml_config(min_history_days=10),
            git_sha="abc1234def",
            now=_RUN_AT,
            factories=_FAST_FACTORIES,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(forecast_repo.predictions), 1)
        self.assertEqual(len(forecast_repo.predictions[0]), 4)
        self.assertFalse(forecast_repo.predictions[0][0]["is_fallback"])
        self.assertEqual(len(forecast_repo.metrics), 1)
        self.assertFalse(forecast_repo.metrics[0]["is_fallback"])

    def test_failed_gate_publishes_flagged_fallback_with_exit_zero(self):
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        forecast_repo = _StubForecastRepo()
        config = ml_config(min_history_days=10).model_copy(
            update={"gate": GateConfig(min_skill_score=2.0)}
        )
        exit_code = run_train_predict(
            features_repo=_StubFeaturesRepo(features),
            klines_repo=_StubKlinesRepo(klines),
            forecast_repo=forecast_repo,
            config=config,
            git_sha="abc1234def",
            now=_RUN_AT,
            factories=_FAST_FACTORIES,
        )
        self.assertEqual(exit_code, 0)
        self.assertTrue(all(r["is_fallback"] for r in forecast_repo.predictions[0]))
        self.assertTrue(forecast_repo.metrics[0]["is_fallback"])

    def test_unexpected_failure_returns_exit_one(self):
        from unittest.mock import patch

        from app.ml import main as ml_main

        with patch.object(ml_main, "FeaturesRepository", side_effect=RuntimeError("sem banco")):
            self.assertEqual(ml_main.main(["train-predict"]), 1)


if __name__ == "__main__":
    unittest.main()
