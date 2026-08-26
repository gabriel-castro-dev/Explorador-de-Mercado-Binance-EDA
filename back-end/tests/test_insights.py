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
    _is_valid_reading,
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


def _service(reading_text="Texto do dia.", snapshots=None, firestore_stored=None, client=None):
    tickers = MagicMock()
    tickers.get_latest_24h_snapshots.return_value = _snapshots() if snapshots is None else snapshots
    features = MagicMock()
    features.query_features.return_value = [{"atr_14": 4.2}]

    if client is None:
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

    def test_build_context_formats_numbers_in_pt_br(self):
        """O prompt manda copiar os números como fornecidos: vírgula decimal, ponto de milhar."""
        service, _, _ = _service()
        context = service.build_context()
        self.assertIn("SYM5USDT 4,50%", context)  # (5 - 2) * 1.5
        self.assertIn("SYM0USDT 6.000.000", context)  # 1_000_000 * 6
        self.assertNotIn("4.50%", context)
        self.assertNotIn("6000000", context)

    def test_system_prompt_demands_digits_not_words(self):
        self.assertIn("algarismos", insights_service.SYSTEM_PROMPT)
        self.assertIn("8,67%", insights_service.SYSTEM_PROMPT)

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


class ReadingValidationTests(unittest.TestCase):
    """Portao contra raciocinio vazado: nada disso pode virar leitura do dia."""

    def test_accepts_a_short_portuguese_paragraph(self):
        self.assertTrue(
            _is_valid_reading(
                "O mercado subiu de forma ampla nas ultimas 24 horas e o volume "
                "acompanhou os pares principais."
            )
        )

    def test_rejects_leaked_reasoning_block(self):
        self.assertFalse(_is_valid_reading("<think>ok, o usuario quer isso</think>"))

    def test_rejects_english_chain_of_thought(self):
        self.assertFalse(
            _is_valid_reading(
                "We need to write a single paragraph in Portuguese. The user gave us "
                "the numbers, so let's start with the breadth of the move."
            )
        )

    def test_rejects_text_longer_than_the_budget(self):
        self.assertFalse(_is_valid_reading("O mercado de cripto subiu de novo. " * 40))

    def test_thousands_separators_do_not_count_as_sentences(self):
        """Regressão: '38.407.882' fazia 4 frases valerem 8 e a leitura era rejeitada."""
        text = (
            "O painel monitora 200 ativos e nas últimas 24 horas 96 subiram enquanto 104 caíram. "
            "As maiores variações foram BMTUSDT com 61,97% de alta e SCRTUSDT com 21,88% de queda. "
            "Os maiores volumes em USDT ficaram com PUMPUSDT em 38.407.882 e PEPEUSDT em 37.751.517. "
            "A maior volatilidade apareceu em HEMIUSDT com 21,92% e PLUMEUSDT com 8,67%."
        )
        self.assertTrue(_is_valid_reading(text))

    def test_rejects_more_than_six_sentences(self):
        self.assertFalse(_is_valid_reading("O mercado de cripto nao parou. " * 7))


class LlmGatewayRequestTests(unittest.TestCase):
    """Corpo enviado e leitura da resposta (sem rede: httpx.post e fake)."""

    @staticmethod
    def _response(content, finish_reason="stop", extra_message=None):
        message = {"content": content}
        if extra_message:
            message.update(extra_message)
        response = MagicMock()
        response.json.return_value = {
            "choices": [{"finish_reason": finish_reason, "message": message}]
        }
        return response

    def test_body_carries_the_generous_token_budget(self):
        """O orçamento folgado é o que impede o modelo de gastar tudo pensando."""
        attempt = GatewayAttempt(provider="openrouter", api_key="k", model="nvidia/nemotron:free")
        with patch(
            "app.clients.llm_gateway.httpx.post", return_value=self._response("Texto.")
        ) as post:
            LlmGatewayClient().complete([attempt], system="s", user="u")
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 2500)

    def test_no_gateway_receives_the_reasoning_field(self):
        """Medido em 2026-08-24: com "reasoning" no corpo o nemotron devolve 502."""
        for provider, model in (
            ("openrouter", "nvidia/nemotron:free"),
            ("opencode-zen", "deepseek-v4-flash-free"),
        ):
            with self.subTest(provider=provider):
                attempt = GatewayAttempt(provider=provider, api_key="k", model=model)
                with patch(
                    "app.clients.llm_gateway.httpx.post", return_value=self._response("Texto.")
                ) as post:
                    LlmGatewayClient().complete([attempt], system="s", user="u")
                self.assertNotIn("reasoning", post.call_args.kwargs["json"])

    def test_upstream_error_in_a_200_body_is_reported_and_advances_the_chain(self):
        """O OpenRouter devolve falha do provedor como 200 com "error" no corpo."""
        attempts = [
            GatewayAttempt(provider="openrouter", api_key="k", model="nvidia/nemotron:free"),
            GatewayAttempt(provider="opencode-zen", api_key="k2", model="nemotron-3-ultra-free"),
        ]
        upstream = MagicMock()
        upstream.json.return_value = {
            "error": {"message": "Upstream error from Nvidia: Internal server error", "code": 502}
        }
        with patch(
            "app.clients.llm_gateway.httpx.post",
            side_effect=[upstream, self._response("O mercado subiu hoje.")],
        ):
            with self.assertLogs("app.clients.llm_gateway", level="WARNING") as logs:
                text, model = LlmGatewayClient().complete(attempts, system="s", user="u")
        self.assertEqual(text, "O mercado subiu hoje.")
        self.assertEqual(model, "opencode-zen/nemotron-3-ultra-free")
        self.assertIn("Upstream error from Nvidia", "".join(logs.output))

    def test_truncated_completion_advances_the_chain(self):
        attempts = [
            GatewayAttempt(provider="opencode-zen", api_key="k", model="deepseek-v4-flash-free"),
            GatewayAttempt(provider="openrouter", api_key="k2", model="nvidia/nemotron:free"),
        ]
        responses = [
            self._response(
                "We need to write the reading in Portuguese. The user gave numbers, so",
                finish_reason="length",
            ),
            self._response("O mercado de cripto subiu com volume forte."),
        ]
        with patch("app.clients.llm_gateway.httpx.post", side_effect=responses):
            text, model = LlmGatewayClient().complete(attempts, system="s", user="u")
        self.assertEqual(text, "O mercado de cripto subiu com volume forte.")
        self.assertEqual(model, "openrouter/nvidia/nemotron:free")

    def test_think_block_is_stripped_and_only_the_paragraph_survives(self):
        attempt = GatewayAttempt(provider="openrouter", api_key="k", model="nvidia/nemotron:free")
        content = "<think>Okay, the user wants five sentences.</think>\nO mercado subiu hoje."
        with patch("app.clients.llm_gateway.httpx.post", return_value=self._response(content)):
            text, _ = LlmGatewayClient().complete([attempt], system="s", user="u")
        self.assertEqual(text, "O mercado subiu hoje.")

    def test_content_with_only_reasoning_counts_as_empty(self):
        attempt = GatewayAttempt(provider="openrouter", api_key="k", model="nvidia/nemotron:free")
        response = self._response(
            "<think>Pensando alto.</think>", extra_message={"reasoning": "Pensando alto."}
        )
        with patch("app.clients.llm_gateway.httpx.post", return_value=response):
            with self.assertRaises(LlmGatewayError):
                LlmGatewayClient().complete([attempt], system="s", user="u")

    def test_validator_rejection_advances_the_chain(self):
        attempts = [
            GatewayAttempt(provider="opencode-zen", api_key="k", model="deepseek-v4-flash-free"),
            GatewayAttempt(provider="openrouter", api_key="k2", model="nvidia/nemotron:free"),
        ]
        responses = [self._response("recusado"), self._response("aceito")]
        with patch("app.clients.llm_gateway.httpx.post", side_effect=responses):
            text, model = LlmGatewayClient().complete(
                attempts, system="s", user="u", validator=lambda t: t == "aceito"
            )
        self.assertEqual(text, "aceito")
        self.assertEqual(model, "openrouter/nvidia/nemotron:free")


class InvalidReadingIsNeverCachedTests(unittest.TestCase):
    def setUp(self):
        self._env_patch = patch.dict(os.environ, _ENV)
        self._env_patch.start()
        get_settings.cache_clear()
        insights_service._cache.clear()

    def tearDown(self):
        self._env_patch.stop()
        get_settings.cache_clear()
        insights_service._cache.clear()

    def test_reasoning_in_every_attempt_leaves_nothing_stored(self):
        service, _, document = _service(client=LlmGatewayClient())
        leaked = "We need to summarize the numbers for the user, so the first sentence"
        with patch.object(LlmGatewayClient, "_complete_once", return_value=leaked):
            with self.assertRaises(InsightsUnavailableError):
                service.get_daily_reading()
        document.set.assert_not_called()
        self.assertEqual(insights_service._cache, {})


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
