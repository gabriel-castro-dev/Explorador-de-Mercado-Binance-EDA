"""ForecastRepository: upsert idempotente e leitura do run mais recente."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.repositories.forecast_repository import ForecastRepository
from tests.test_api_repositories import _chainable


def _row(symbol="BTCUSDT", horizon=1):
    return {
        "symbol": symbol,
        "model_version": "20260823-abc1234-gbm",
        "target_time": "2026-08-24T00:00:00+00:00",
        "horizon_days": horizon,
    }


class UpsertPredictionsTests(unittest.TestCase):
    def test_uses_natural_key_on_conflict(self):
        supabase, builder = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        count = repo.upsert_predictions([_row()])
        self.assertEqual(count, 1)
        supabase.table.assert_called_with("predictions")
        _, kwargs = builder.upsert.call_args
        self.assertEqual(kwargs["on_conflict"], "symbol,target_time,horizon_days,model_version")

    def test_rerun_sends_identical_payload(self):
        # Idempotência no cliente: duas rodadas idênticas → upserts idênticos;
        # o unique constraint da tabela faz o resto no servidor.
        supabase, builder = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        rows = [_row(horizon=h) for h in (1, 2)]
        repo.upsert_predictions(rows)
        repo.upsert_predictions(rows)
        first, second = builder.upsert.call_args_list
        self.assertEqual(first, second)

    def test_batches_large_payloads(self):
        supabase, builder = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        repo.upsert_predictions([_row(horizon=h) for h in range(1, 1202)])
        self.assertEqual(builder.upsert.call_count, 3)  # 500 + 500 + 201

    def test_empty_rows_do_not_touch_the_database(self):
        supabase, builder = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        self.assertEqual(repo.upsert_predictions([]), 0)
        builder.upsert.assert_not_called()


class ModelMetricsTests(unittest.TestCase):
    def test_upsert_keyed_by_model_version(self):
        supabase, builder = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        repo.upsert_model_metrics({"model_version": "20260823-abc1234-gbm"})
        supabase.table.assert_called_with("model_metrics")
        _, kwargs = builder.upsert.call_args
        self.assertEqual(kwargs["on_conflict"], "model_version")


class LatestRunPredictionsTests(unittest.TestCase):
    def test_empty_table_returns_empty_list(self):
        supabase, _ = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        self.assertEqual(repo.get_latest_run_predictions(), [])

    def test_filters_by_latest_run_and_symbol(self):
        supabase, builder = _chainable([{"run_at": "2026-08-23T00:10:00+00:00"}])
        repo = ForecastRepository(supabase=supabase)
        repo.get_latest_run_predictions(symbol="BTCUSDT")
        eq_calls = {call.args for call in builder.eq.call_args_list}
        self.assertIn(("run_at", "2026-08-23T00:10:00+00:00"), eq_calls)
        self.assertIn(("symbol", "BTCUSDT"), eq_calls)


class LatestRunMetricsTests(unittest.TestCase):
    def test_no_predictions_yet_returns_none(self):
        supabase, _ = _chainable([])
        repo = ForecastRepository(supabase=supabase)
        self.assertIsNone(repo.get_latest_run_metrics())

    def test_reads_metrics_of_the_version_that_signed_the_latest_run(self):
        # 1ª consulta: model_version do run mais recente; 2ª: linha em model_metrics.
        supabase, builder = _chainable([{"model_version": "20260823-abc1234-gbm"}])
        builder.execute.return_value.data = [{"model_version": "20260823-abc1234-gbm"}]
        repo = ForecastRepository(supabase=supabase)
        record = repo.get_latest_run_metrics()
        self.assertEqual(record["model_version"], "20260823-abc1234-gbm")
        tables = [call.args[0] for call in supabase.table.call_args_list]
        self.assertEqual(tables, ["predictions", "model_metrics"])
        builder.eq.assert_called_with("model_version", "20260823-abc1234-gbm")

    def test_latest_run_without_metrics_row_returns_none(self):
        supabase, builder = _chainable([])
        builder.execute.return_value.data = [{"model_version": "20260823-abc1234-gbm"}]
        # Segunda execução (model_metrics) devolve vazio.
        builder.execute.side_effect = [
            type("R", (), {"data": [{"model_version": "20260823-abc1234-gbm"}]})(),
            type("R", (), {"data": []})(),
        ]
        repo = ForecastRepository(supabase=supabase)
        self.assertIsNone(repo.get_latest_run_metrics())


if __name__ == "__main__":
    unittest.main()
