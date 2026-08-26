"""LightGBM global: capacidade, determinismo e uso do símbolo categórico."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.dataset import build_dataset
from app.ml.evaluation.metrics import skill_by_horizon
from app.ml.evaluation.walkforward import evaluate_walk_forward
from app.ml.models.baselines import NaiveZeroReturn
from app.ml.models.gbm import LightGBMModel
from app.ml.splits import walk_forward_windows
from tests.ml.synthetic import make_drift_market, ml_config


def _tabular(seed: int = 0, rows: int = 800) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 1.0, rows)
    return pd.DataFrame(
        {
            "symbol": np.where(np.arange(rows) % 2 == 0, "AAAUSDT", "BBBUSDT"),
            "feat": x,
            # Padrão plantado não-linear: degrau no sinal da feature.
            "y_1": np.where(x > 0, 0.03, -0.01),
        }
    )


class LightGBMCapacityTests(unittest.TestCase):
    def test_learns_planted_step_pattern(self):
        train = _tabular(seed=0)
        holdout = _tabular(seed=1, rows=200)
        model = LightGBMModel(seed=42).fit(train, ("feat",), ("y_1",))
        predictions = model.predict(holdout)
        positive = holdout["feat"] > 0
        self.assertAlmostEqual(predictions.loc[positive, "y_1"].mean(), 0.03, places=3)
        self.assertAlmostEqual(predictions.loc[~positive, "y_1"].mean(), -0.01, places=3)

    def test_same_seed_same_predictions(self):
        train = _tabular(seed=2)
        holdout = _tabular(seed=3, rows=100)
        first = LightGBMModel(seed=42).fit(train, ("feat",), ("y_1",)).predict(holdout)
        second = LightGBMModel(seed=42).fit(train, ("feat",), ("y_1",)).predict(holdout)
        pd.testing.assert_frame_equal(first, second)

    def test_symbol_categorical_carries_signal(self):
        rng = np.random.default_rng(4)
        rows = 600
        symbols = np.where(np.arange(rows) % 2 == 0, "AAAUSDT", "BBBUSDT")
        train = pd.DataFrame(
            {
                "symbol": symbols,
                "feat": rng.normal(0.0, 1.0, rows),  # ruído puro
                "y_1": np.where(symbols == "AAAUSDT", 0.02, -0.02),
            }
        )
        model = LightGBMModel(seed=42).fit(train, ("feat",), ("y_1",))
        holdout = pd.DataFrame(
            {"symbol": ["AAAUSDT", "BBBUSDT", "NOVAUSDT"], "feat": [0.0, 0.0, 0.0]}
        )
        predictions = model.predict(holdout)
        self.assertAlmostEqual(predictions.loc[0, "y_1"], 0.02, places=3)
        self.assertAlmostEqual(predictions.loc[1, "y_1"], -0.02, places=3)
        # Símbolo nunca visto não pode explodir — só cai num palpite neutro.
        self.assertTrue(np.isfinite(predictions.loc[2, "y_1"]))

    def test_feature_importance_ranks_signal_over_noise(self):
        rng = np.random.default_rng(5)
        rows = 800
        signal = rng.normal(0.0, 1.0, rows)
        train = pd.DataFrame(
            {
                "symbol": "AAAUSDT",
                "signal": signal,
                "noise": rng.normal(0.0, 1.0, rows),
                "y_1": 0.05 * signal,
            }
        )
        model = LightGBMModel(seed=42).fit(train, ("signal", "noise"), ("y_1",))
        importance = model.feature_importance()
        self.assertEqual(importance.index[0], "signal")


class LightGBMWalkForwardTests(unittest.TestCase):
    def test_beats_naive_on_drift_market(self):
        config = ml_config(min_history_days=10)
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        dataset = build_dataset(features, klines, config.dataset)
        dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
        folds = walk_forward_windows(dates, eval_days=20, embargo_days=2, n_folds=2)

        gbm_result = evaluate_walk_forward(dataset, lambda: LightGBMModel(seed=42), folds, config)
        naive_result = evaluate_walk_forward(dataset, NaiveZeroReturn, folds, config)
        skills = skill_by_horizon(gbm_result.pooled, naive_result.pooled)
        # O drift por símbolo é aprendível via categoria: skill claramente positivo.
        self.assertGreater(skills["y_1"], 0.5)


if __name__ == "__main__":
    unittest.main()
