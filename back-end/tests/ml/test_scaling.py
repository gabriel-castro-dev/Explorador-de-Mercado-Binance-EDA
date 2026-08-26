"""Testes do scaler: estatísticas exclusivamente do treino."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.scaling import FeatureScaler


def _frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(0)
    train = pd.DataFrame({"a": rng.normal(10.0, 2.0, 200), "b": rng.normal(-5.0, 0.5, 200)})
    val = pd.DataFrame({"a": rng.normal(50.0, 9.0, 80), "b": rng.normal(3.0, 4.0, 80)})
    return train, val


class FeatureScalerTests(unittest.TestCase):
    def test_statistics_come_from_train_only(self):
        train, val = _frames()
        scaler = FeatureScaler().fit(train, ("a", "b"))
        pd.testing.assert_series_equal(scaler.means, train[["a", "b"]].mean())
        # Transformar a validação usa média/desvio do TREINO: o resultado não é
        # z-score da própria validação (que teria média ~0).
        scaled_val = scaler.transform(val)
        self.assertGreater(scaled_val["a"].mean(), 5.0)
        # E o treino transformado fica de fato centrado.
        scaled_train = scaler.transform(train)
        self.assertAlmostEqual(scaled_train["a"].mean(), 0.0, places=10)

    def test_transform_before_fit_raises(self):
        train, _ = _frames()
        with self.assertRaises(RuntimeError):
            FeatureScaler().transform(train)

    def test_constant_column_does_not_explode(self):
        train = pd.DataFrame({"a": [3.0, 3.0, 3.0, 3.0]})
        scaler = FeatureScaler().fit(train, ("a",))
        result = scaler.transform(train)
        self.assertTrue(np.isfinite(result["a"]).all())
        self.assertTrue((result["a"] == 0.0).all())

    def test_outliers_are_clipped_at_sigma(self):
        train = pd.DataFrame({"a": np.concatenate([np.zeros(99), [1.0]])})
        scaler = FeatureScaler(clip_sigma=3.0).fit(train, ("a",))
        extreme = pd.DataFrame({"a": [1e9, -1e9]})
        result = scaler.transform(extreme)
        self.assertEqual(result["a"].tolist(), [3.0, -3.0])

    def test_missing_column_raises(self):
        train, _ = _frames()
        scaler = FeatureScaler().fit(train, ("a", "b"))
        with self.assertRaises(ValueError):
            scaler.transform(train.drop(columns=["b"]))


if __name__ == "__main__":
    unittest.main()
