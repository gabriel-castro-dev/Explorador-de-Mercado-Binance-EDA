"""Offline tests for the daily reading (LLM em cadeia de gateways, cache por dia UTC).

No network: the gateway client and Firestore are faked; repositories are
plain mocks. The FastAPI layer is exercised through dependency overrides,
mirroring tests/test_preferences.py.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.auth.verifier import UserClaims
from app.clients.llm_gateway import GatewayAttempt, LlmGatewayClient, LlmGatewayError
from app.schemas.insights import DailyReadingOut
from app.services import insights_service
from app.services.insights_service import (
    DISCLAIMER,
    InsightsService,
    InsightsUnavailableError,
    build_attempts,
)
from config import get_settings

_ENV = {
    "SUPABASE_URL": "https://test-project.supabase.co",
    "SUPABASE_KEY": "service-role-test",
    "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    "BINANCE_API_KEY": "x",
    "BINANCE_API_SECRET": "x",
    "FIREBASE_CREDENTIALS_PATH": "",
    "FIREBASE_CREDENTIALS_JSON": "",
    "OPENCODE_ZEN_API_KEY": "zen-test-key",
    "OPENROUTER_API_KEY": "or-test-key",
}

_CLAIMS = UserClaims(
    sub="8f8f0000-0000-0000-0000-000000000001", role="authenticated", email="user@example.com"
)


def _snapshots(n=6):
    rows = []
    for i in range(n):
        rows.append(
            {
                "symbol": f"SYM{i}USDT",
                "last_price": 100.0 + i,
                "price_change_percent": (i - 2) * 1.5,  # mistura de altas e baixas
                "quote_volume": 1_000_000.0 * (n - i),
            }
        )
    return rows


def _service(reading_text="Texto do dia.", snapshots=None, firestore_stored=None):
    tickers = MagicMock()
    tickers.get_latest_24h_snapshots.return_value = _snapshots() if snapshots is None else snapshots
    features = MagicMock()
    features.query_features.return_value = [{"atr_14": 4.2}]

    client = MagicMock()
    client.complete.return_value = (reading_text, "opencode-zen/deepseek-v4-flash-free")

    snapshot = MagicMock()
    snapshot.exists = firestore_stored is not None
    snapshot.to_dict.return_value = firestore_stored
    document = MagicMock()
    document.get.return_value = snapshot
    collection = MagicMock()
    collection.document.return_value = document
    firestore = MagicMock()
    firestore.collection.return_value = collection

    service = InsightsService(
        tickers_repo=tickers,
        features_repo=features,
        client=client,
        firestore_client=firestore,
    )
    return service, client, document


class InsightsServiceTests(unittest.TestCase):
    def setUp(self):
        self._env_patch = patch.dict(os.environ, _ENV)
        self._env_patch.start()
        get_settings.cache_clear()
        insights_service._cache.clear()

    def tearDown(self):
        self._env_patch.stop()
        get_settings.cache_clear()
        insights_service._cache.clear()

    def test_build_context_translates_the_snapshot_into_numbers_only(self):
        service, _, _ = _service()
        context = service.build_context()
        self.assertIn("Ativos acompanhados: 6", context)
        self.assertIn("Subiram nas últimas 24 horas: 3", context)
        self.assertIn("Maiores variações de preço", context)
        self.assertIn("Maiores volumes em 24 horas", context)
        self.assertIn("Maior volatilidade", context)

    def test_build_context_requires_a_minimum_of_market_data(self):
        service, _, _ = _service(snapshots=_snapshots(2))
        with self.assertRaises(InsightsUnavailableError):
            service.build_context()

    def test_generates_stores_and_caches_the_reading(self):
        service, client, document = _service(reading_text="Mercado comprador hoje.")
        reading = service.get_daily_reading()
        self.assertEqual(reading.text, "Mercado comprador hoje.")
        self.assertEqual(reading.disclaimer, DISCLAIMER)
        self.assertEqual(reading.model, "opencode-zen/deepseek-v4-flash-free")
        document.set.assert_called_once()
        # Segunda chamada: cache de processo, sem novo LLM.
        again = service.get_daily_reading()
        self.assertIs(again, reading)
        client.complete.assert_called_once()

    def test_fallback_chain_zen_first_then_openrouter(self):
        """Ordem decidida com o usuário: Zen deepseek free → Zen nemotron → OpenRouter."""
        service, client, _ = _service()
        service.get_daily_reading()
        attempts = client.complete.call_args.args[0]
        self.assertEqual(
            [(a.provider, a.model) for a in attempts],
            [
                ("opencode-zen", "deepseek-v4-flash-free"),
                ("opencode-zen", "nemotron-3-ultra-free"),
                ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"),
            ],
        )

    def test_build_attempts_skips_gateways_without_a_key(self):
        with patch.dict(os.environ, {"OPENCODE_ZEN_API_KEY": ""}):
            get_settings.cache_clear()
            attempts = build_attempts(get_settings())
        get_settings.cache_clear()
        self.assertEqual(
            [(a.provider, a.model) for a in attempts],
            [("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free")],
        )

    def test_firestore_document_wins_over_generation(self):
        stored = DailyReadingOut(
            date=insights_service._today_utc(),
            generated_at="2026-08-23T09:00:00Z",
            model="opencode-zen/deepseek-v4-flash-free",
            text="Leitura já gravada.",
            disclaimer=DISCLAIMER,
        ).model_dump(mode="json")
        service, client, _ = _service(firestore_stored=stored)
        reading = service.get_daily_reading()
        self.assertEqual(reading.text, "Leitura já gravada.")
        client.complete.assert_not_called()

    def test_gateway_chain_failure_becomes_unavailable(self):
        service, client, _ = _service()
        client.complete.side_effect = LlmGatewayError("todas as tentativas falharam")
        with self.assertRaises(InsightsUnavailableError):
            service.get_daily_reading()

    def test_client_falls_through_the_chain_and_reports_the_winner(self):
        """O client real tenta na ordem e devolve provider/model de quem respondeu."""
        client = LlmGatewayClient()
        attempts = [
            GatewayAttempt(provider="opencode-zen", api_key="k", model="deepseek-v4-flash-free"),
            GatewayAttempt(provider="opencode-zen", api_key="k", model="nemotron-3-ultra-free"),
            GatewayAttempt(provider="openrouter", api_key="k2", model="nvidia/nemotron:free"),
        ]
        calls = []

        def fake_once(attempt, **_kwargs):
            calls.append((attempt.provider, attempt.model))
            if len(calls) < 3:
                raise LlmGatewayError("indisponível")
            return "Texto final."

        with patch.object(LlmGatewayClient, "_complete_once", side_effect=fake_once):
            text, model = client.complete(attempts, system="s", user="u")
        self.assertEqual(text, "Texto final.")
        self.assertEqual(model, "openrouter/nvidia/nemotron:free")
        self.assertEqual(len(calls), 3)

    def test_client_with_empty_chain_raises(self):
        with self.assertRaises(LlmGatewayError):
            LlmGatewayClient().complete([], system="s", user="u")


class InsightsApiTests(unittest.TestCase):
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

    def setUp(self):
        insights_service._cache.clear()

    def tearDown(self):
        self.app.dependency_overrides.clear()
        insights_service._cache.clear()

    def _client(self):
        from app.controllers.deps import get_claims, get_features_repo, get_tickers_repo

        self.app.dependency_overrides[get_claims] = lambda: _CLAIMS
        self.app.dependency_overrides[get_tickers_repo] = lambda: MagicMock()
        self.app.dependency_overrides[get_features_repo] = lambda: MagicMock()
        return TestClient(self.app)

    def test_requires_a_token(self):
        response = TestClient(self.app).get("/api/v1/insights/daily-reading")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")

    def test_returns_the_reading_with_the_fixed_disclaimer(self):
        reading = DailyReadingOut(
            date="2026-08-23",
            generated_at="2026-08-23T09:00:00Z",
            model="deepseek/deepseek-v4-flash",
            text="Leitura do dia.",
            disclaimer=DISCLAIMER,
        )
        with patch.object(InsightsService, "get_daily_reading", return_value=reading):
            response = self._client().get("/api/v1/insights/daily-reading")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["text"], "Leitura do dia.")
        self.assertEqual(body["disclaimer"], DISCLAIMER)

    def test_maps_unavailability_to_503(self):
        with patch.object(
            InsightsService,
            "get_daily_reading",
            side_effect=InsightsUnavailableError("sem cache e sem geração"),
        ):
            response = self._client().get("/api/v1/insights/daily-reading")
        self.assertEqual(response.status_code, 503)
        self.assertIn("indisponível", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
