"""Seleção de campeão: ranking por skill e regra do ensemble."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.evaluation.metrics import evaluate_predictions
from app.ml.evaluation.walkforward import WalkForwardResult
from app.ml.selection import select_champion


def _frame() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {"symbol": "AAAUSDT", "y_1": rng.normal(0.0, 0.02, 100)},
        index=range(100),
    )


def _result(frame: pd.DataFrame, predictions: pd.Series) -> WalkForwardResult:
    prediction_frame = pd.DataFrame({"y_1": predictions}, index=frame.index)
    report = evaluate_predictions(frame, prediction_frame, ("y_1",))
    return WalkForwardResult(
        pooled=report,
        fold_reports=[report],
        pooled_predictions=prediction_frame,
        pooled_frame=frame,
    )


class SelectChampionTests(unittest.TestCase):
    def test_single_winner_is_champion_without_ensemble(self):
        frame = _frame()
        rng = np.random.default_rng(1)
        results = {
            "naive": _result(frame, pd.Series(0.0, index=frame.index)),
            "good": _result(frame, frame["y_1"] + rng.normal(0.0, 0.001, len(frame))),
            "bad": _result(frame, frame["y_1"] + rng.normal(0.0, 0.5, len(frame))),
        }
        champion = select_champion(results)
        self.assertEqual(champion.name, "good")
        self.assertEqual(champion.members, ("good",))
        self.assertGreater(champion.skill, 0.0)
        # Só um candidato bateu o naive → ensemble nem entra no ranking.
        self.assertFalse(any(name.startswith("ensemble") for name in champion.ranking.index))

    def test_ensemble_wins_when_errors_cancel(self):
        frame = _frame()
        noise = 0.005 * np.ones(len(frame))
        results = {
            "naive": _result(frame, pd.Series(0.0, index=frame.index)),
            # Erros simétricos: a média dos dois é o foresight perfeito.
            "plus": _result(frame, frame["y_1"] + noise),
            "minus": _result(frame, frame["y_1"] - noise),
        }
        champion = select_champion(results)
        self.assertTrue(champion.name.startswith("ensemble:"))
        self.assertEqual(set(champion.members), {"plus", "minus"})
        self.assertAlmostEqual(champion.skill, 1.0, places=9)

    def test_missing_naive_reference_raises(self):
        frame = _frame()
        with self.assertRaises(ValueError):
            select_champion({"good": _result(frame, frame["y_1"])})

    def test_candidates_on_different_rows_are_rejected(self):
        frame = _frame()
        other = frame.iloc[:50]
        results = {
            "naive": _result(frame, pd.Series(0.0, index=frame.index)),
            "good": _result(other, other["y_1"]),
        }
        with self.assertRaises(ValueError):
            select_champion(results)


if __name__ == "__main__":
    unittest.main()
