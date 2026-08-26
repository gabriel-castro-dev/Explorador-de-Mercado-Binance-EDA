"""Testes das métricas em valores fechados — nada de 'parece razoável'."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.evaluation.metrics import (
    directional_accuracy,
    evaluate_predictions,
    mean_absolute_error,
    root_mean_squared_error,
    skill_by_horizon,
    skill_score,
)


class PointMetricTests(unittest.TestCase):
    def test_mae_and_rmse_closed_form(self):
        y_true = np.array([1.0, -1.0, 2.0])
        y_pred = np.array([0.0, 0.0, 0.0])
        self.assertAlmostEqual(mean_absolute_error(y_true, y_pred), 4.0 / 3.0, places=12)
        self.assertAlmostEqual(root_mean_squared_error(y_true, y_pred), np.sqrt(2.0), places=12)

    def test_directional_accuracy_counts_sign_matches(self):
        y_true = np.array([0.5, -0.5, 0.5, -0.5])
        y_pred = np.array([0.1, 0.1, 0.1, -0.1])  # acerta 1ª, erra 2ª, acerta 3ª e 4ª
        self.assertAlmostEqual(directional_accuracy(y_true, y_pred), 0.75, places=12)

    def test_directional_accuracy_ignores_zero_true_returns(self):
        y_true = np.array([0.0, 0.0, 1.0])
        y_pred = np.array([1.0, -1.0, 1.0])
        self.assertAlmostEqual(directional_accuracy(y_true, y_pred), 1.0, places=12)
        self.assertTrue(np.isnan(directional_accuracy(np.zeros(3), y_pred)))

    def test_skill_score_semantics(self):
        self.assertAlmostEqual(skill_score(1.0, 1.0), 0.0)  # naive contra si mesmo
        self.assertAlmostEqual(skill_score(0.5, 1.0), 0.5)  # metade do erro do naive
        self.assertLess(skill_score(2.0, 1.0), 0.0)  # pior que o naive é negativo
        with self.assertRaises(ValueError):
            skill_score(1.0, 0.0)


class EvaluatePredictionsTests(unittest.TestCase):
    def _toy(self):
        frame = pd.DataFrame(
            {
                "symbol": ["AAA", "AAA", "BBB", "BBB"],
                "y_1": [0.1, -0.1, 0.2, 0.2],
                "y_2": [0.2, -0.2, 0.4, 0.4],
            },
            index=[10, 11, 12, 13],
        )
        predictions = pd.DataFrame(
            {"y_1": [0.1, 0.1, 0.2, 0.2], "y_2": [0.2, -0.2, 0.4, 0.4]},
            index=[10, 11, 12, 13],
        )
        return frame, predictions

    def test_per_horizon_and_per_symbol_reports(self):
        frame, predictions = self._toy()
        report = evaluate_predictions(frame, predictions, ("y_1", "y_2"))
        self.assertAlmostEqual(report.per_horizon.loc["y_1", "mae"], 0.05, places=12)
        self.assertAlmostEqual(report.per_horizon.loc["y_2", "mae"], 0.0, places=12)
        self.assertAlmostEqual(report.per_horizon.loc["y_1", "dir_acc"], 0.75, places=12)
        # Por símbolo (h=1): AAA errou metade, BBB acertou tudo.
        self.assertAlmostEqual(report.per_symbol.loc["AAA", "mae"], 0.1, places=12)
        self.assertAlmostEqual(report.per_symbol.loc["BBB", "mae"], 0.0, places=12)
        self.assertEqual(int(report.per_symbol.loc["AAA", "n"]), 2)

    def test_index_mismatch_is_rejected(self):
        frame, predictions = self._toy()
        with self.assertRaises(ValueError):
            evaluate_predictions(frame, predictions.reset_index(drop=True), ("y_1",))

    def test_skill_by_horizon_compares_reports(self):
        frame, predictions = self._toy()
        model = evaluate_predictions(frame, predictions, ("y_1", "y_2"))
        naive = evaluate_predictions(
            frame,
            pd.DataFrame(0.0, index=frame.index, columns=["y_1", "y_2"]),
            ("y_1", "y_2"),
        )
        skills = skill_by_horizon(model, naive)
        # Naive MAE em y_1 = mean(|0.1|,|0.1|,|0.2|,|0.2|) = 0.15; modelo = 0.05.
        self.assertAlmostEqual(skills["y_1"], 1.0 - 0.05 / 0.15, places=12)
        self.assertAlmostEqual(skills["y_2"], 1.0, places=12)


if __name__ == "__main__":
    unittest.main()
