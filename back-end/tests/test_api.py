"""Offline tests for the API surface (TestClient + dependency overrides)."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.auth.verifier import UserClaims
from config import get_settings

_ENV = {
    "SUPABASE_URL": "https://test-project.supabase.co",
    "SUPABASE_KEY": "service-role-test",
    "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    "BINANCE_API_KEY": "x",
    "BINANCE_API_SECRET": "x",
}

_CLAIMS = UserClaims(sub="8f8f0000-0000-0000-0000-000000000001", role="authenticated")

_KLINE_ROW = {
    "id": 1,
    "symbol": "BTCUSDT",
    "open_time": "2026-08-19T00:00:00+00:00",
    "open": 1.0,
    "high": 2.0,
    "low": 0.5,
    "close": 1.5,
    "volume": 10.0,
}


def _chainable(rows):
    builder = MagicMock()
    for method in ("select", "eq", "gte", "lte", "order", "limit"):
        getattr(builder, method).return_value = builder
    builder.execute.return_value.data = rows
    supabase = MagicMock()
    supabase.table.return_value = builder
    return supabase, builder


class ApiTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._env_patch = patch.dict(os.environ, _ENV)
        cls._env_patch.start()
        get_settings.cache_clear()
        from app.main import create_app

        cls.app = create_app()

    @classmethod
    def tearDownClass(cls):
        cls._env_patch.stop()
        get_settings.cache_clear()

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _authed_client(self, rows):
        from app.controllers.deps import get_claims, get_rls_supabase

        supabase, builder = _chainable(rows)
        self.app.dependency_overrides[get_claims] = lambda: _CLAIMS
        self.app.dependency_overrides[get_rls_supabase] = lambda: supabase
        return TestClient(self.app), supabase, builder


class HealthTests(ApiTestBase):
    def test_health_is_public(self):
        client = TestClient(self.app)
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class AuthGateTests(ApiTestBase):
    def test_endpoints_require_a_token(self):
        client = TestClient(self.app)
        for path in (
            "/api/v1/symbols",
            "/api/v1/klines/1h?symbol=BTCUSDT",
            "/api/v1/features/1h?symbol=BTCUSDT",
            "/api/v1/tickers/24h",
        ):
            response = client.get(path)
            self.assertEqual(response.status_code, 401, path)
            self.assertEqual(response.headers["WWW-Authenticate"], "Bearer", path)

    def test_garbage_token_is_rejected(self):
        client = TestClient(self.app)
        response = client.get("/api/v1/symbols", headers={"Authorization": "Bearer not-a-jwt"})
        self.assertEqual(response.status_code, 401)


class KlinesEndpointTests(ApiTestBase):
    def test_happy_path_filters_and_shape(self):
        client, supabase, builder = self._authed_client([_KLINE_ROW])
        response = client.get("/api/v1/klines/1h?symbol=btcusdt&limit=5")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["symbol"], "BTCUSDT")
        self.assertNotIn("id", body[0])  # extra="ignore" filtra o surrogate id
        supabase.table.assert_called_once_with("klines_1h")
        builder.eq.assert_called_once_with("symbol", "BTCUSDT")  # upper() aplicado
        builder.limit.assert_called_once_with(5)

    def test_invalid_timeframe_is_422(self):
        client, _, _ = self._authed_client([])
        self.assertEqual(client.get("/api/v1/klines/2h?symbol=BTCUSDT").status_code, 422)

    def test_missing_symbol_is_422(self):
        client, _, _ = self._authed_client([])
        self.assertEqual(client.get("/api/v1/klines/1h").status_code, 422)

    def test_empty_history_is_200_empty_list(self):
        client, _, _ = self._authed_client([])
        response = client.get("/api/v1/klines/1d?symbol=NOHISTORY")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class FeaturesEndpointTests(ApiTestBase):
    def test_24h_alias_reads_features_24h(self):
        row = {"symbol": "BTCUSDT", "timestamp": "2026-08-19T00:00:00+00:00", "rsi_14": 55.5}
        client, supabase, _ = self._authed_client([row])
        response = client.get("/api/v1/features/24h?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["rsi_14"], 55.5)
        supabase.table.assert_called_once_with("features_24h")


class SymbolsEndpointTests(ApiTestBase):
    def test_lists_symbols(self):
        client, _, _ = self._authed_client([{"symbol": "ADAUSDT"}])
        response = client.get("/api/v1/symbols")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"symbol": "ADAUSDT", "created_at": None}])


class TickersEndpointTests(ApiTestBase):
    def test_single_symbol_snapshot(self):
        row = {"symbol": "BTCUSDT", "open_time": "2026-08-19 00:00:00", "last_price": 50000.0}
        client, _, builder = self._authed_client([row])
        response = client.get("/api/v1/tickers/24h?symbol=btcusdt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["last_price"], 50000.0)
        builder.eq.assert_called_once_with("symbol", "BTCUSDT")


_FORECAST_ROW = {
    "id": 7,
    "symbol": "BTCUSDT",
    "model_version": "20260823-abc1234-gbm",
    # Não é coluna de `predictions`: o fake serve a mesma linha à consulta de
    # model_metrics.model_type (testes com side_effect cobrem o caminho real).
    "model_type": "gbm",
    "run_at": "2026-08-23T00:10:00+00:00",
    "target_time": "2026-08-24T00:00:00+00:00",
    "horizon_days": 1,
    "predicted_close": 114000.5,
    "predicted_log_return": 0.0043,
    "pred_lower": 111500.0,
    "pred_upper": 116400.0,
    "is_fallback": False,
    "created_at": "2026-08-23T00:10:05+00:00",
}


class ForecastsEndpointTests(ApiTestBase):
    def test_requires_a_token(self):
        client = TestClient(self.app)
        response = client.get("/api/v1/forecasts")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")

    def test_happy_path_contract(self):
        client, supabase, builder = self._authed_client([_FORECAST_ROW])
        response = client.get("/api/v1/forecasts?symbol=btcusdt")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        # Contrato: rastreabilidade e estado de fallback sempre presentes.
        self.assertEqual(body[0]["model_version"], "20260823-abc1234-gbm")
        self.assertEqual(body[0]["model_type"], "gbm")
        self.assertFalse(body[0]["is_fallback"])
        self.assertEqual(body[0]["horizon_days"], 1)
        self.assertNotIn("id", body[0])  # extra="ignore" filtra o surrogate id
        tables = [call.args[0] for call in supabase.table.call_args_list]
        self.assertEqual(tables, ["predictions", "predictions", "model_metrics"])
        eq_calls = {call.args for call in builder.eq.call_args_list}
        self.assertIn(("symbol", "BTCUSDT"), eq_calls)  # upper() aplicado

    def test_curve_preserves_horizon_order(self):
        rows = [
            {
                **_FORECAST_ROW,
                "horizon_days": h,
                "target_time": f"2026-08-{23 + h:02d}T00:00:00+00:00",
            }
            for h in (1, 2, 3)
        ]
        client, _, _ = self._authed_client(rows)
        body = client.get("/api/v1/forecasts?symbol=BTCUSDT").json()
        self.assertEqual([row["horizon_days"] for row in body], [1, 2, 3])

    def test_rows_carry_the_model_type_of_their_version(self):
        client, supabase, builder = self._authed_client([_FORECAST_ROW])
        builder.execute.side_effect = [
            MagicMock(data=[{"run_at": _FORECAST_ROW["run_at"]}]),
            MagicMock(data=[_FORECAST_ROW]),
            MagicMock(data=[{"model_type": "gbm"}]),
        ]
        body = client.get("/api/v1/forecasts").json()
        self.assertEqual(body[0]["model_type"], "gbm")
        tables = [call.args[0] for call in supabase.table.call_args_list]
        self.assertEqual(tables, ["predictions", "predictions", "model_metrics"])

    def test_model_type_is_null_when_metrics_row_is_missing(self):
        client, _, builder = self._authed_client([_FORECAST_ROW])
        builder.execute.side_effect = [
            MagicMock(data=[{"run_at": _FORECAST_ROW["run_at"]}]),
            MagicMock(data=[_FORECAST_ROW]),
            MagicMock(data=[]),
        ]
        body = client.get("/api/v1/forecasts").json()
        self.assertIsNone(body[0]["model_type"])

    def test_no_forecasts_yet_is_200_empty_list(self):
        client, _, _ = self._authed_client([])
        response = client.get("/api/v1/forecasts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_invalid_symbol_length_is_422(self):
        client, _, _ = self._authed_client([])
        symbol_too_long = "A" * 21
        response = client.get(f"/api/v1/forecasts?symbol={symbol_too_long}")
        self.assertEqual(response.status_code, 422)


_METRICS_ROW = {
    "id": 3,
    "model_version": "20260823-abc1234-gbm",
    "model_type": "gbm",
    "trained_at": "2026-08-23T00:10:00+00:00",
    "train_start": "2021-05-13T00:00:00+00:00",
    "train_end": "2026-08-17T00:00:00+00:00",
    "git_sha": "abc1234def",
    "hyperparams": {
        "champion": "gbm",
        "members": ["gbm"],
        "ranking": {"gbm": 0.01, "naive": 0.0},
        "gate": {"passed": True, "reason": "Skill score 0.0100 em y_1 — publicação liberada."},
        "n_folds": 4,
    },
    "metrics": {
        "skill_score_h1": 0.01,
        "per_fold_skill_h1": [0.02, 0.0, 0.01, 0.01],
        "per_horizon": {"y_1": {"mae": 0.0258, "rmse": 0.0464, "dir_acc": 0.4995, "n": 2114.0}},
        "per_symbol": {
            "BTCUSDT": {"mae": 0.02, "dir_acc": 0.503, "n": 173.0},
            "PLUMEUSDT": {"mae": 0.05, "dir_acc": 0.5, "n": 38.0},
        },
    },
    "baseline_mae": {"y_1": 0.0258},
    "realized_metrics": None,
    "is_fallback": False,
    "created_at": "2026-08-23T00:10:05+00:00",
}


class ForecastMetricsEndpointTests(ApiTestBase):
    def test_requires_a_token(self):
        client = TestClient(self.app)
        response = client.get("/api/v1/forecasts/metrics")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")

    def test_happy_path_contract(self):
        # O mesmo fake responde às duas consultas (model_version do run e a linha
        # de model_metrics): a primeira só lê model_version.
        client, supabase, _ = self._authed_client([_METRICS_ROW])
        response = client.get("/api/v1/forecasts/metrics")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model_version"], "20260823-abc1234-gbm")
        self.assertEqual(body["model_type"], "gbm")
        self.assertTrue(body["gate"]["passed"])
        self.assertEqual(body["per_horizon"]["y_1"]["mae_log_return"], 0.0258)
        self.assertEqual(body["per_horizon"]["y_1"]["n"], 2114)
        self.assertEqual(body["baseline_mae_log_return"]["y_1"], 0.0258)
        self.assertEqual(body["per_symbol"]["BTCUSDT"]["confidence"], 50)
        self.assertIsNone(body["per_symbol"]["PLUMEUSDT"]["confidence"])  # abaixo do piso
        self.assertIsNone(body["realized_metrics"])
        self.assertNotIn("id", body)
        self.assertNotIn("hyperparams", body)
        tables = [call.args[0] for call in supabase.table.call_args_list]
        self.assertEqual(tables, ["predictions", "model_metrics"])

    def test_no_run_yet_is_200_null(self):
        client, _, _ = self._authed_client([])
        response = client.get("/api/v1/forecasts/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())


if __name__ == "__main__":
    unittest.main()
