"""ForecastMetricsOut aceita exatamente o que o job grava em model_metrics.

O contrato da API é construído a partir do registro de ``build_metrics_record``
(o mesmo que vai para o jsonb) — qualquer drift entre gravação e leitura quebra
aqui, offline, antes de chegar ao dashboard.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from app.ml.config import load_ml_config
from app.ml.inference import build_metrics_record
from app.ml.models.baselines import DriftBaseline, NaiveZeroReturn
from app.ml.training import run_training
from app.schemas.forecast import MIN_CONFIDENCE_SAMPLES, ForecastMetricsOut
from tests.ml.synthetic import make_drift_market, ml_config

_RUN_AT = pd.Timestamp("2026-08-23T00:10:00", tz="UTC")


def _record(published_fallback: bool = False) -> dict:
    features, klines = make_drift_market({"AAAUSDT": 0.01, "BBBUSDT": -0.01})
    outcome = run_training(
        features,
        klines,
        ml_config(min_history_days=10),
        git_sha="abc1234def",
        run_date=_RUN_AT,
        factories={"naive": NaiveZeroReturn, "drift": DriftBaseline},
    )
    record = build_metrics_record(outcome, _RUN_AT, "abc1234def", published_fallback)
    # Ida e volta pelo JSON: é assim que a linha chega do PostgREST.
    return json.loads(json.dumps(record))


class ForecastMetricsOutTests(unittest.TestCase):
    def test_accepts_the_record_the_job_writes(self):
        record = _record()
        out = ForecastMetricsOut.from_record(record)
        self.assertEqual(out.model_version, "20260823-abc1234-drift")
        self.assertEqual(out.model_type, "drift")
        self.assertFalse(out.is_fallback)
        self.assertEqual(out.git_sha, "abc1234def")
        self.assertTrue(out.gate.passed)
        self.assertIn("y_1", out.per_horizon)
        self.assertEqual(len(out.per_fold_skill_h1), 2)
        self.assertIsNone(out.realized_metrics)
        # Renomeação na borda: MAE é log-retorno e o nome diz isso.
        h1 = out.per_horizon["y_1"]
        self.assertAlmostEqual(h1.mae_log_return, record["metrics"]["per_horizon"]["y_1"]["mae"])
        self.assertIsInstance(h1.n, int)
        self.assertAlmostEqual(out.baseline_mae_log_return["y_1"], record["baseline_mae"]["y_1"])

    def test_confidence_is_rounded_direction_accuracy_percent(self):
        record = _record()
        # Mercado sintético: validação cobre 20 dias por símbolo → abaixo do piso.
        for symbol, item in record["metrics"]["per_symbol"].items():
            item["n"] = float(MIN_CONFIDENCE_SAMPLES)
            item["dir_acc"] = 0.577 if symbol == "AAAUSDT" else 0.5
        out = ForecastMetricsOut.from_record(record)
        self.assertEqual(out.per_symbol["AAAUSDT"].confidence, 58)
        self.assertEqual(out.per_symbol["BBBUSDT"].confidence, 50)

    def test_confidence_is_null_below_the_sample_floor(self):
        record = _record()
        record["metrics"]["per_symbol"]["AAAUSDT"]["n"] = float(MIN_CONFIDENCE_SAMPLES - 1)
        record["metrics"]["per_symbol"]["AAAUSDT"]["dir_acc"] = 0.9
        out = ForecastMetricsOut.from_record(record)
        self.assertIsNone(out.per_symbol["AAAUSDT"].confidence)

    def test_confidence_is_null_when_direction_accuracy_is_undefined(self):
        record = _record()
        record["metrics"]["per_symbol"]["AAAUSDT"]["n"] = float(MIN_CONFIDENCE_SAMPLES)
        record["metrics"]["per_symbol"]["AAAUSDT"]["dir_acc"] = None  # só retornos zero
        out = ForecastMetricsOut.from_record(record)
        self.assertIsNone(out.per_symbol["AAAUSDT"].dir_acc)
        self.assertIsNone(out.per_symbol["AAAUSDT"].confidence)

    def test_fallback_record_is_flagged(self):
        out = ForecastMetricsOut.from_record(_record(published_fallback=True))
        self.assertTrue(out.is_fallback)
        self.assertEqual(out.model_type, "naive-fallback")
        self.assertEqual(out.skill_score_h1, 0.0)
        self.assertEqual(out.per_fold_skill_h1, [])

    def test_realized_metrics_round_trip_from_evaluate_payload(self):
        record = _record()
        record["realized_metrics"] = {
            "computed_at": "2026-08-30T02:00:00+00:00",
            "n_rows": 32,
            "is_degenerate": False,
            "per_horizon": {"1": {"mae": 0.02, "naive_mae": 0.021, "skill": 0.0476, "n": 16}},
        }
        out = ForecastMetricsOut.from_record(record)
        realized = out.realized_metrics
        self.assertEqual(realized.n_rows, 32)
        self.assertAlmostEqual(realized.per_horizon["1"].mae_log_return, 0.02)
        self.assertAlmostEqual(realized.per_horizon["1"].naive_mae_log_return, 0.021)
        self.assertEqual(realized.per_horizon["1"].n, 16)

    def test_confidence_floor_matches_training_history_floor(self):
        # Uma definição só: o piso da confiança é o mesmo piso de histórico do treino.
        self.assertEqual(MIN_CONFIDENCE_SAMPLES, load_ml_config().dataset.min_history_days)


if __name__ == "__main__":
    unittest.main()
