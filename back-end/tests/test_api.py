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


if __name__ == "__main__":
    unittest.main()
