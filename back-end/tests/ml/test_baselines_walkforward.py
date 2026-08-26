"""Baselines + harness walk-forward: isolamento temporal e respostas fechadas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.dataset import build_dataset
from app.ml.evaluation.metrics import skill_by_horizon
from app.ml.evaluation.walkforward import evaluate_walk_forward
from app.ml.models.baselines import (
    DriftBaseline,
    NaiveZeroReturn,
    RidgeBaseline,
    is_degenerate_prediction,
)
from app.ml.splits import WalkForwardFold, walk_forward_windows
from tests.ml.synthetic import make_drift_market, ml_config


def _drift_setup():
    config = ml_config(min_history_days=10)
    features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
    dataset = build_dataset(features, klines, config.dataset)
    dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
    folds = walk_forward_windows(dates, eval_days=20, embargo_days=2, n_folds=2)
    return config, dataset, folds


class BaselineBehaviorTests(unittest.TestCase):
    def test_naive_predicts_zero_and_is_flagged_degenerate(self):
        frame = pd.DataFrame({"symbol": ["AAA"], "y_1": [0.5]})
        naive = NaiveZeroReturn().fit(frame, (), ("y_1",))
        predictions = naive.predict(frame)
        self.assertEqual(predictions["y_1"].tolist(), [0.0])
        self.assertTrue(is_degenerate_prediction(predictions))

    def test_drift_learns_per_symbol_mean(self):
        train = pd.DataFrame(
            {"symbol": ["AAA", "AAA", "BBB", "BBB"], "y_1": [0.01, 0.01, -0.02, -0.02]}
        )
        drift = DriftBaseline().fit(train, (), ("y_1",))
        out = drift.predict(pd.DataFrame({"symbol": ["AAA", "BBB", "NOVA"]}, index=[7, 8, 9]))
        self.assertAlmostEqual(out.loc[7, "y_1"], 0.01, places=12)
        self.assertAlmostEqual(out.loc[8, "y_1"], -0.02, places=12)
        # Símbolo fora do treino cai na média global (-0.005).
        self.assertAlmostEqual(out.loc[9, "y_1"], -0.005, places=12)

    def test_ridge_recovers_planted_linear_signal(self):
        rng = np.random.default_rng(1)
        x = rng.normal(0.0, 1.0, 500)
        train = pd.DataFrame({"symbol": "AAA", "feat": x, "y_1": 3.0 * x})
        ridge = RidgeBaseline(alpha=1e-8).fit(train, ("feat",), ("y_1",))
        holdout = pd.DataFrame({"symbol": "AAA", "feat": [1.0, -2.0]}, index=[0, 1])
        predictions = ridge.predict(holdout)
        self.assertAlmostEqual(predictions.loc[0, "y_1"], 3.0, places=5)
        self.assertAlmostEqual(predictions.loc[1, "y_1"], -6.0, places=5)


class WalkForwardHarnessTests(unittest.TestCase):
    def test_drift_market_has_closed_form_answers(self):
        config, dataset, folds = _drift_setup()
        naive_result = evaluate_walk_forward(dataset, NaiveZeroReturn, folds, config)
        drift_result = evaluate_walk_forward(dataset, DriftBaseline, folds, config)
        # Série de drift constante: y_1 = ±0.01 sempre → MAE do naive = 0.01 exato.
        self.assertAlmostEqual(naive_result.pooled.per_horizon.loc["y_1", "mae"], 0.01, places=10)
        # O drift aprende a taxa exata no treino → erro ~zero e skill ~1.
        self.assertLess(drift_result.pooled.per_horizon.loc["y_1", "mae"], 1e-9)
        skills = skill_by_horizon(drift_result.pooled, naive_result.pooled)
        self.assertGreater(skills["y_1"], 0.999)
        self.assertAlmostEqual(
            drift_result.pooled.per_horizon.loc["y_1", "dir_acc"], 1.0, places=12
        )

    def test_model_never_sees_eval_dates(self):
        config, dataset, folds = _drift_setup()
        observed: list[tuple[pd.Timestamp, pd.Timestamp]] = []

        class SpyModel(NaiveZeroReturn):
            def fit(self, train_frame, feature_columns, target_columns):
                self._max_train = train_frame["timestamp"].max()
                return super().fit(train_frame, feature_columns, target_columns)

            def predict(self, frame):
                observed.append((self._max_train, frame["timestamp"].min()))
                return super().predict(frame)

        evaluate_walk_forward(dataset, SpyModel, folds, config)
        self.assertEqual(len(observed), len(folds))
        for max_train, min_eval in observed:
            self.assertGreater((min_eval - max_train).days, 2)  # embargo estrito

    def test_overlapping_folds_are_rejected(self):
        config, dataset, folds = _drift_setup()
        overlapping = [folds[0], WalkForwardFold(folds[1].train_dates, folds[0].eval_dates)]
        with self.assertRaises(ValueError):
            evaluate_walk_forward(dataset, NaiveZeroReturn, overlapping, config)

    def test_per_symbol_report_covers_both_symbols(self):
        config, dataset, folds = _drift_setup()
        result = evaluate_walk_forward(dataset, DriftBaseline, folds, config)
        self.assertEqual(set(result.pooled.per_symbol.index), {"AAAUSDT", "BBBUSDT"})


if __name__ == "__main__":
    unittest.main()
