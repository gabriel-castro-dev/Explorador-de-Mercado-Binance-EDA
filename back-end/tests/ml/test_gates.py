"""Gate de publicação: aprova e reprova pelos motivos certos."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.config import GateConfig
from app.ml.evaluation.gates import publication_gate
from app.ml.evaluation.metrics import evaluate_predictions


def _reports(model_errors: np.ndarray):
    """Monta relatórios modelo × naive sobre os mesmos targets realizados."""
    rng = np.random.default_rng(0)
    y_true = rng.normal(0.0, 0.02, 200)
    frame = pd.DataFrame({"symbol": "AAAUSDT", "y_1": y_true})
    model_predictions = pd.DataFrame({"y_1": y_true + model_errors}, index=frame.index)
    naive_predictions = pd.DataFrame({"y_1": 0.0}, index=frame.index)
    model_report = evaluate_predictions(frame, model_predictions, ("y_1",))
    naive_report = evaluate_predictions(frame, naive_predictions, ("y_1",))
    return model_report, naive_report, model_predictions


class PublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.config = GateConfig(min_skill_score=0.0)

    def test_model_better_than_naive_passes(self):
        rng = np.random.default_rng(1)
        model_report, naive_report, predictions = _reports(rng.normal(0.0, 0.001, 200))
        result = publication_gate(model_report, naive_report, predictions, self.config)
        self.assertTrue(result.passed)
        self.assertGreater(result.skill, 0.0)

    def test_model_worse_than_naive_fails(self):
        rng = np.random.default_rng(2)
        model_report, naive_report, predictions = _reports(rng.normal(0.0, 0.1, 200))
        result = publication_gate(model_report, naive_report, predictions, self.config)
        self.assertFalse(result.passed)
        self.assertLess(result.skill, 0.0)
        self.assertIn("não bate o naive", result.reason)

    def test_degenerate_predictions_fail_even_with_good_mae(self):
        rng = np.random.default_rng(3)
        y_true = rng.normal(0.0, 0.0001, 200)  # mercado quase parado
        frame = pd.DataFrame({"symbol": "AAAUSDT", "y_1": y_true})
        constant = pd.DataFrame({"y_1": 0.0}, index=frame.index)
        report = evaluate_predictions(frame, constant, ("y_1",))
        result = publication_gate(report, report, constant, self.config)
        self.assertFalse(result.passed)
        self.assertIn("degenerada", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
