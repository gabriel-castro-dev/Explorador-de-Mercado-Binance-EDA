"""Monte Carlo fase 1: bootstrap dos resíduos de validação sobre o drift previsto.

Invariantes cobertas: determinismo por seed derivada de model_version, forma e
sanidade das trajetórias, classificação apontando para índices reais e — a
mais importante — a nuvem conta a mesma história que a banda de incerteza.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.config import GateConfig, MonteCarloConfig
from app.ml.inference import (
    build_fallback_rows,
    build_forecast_rows,
    build_monte_carlo_rows,
)
from app.ml.main import run_train_predict
from app.ml.models.baselines import DriftBaseline, NaiveZeroReturn
from app.ml.montecarlo import classify_paths, seed_from_version, simulate_paths
from app.ml.training import run_training
from tests.ml.synthetic import make_drift_market, make_market, ml_config

_RUN_AT = pd.Timestamp("2026-08-23T00:10:00", tz="UTC")
_FACTORIES = {"naive": NaiveZeroReturn, "drift": DriftBaseline}


def _residuals():
    rng = np.random.default_rng(7)
    return rng.normal(0.0, [0.02, 0.03], size=(300, 2))


class SimulatePathsTests(unittest.TestCase):
    def test_same_inputs_same_paths(self):
        first = simulate_paths(100.0, np.array([0.01, 0.02]), _residuals(), 50, seed=123)
        second = simulate_paths(100.0, np.array([0.01, 0.02]), _residuals(), 50, seed=123)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape, (50, 2))

    def test_different_seed_different_paths(self):
        first = simulate_paths(100.0, np.array([0.01, 0.02]), _residuals(), 50, seed=1)
        second = simulate_paths(100.0, np.array([0.01, 0.02]), _residuals(), 50, seed=2)
        self.assertFalse(np.array_equal(first, second))

    def test_paths_are_prices_positive_and_finite(self):
        paths = simulate_paths(100.0, np.array([0.01, 0.02]), _residuals(), 200, seed=0)
        self.assertTrue(np.isfinite(paths).all())
        self.assertTrue((paths > 0).all())
        # Sem resíduo, a trajetória é o próprio drift em preço.
        flat = simulate_paths(100.0, np.array([0.01, 0.02]), np.zeros((5, 2)), 3, seed=0)
        np.testing.assert_allclose(flat[0], 100.0 * np.exp([0.01, 0.02]))

    def test_each_path_resamples_one_validation_row(self):
        # Um cenário por trajetória: o resíduo de h=1 e h=2 vêm da MESMA linha,
        # preservando a forma da trajetória (não um sorteio independente por passo).
        residuals = np.array([[0.1, 0.5], [-0.1, -0.5]])
        paths = simulate_paths(1.0, np.zeros(2), residuals, 40, seed=3)
        logs = np.log(paths)
        for row in logs:
            self.assertIn(tuple(np.round(row, 9)), {(0.1, 0.5), (-0.1, -0.5)})

    def test_rejects_shape_mismatch(self):
        with self.assertRaises(ValueError):
            simulate_paths(100.0, np.array([0.01, 0.02, 0.03]), _residuals(), 10, seed=0)


class ClassifyPathsTests(unittest.TestCase):
    def test_best_base_worst_by_terminal_value(self):
        paths = np.array([[1.0, 1.2], [1.0, 0.8], [1.0, 1.0], [1.0, 1.1], [1.0, 0.9]])
        classified = classify_paths(paths)
        self.assertEqual(classified["best"], 0)
        self.assertEqual(classified["worst"], 1)
        self.assertEqual(classified["base"], 2)  # mediana terminal = 1.0
        for index in classified.values():
            self.assertLess(index, len(paths))


class SeedTests(unittest.TestCase):
    def test_seed_is_stable_and_version_specific(self):
        self.assertEqual(
            seed_from_version("20260826-abc1234-drift"), seed_from_version("20260826-abc1234-drift")
        )
        self.assertNotEqual(
            seed_from_version("20260826-abc1234-drift"),
            seed_from_version("20260826-abc1234-drift-fallback-naive"),
        )
        self.assertNotEqual(
            seed_from_version("20260826-abc1234-drift", "BTCUSDT"),
            seed_from_version("20260826-abc1234-drift", "ETHUSDT"),
        )


def _noisy_outcome(config=None):
    config = config or ml_config(min_history_days=10)
    features, klines = make_market(days=160, seed=11)
    return run_training(
        features, klines, config, git_sha="abc1234def", run_date=_RUN_AT, factories=_FACTORIES
    )


class MonteCarloRowsTests(unittest.TestCase):
    def test_one_row_per_symbol_with_real_count_and_classification(self):
        outcome = _noisy_outcome()
        rows = build_monte_carlo_rows(outcome, run_at=_RUN_AT, n_paths=200)
        self.assertEqual(sorted(r["symbol"] for r in rows), ["AAAUSDT", "BBBUSDT"])
        for row in rows:
            self.assertEqual(row["model_version"], outcome.model_version)
            self.assertEqual(row["run_at"], _RUN_AT.isoformat())
            self.assertEqual(row["horizon_days"], 2)
            self.assertEqual(row["step_seconds"], 86400)
            self.assertEqual(row["n_simulated"], 200)
            self.assertEqual(len(row["paths"]), row["n_simulated"])
            self.assertTrue(all(len(path) == 2 for path in row["paths"]))
            self.assertTrue(all(np.isfinite(path).all() for path in row["paths"]))
            self.assertTrue(all(min(path) > 0 for path in row["paths"]))
            classified = row["classified"]
            self.assertEqual(set(classified), {"best", "base", "worst"})
            self.assertGreaterEqual(
                row["paths"][classified["best"]][-1], row["paths"][classified["worst"]][-1]
            )
            json.dumps(row)  # jsonb

    def test_rows_are_deterministic_per_model_version(self):
        outcome = _noisy_outcome()
        first = build_monte_carlo_rows(outcome, run_at=_RUN_AT, n_paths=50)
        second = build_monte_carlo_rows(outcome, run_at=_RUN_AT, n_paths=50)
        self.assertEqual(first, second)

    def test_symbols_do_not_share_scenario_order(self):
        # Mesma rodada, ativos diferentes: os resíduos reamostrados (log(path) −
        # log(close) − ŷ) não podem ser idênticos linha a linha entre ativos.
        outcome = _noisy_outcome()
        forecasts = build_forecast_rows(outcome, run_at=_RUN_AT)
        rows = build_monte_carlo_rows(outcome, run_at=_RUN_AT, n_paths=100)
        sampled = {}
        for row in rows:
            predicted = np.array(
                [
                    f["predicted_log_return"]
                    for f in sorted(
                        (f for f in forecasts if f["symbol"] == row["symbol"]),
                        key=lambda f: f["horizon_days"],
                    )
                ]
            )
            close = next(
                f for f in forecasts if f["symbol"] == row["symbol"] and f["horizon_days"] == 1
            )["predicted_close"] / np.exp(predicted[0])
            sampled[row["symbol"]] = np.log(np.array(row["paths"]) / close) - predicted
        self.assertFalse(np.allclose(sampled["AAAUSDT"], sampled["BBBUSDT"], atol=1e-4))

    def test_cloud_agrees_with_uncertainty_band(self):
        # Quantis 10/90 do terminal (último horizonte) ≈ pred_lower/pred_upper.
        outcome = _noisy_outcome()
        forecasts = build_forecast_rows(outcome, run_at=_RUN_AT)
        rows = build_monte_carlo_rows(outcome, run_at=_RUN_AT, n_paths=4000)
        for row in rows:
            last = next(
                f for f in forecasts if f["symbol"] == row["symbol"] and f["horizon_days"] == 2
            )
            terminal = np.array([path[-1] for path in row["paths"]])
            lower, upper = np.quantile(terminal, [0.1, 0.9])
            band_width = np.log(last["pred_upper"]) - np.log(last["pred_lower"])
            self.assertGreater(band_width, 0)
            tolerance = 0.25 * band_width
            self.assertLessEqual(abs(np.log(lower) - np.log(last["pred_lower"])), tolerance)
            self.assertLessEqual(abs(np.log(upper) - np.log(last["pred_upper"])), tolerance)

    def test_fallback_cloud_uses_naive_residuals_and_fallback_version(self):
        outcome = _noisy_outcome(
            ml_config(min_history_days=10).model_copy(
                update={"gate": GateConfig(min_skill_score=2.0)}
            )
        )
        self.assertFalse(outcome.gate.passed)
        forecasts = build_fallback_rows(outcome, run_at=_RUN_AT)
        rows = build_monte_carlo_rows(
            outcome, run_at=_RUN_AT, n_paths=4000, published_fallback=True
        )
        for row in rows:
            self.assertTrue(row["model_version"].endswith("-fallback-naive"))
            last = next(
                f for f in forecasts if f["symbol"] == row["symbol"] and f["horizon_days"] == 2
            )
            terminal = np.array([path[-1] for path in row["paths"]])
            lower, upper = np.quantile(terminal, [0.1, 0.9])
            tolerance = 0.25 * (np.log(last["pred_upper"]) - np.log(last["pred_lower"]))
            self.assertLessEqual(abs(np.log(lower) - np.log(last["pred_lower"])), tolerance)
            self.assertLessEqual(abs(np.log(upper) - np.log(last["pred_upper"])), tolerance)


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
        self.monte_carlo: list[list[dict]] = []

    def upsert_predictions(self, rows):
        self.predictions.append(rows)
        return len(rows)

    def upsert_model_metrics(self, record):
        self.metrics.append(record)

    def upsert_monte_carlo(self, rows):
        self.monte_carlo.append(rows)
        return len(rows)


class TrainPredictPublishesMonteCarloTests(unittest.TestCase):
    def test_paths_share_the_model_version_of_the_published_curve(self):
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        repo = _StubForecastRepo()
        config = ml_config(min_history_days=10).model_copy(
            update={"montecarlo": MonteCarloConfig(n_paths=30)}
        )
        exit_code = run_train_predict(
            features_repo=_StubFeaturesRepo(features),
            klines_repo=_StubKlinesRepo(klines),
            forecast_repo=repo,
            config=config,
            git_sha="abc1234def",
            now=_RUN_AT,
            factories=_FACTORIES,
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(repo.monte_carlo), 1)
        versions = {row["model_version"] for row in repo.monte_carlo[0]}
        self.assertEqual(versions, {repo.predictions[0][0]["model_version"]})
        self.assertEqual(repo.monte_carlo[0][0]["n_simulated"], 30)


if __name__ == "__main__":
    unittest.main()
