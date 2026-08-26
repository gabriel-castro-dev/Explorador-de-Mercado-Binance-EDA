"""Monitoramento: erro realizado com resposta fechada e regra de degradação."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd

from app.ml.config import MonitoringConfig
from app.ml.main import run_evaluate
from app.ml.monitoring import detect_degradation, score_predictions

_CONFIG = MonitoringConfig(lookback_days=30, degradation_runs=2, min_scored_rows=2)


def _klines(closes: dict[str, list[float]], start: str = "2026-08-01") -> pd.DataFrame:
    rows = []
    for symbol, values in closes.items():
        dates = pd.date_range(start, periods=len(values), freq="D", tz="UTC")
        rows.append(pd.DataFrame({"symbol": symbol, "open_time": dates, "close": values}))
    return pd.concat(rows, ignore_index=True)


def _prediction(
    symbol: str,
    target: str,
    origin_close: float,
    predicted_log_return: float,
    version: str = "v1",
    run_at: str = "2026-08-02T00:10:00+00:00",
    horizon: int = 1,
) -> dict:
    return {
        "symbol": symbol,
        "model_version": version,
        "run_at": run_at,
        "target_time": f"{target}T00:00:00+00:00",
        "horizon_days": horizon,
        "predicted_close": origin_close * float(np.exp(predicted_log_return)),
        "predicted_log_return": predicted_log_return,
        "is_fallback": False,
    }


class ScorePredictionsTests(unittest.TestCase):
    def test_realized_error_closed_form(self):
        # Close 100 → 110: retorno realizado = log(1.1). Previsto log(1.05).
        klines = _klines({"AAAUSDT": [100.0, 110.0, 121.0]})
        predictions = [
            _prediction("AAAUSDT", "2026-08-02", 100.0, np.log(1.05)),
            _prediction("AAAUSDT", "2026-08-03", 110.0, np.log(1.10)),  # acerto exato
        ]
        [score] = score_predictions(predictions, klines, _CONFIG)
        expected_mae = (abs(np.log(1.05) - np.log(1.1)) + 0.0) / 2
        self.assertAlmostEqual(score.per_horizon.loc[1, "mae"], expected_mae, places=12)
        self.assertAlmostEqual(score.per_horizon.loc[1, "naive_mae"], np.log(1.1), places=12)
        self.assertGreater(score.skill_h1, 0.0)

    def test_predictions_without_realized_candle_are_ignored(self):
        klines = _klines({"AAAUSDT": [100.0, 110.0]})
        predictions = [
            _prediction("AAAUSDT", "2026-08-02", 100.0, 0.01),
            _prediction("AAAUSDT", "2026-08-09", 100.0, 0.01),  # sem vela → ignorada
            _prediction("AAAUSDT", "2026-08-02", 100.0, 0.02, horizon=2),
        ]
        [score] = score_predictions(predictions, klines, _CONFIG)
        self.assertEqual(score.n_rows, 2)

    def test_version_below_min_scored_rows_is_skipped(self):
        klines = _klines({"AAAUSDT": [100.0, 110.0]})
        predictions = [_prediction("AAAUSDT", "2026-08-02", 100.0, 0.01)]  # só 1 linha
        self.assertEqual(score_predictions(predictions, klines, _CONFIG), [])

    def test_empty_predictions_return_empty(self):
        self.assertEqual(score_predictions([], _klines({"AAAUSDT": [100.0]}), _CONFIG), [])


class DetectDegradationTests(unittest.TestCase):
    def _scores(self, log_returns_by_version: dict[str, float]) -> list:
        # Mercado sempre sobe log(1.1); previsão constante por versão.
        klines = _klines({"AAAUSDT": [100.0 * 1.1**i for i in range(10)]})
        predictions = []
        for index, (version, predicted) in enumerate(log_returns_by_version.items()):
            run_day = f"2026-08-0{index + 1}"
            for day in range(2, 6):
                origin = 100.0 * 1.1 ** (day - 2)  # close da véspera do target
                predictions.append(
                    _prediction(
                        "AAAUSDT",
                        f"2026-08-0{day}",
                        origin,
                        predicted,
                        version=version,
                        run_at=f"{run_day}T00:10:00+00:00",
                    )
                )
        return score_predictions(predictions, klines, _CONFIG)

    def test_consecutive_losses_trigger(self):
        # Previsão na direção errada: erro |pred − real| > |real| → skill < 0.
        scores = self._scores({"v1": -0.1, "v2": -0.1})
        self.assertTrue(all(s.skill_h1 < 0 for s in scores))
        self.assertTrue(detect_degradation(scores, _CONFIG))

    def test_recovery_resets_the_streak(self):
        scores = self._scores({"v1": -0.1, "v2": np.log(1.1)})  # v2 acerta
        self.assertFalse(detect_degradation(scores, _CONFIG))

    def test_too_few_scored_versions_never_trigger(self):
        scores = self._scores({"v1": -0.1})
        self.assertFalse(detect_degradation(scores, _CONFIG))


class _StubKlinesRepo:
    def __init__(self, frame):
        self.frame = frame

    def get_latest_klines(self, timeframe):
        return self.frame


class _StubForecastRepo:
    def __init__(self, predictions):
        self.predictions = predictions
        self.realized: dict[str, dict] = {}

    def get_scoreable_predictions(self, now, since):
        return self.predictions

    def update_realized_metrics(self, model_version, payload):
        self.realized[model_version] = payload


class EvaluateCommandTests(unittest.TestCase):
    def test_persists_realized_metrics_and_exits_zero(self):
        klines = _klines({"AAAUSDT": [100.0, 110.0, 121.0]})
        predictions = [
            _prediction("AAAUSDT", "2026-08-02", 100.0, np.log(1.1)),
            _prediction("AAAUSDT", "2026-08-03", 110.0, np.log(1.1)),
        ]
        repo = _StubForecastRepo(predictions)
        exit_code = run_evaluate(
            klines_repo=_StubKlinesRepo(klines),
            forecast_repo=repo,
            config=_evaluate_config(),
            now=pd.Timestamp("2026-08-10", tz="UTC"),
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("v1", repo.realized)
        self.assertEqual(repo.realized["v1"]["per_horizon"]["1"]["n"], 2)

    def test_degradation_returns_exit_one(self):
        klines = _klines({"AAAUSDT": [100.0 * 1.1**i for i in range(6)]})
        predictions = []
        for version, run_day in (("v1", "2026-08-01"), ("v2", "2026-08-02")):
            for day in range(2, 5):
                origin = 100.0 * 1.1 ** (day - 2)  # close da véspera do target
                predictions.append(
                    _prediction(
                        "AAAUSDT",
                        f"2026-08-0{day}",
                        origin,
                        -0.1,  # direção errada consistentemente
                        version=version,
                        run_at=f"{run_day}T00:10:00+00:00",
                    )
                )
        exit_code = run_evaluate(
            klines_repo=_StubKlinesRepo(klines),
            forecast_repo=_StubForecastRepo(predictions),
            config=_evaluate_config(),
            now=pd.Timestamp("2026-08-10", tz="UTC"),
        )
        self.assertEqual(exit_code, 1)

    def test_no_scoreable_predictions_is_a_quiet_success(self):
        exit_code = run_evaluate(
            klines_repo=_StubKlinesRepo(_klines({"AAAUSDT": [100.0]})),
            forecast_repo=_StubForecastRepo([]),
            config=_evaluate_config(),
            now=pd.Timestamp("2026-08-10", tz="UTC"),
        )
        self.assertEqual(exit_code, 0)


def _evaluate_config():
    from tests.ml.synthetic import ml_config

    config = ml_config(min_history_days=10)
    return config.model_copy(update={"monitoring": _CONFIG})


if __name__ == "__main__":
    unittest.main()
