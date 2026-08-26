"""GRU: capacidade (overfit sanity), determinismo, early stopping e horizontes."""

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.dataset import build_dataset
from app.ml.evaluation.metrics import skill_by_horizon
from app.ml.evaluation.walkforward import evaluate_walk_forward
from app.ml.models.baselines import NaiveZeroReturn
from app.ml.models.gru import GRUModel
from app.ml.splits import walk_forward_windows
from tests.ml.synthetic import make_drift_market, ml_config

_FAST = {
    "hidden_size": 32,
    "embedding_dim": 4,
    "dropout": 0.0,
    "batch_size": 64,
    "inner_val_fraction": 0.2,
}


def _linear_frame(
    days: int = 90, seed: int = 0, slope_by_target: dict[str, float] | None = None
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    slopes = slope_by_target or {"y_1": 0.05}
    dates = pd.date_range("2024-01-01", periods=days, freq="D", tz="UTC")
    x = rng.normal(0.0, 1.0, days)
    frame = pd.DataFrame({"symbol": "AAAUSDT", "timestamp": dates, "feat": x})
    for target, slope in slopes.items():
        frame[target] = slope * x
    return frame


class GRUCapacityTests(unittest.TestCase):
    def test_overfits_planted_linear_signal_within_time_budget(self):
        frame = _linear_frame()
        started = time.monotonic()
        model = GRUModel(
            lookback=3,
            seed=42,
            params={**_FAST, "max_epochs": 300, "patience": 300},
        ).fit(frame, ("feat",), ("y_1",))
        elapsed = time.monotonic() - started
        predictions = model.predict(frame)
        residual = predictions["y_1"].to_numpy() - frame["y_1"].to_numpy()
        explained = 1.0 - np.var(residual) / np.var(frame["y_1"].to_numpy())
        # Sanity clássico de DL: capacidade de decorar um padrão simples.
        self.assertGreater(explained, 0.8)
        # E sem explosão de tempo em CPU (limite generoso para runners lentos).
        self.assertLess(elapsed, 60.0)

    def test_same_seed_same_predictions(self):
        frame = _linear_frame(seed=1)
        params = {**_FAST, "max_epochs": 20, "patience": 20}
        first = (
            GRUModel(lookback=3, seed=42, params=params)
            .fit(frame, ("feat",), ("y_1",))
            .predict(frame)
        )
        second = (
            GRUModel(lookback=3, seed=42, params=params)
            .fit(frame, ("feat",), ("y_1",))
            .predict(frame)
        )
        pd.testing.assert_frame_equal(first, second)

    def test_early_stopping_halts_on_pure_noise(self):
        rng = np.random.default_rng(2)
        frame = _linear_frame(days=120, seed=2)
        frame["y_1"] = rng.normal(0.0, 1.0, len(frame))  # nada a aprender
        model = GRUModel(
            lookback=3,
            seed=42,
            params={**_FAST, "max_epochs": 200, "patience": 3},
        ).fit(frame, ("feat",), ("y_1",))
        self.assertLess(model.epochs_run_, 200)

    def test_horizon_outputs_diverge(self):
        # y_2 é o oposto de y_1: cabeças multi-output não podem colapsar numa só.
        frame = _linear_frame(days=120, seed=3, slope_by_target={"y_1": 0.05, "y_2": -0.05})
        model = GRUModel(
            lookback=3,
            seed=42,
            params={**_FAST, "max_epochs": 200, "patience": 200},
        ).fit(frame, ("feat",), ("y_1", "y_2"))
        predictions = model.predict(frame)
        correlation = np.corrcoef(predictions["y_1"], predictions["y_2"])[0, 1]
        self.assertLess(correlation, 0.0)


class GRUWalkForwardTests(unittest.TestCase):
    def test_beats_naive_on_drift_market(self):
        config = ml_config(min_history_days=10, lookback_window=5)
        features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
        dataset = build_dataset(features, klines, config.dataset)
        dates = pd.DatetimeIndex(dataset.frame["timestamp"].unique()).sort_values()
        folds = walk_forward_windows(dates, eval_days=20, embargo_days=2, n_folds=2)

        def factory():
            return GRUModel(
                lookback=5,
                seed=42,
                params={**_FAST, "hidden_size": 16, "max_epochs": 80, "patience": 80},
            )

        gru_result = evaluate_walk_forward(dataset, factory, folds, config)
        naive_result = evaluate_walk_forward(dataset, NaiveZeroReturn, folds, config)
        skills = skill_by_horizon(gru_result.pooled, naive_result.pooled)
        # O drift por símbolo é aprendível pelo embedding: skill positivo claro.
        self.assertGreater(skills["y_1"], 0.3)


if __name__ == "__main__":
    unittest.main()
