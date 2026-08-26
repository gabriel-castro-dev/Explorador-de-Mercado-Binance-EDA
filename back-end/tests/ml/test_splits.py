"""Testes das janelas walk-forward: embargo estrito, sem sobreposição, expanding."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from app.ml.splits import walk_forward_windows


def _dates(days: int, start: str = "2023-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start, periods=days, freq="D", tz="UTC")


class WalkForwardTests(unittest.TestCase):
    def test_folds_are_chronological_contiguous_and_embargoed(self):
        dates = _dates(400)
        folds = walk_forward_windows(dates, eval_days=30, embargo_days=7, n_folds=4)
        self.assertEqual(len(folds), 4)
        for fold in folds:
            gap = (fold.eval_dates.min() - fold.train_dates.max()).days
            # Gap estrito: com embargo=7, um target de treino y_7 termina no
            # máximo um dia antes da janela avaliada começar.
            self.assertGreater(gap, 7)
            self.assertEqual(len(fold.eval_dates), 30)
            self.assertFalse(set(fold.train_dates) & set(fold.eval_dates))
        # Janelas de avaliação cobrem o fim da série sem buraco nem sobreposição.
        for earlier, later in zip(folds, folds[1:]):
            self.assertEqual((later.eval_dates.min() - earlier.eval_dates.max()).days, 1)
        self.assertEqual(folds[-1].eval_dates.max(), dates.max())

    def test_train_windows_are_expanding(self):
        folds = walk_forward_windows(_dates(400), eval_days=30, embargo_days=7, n_folds=4)
        sizes = [len(fold.train_dates) for fold in folds]
        self.assertEqual(sizes, sorted(sizes))
        self.assertLess(sizes[0], sizes[-1])

    def test_too_many_folds_for_history_raises(self):
        with self.assertRaises(ValueError):
            walk_forward_windows(
                _dates(100), eval_days=30, embargo_days=7, n_folds=4, min_train_days=30
            )

    def test_naive_dates_are_rejected(self):
        naive = pd.date_range("2023-01-01", periods=300, freq="D")  # sem tz
        with self.assertRaises(ValueError):
            walk_forward_windows(naive, eval_days=30, embargo_days=7, n_folds=2)


if __name__ == "__main__":
    unittest.main()
