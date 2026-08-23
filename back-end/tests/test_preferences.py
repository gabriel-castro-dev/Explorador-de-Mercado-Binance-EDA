"""Offline tests for the user preferences surface (Firestore-backed).

No Firebase credentials and no network: the Firestore client is faked and
the repository is injected through the FastAPI dependency override.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.auth.verifier import UserClaims
from app.repositories.preferences_repository import PreferencesRepository
from config import Settings, get_settings

_ENV = {
    "SUPABASE_URL": "https://test-project.supabase.co",
    "SUPABASE_KEY": "service-role-test",
    "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    "BINANCE_API_KEY": "x",
    "BINANCE_API_SECRET": "x",
    # Vazias de proposito: qualquer dependencia do Firebase que escape de um
    # override falha aqui em vez de conectar de verdade (o CI nao tem .env,
    # e a suite tem que se comportar igual na maquina de quem desenvolve).
    "FIREBASE_CREDENTIALS_PATH": "",
    "FIREBASE_CREDENTIALS_JSON": "",
}

_UID = "8f8f0000-0000-0000-0000-000000000001"
_CLAIMS = UserClaims(sub=_UID, role="authenticated", email="user@example.com")

_STORED = {
    "user_id": _UID,
    "display_name": "Gabriel Castro",
    "phone": "+5511981234567",
    "notifications": {
        "enabled": True,
        "channel": "email",
        "topics": {
            "forecast_gap": True,
            "volume_movers": True,
            "volatility": False,
            "model_runs": False,
        },
    },
    "chart": {"hollow_up_candles": True},
    "schema_version": 1,
}


def _fake_firestore(stored=None):
    """Firestore double: client.collection().document().get()/set()."""
    snapshot = MagicMock()
    snapshot.exists = stored is not None
    snapshot.to_dict.return_value = stored
    document = MagicMock()
    document.get.return_value = snapshot
    collection = MagicMock()
    collection.document.return_value = document
    client = MagicMock()
    client.collection.return_value = collection
    return client, collection, document


class PreferencesRepositoryTests(unittest.TestCase):
    def test_get_returns_none_when_the_user_never_saved(self):
        client, collection, _ = _fake_firestore(stored=None)
        repo = PreferencesRepository(firestore_client=client, collection="user_preferences")
        self.assertIsNone(repo.get(_UID))
        client.collection.assert_called_with("user_preferences")
        collection.document.assert_called_with(_UID)

    def test_get_returns_the_stored_document(self):
        client, _, _ = _fake_firestore(stored=_STORED)
        repo = PreferencesRepository(firestore_client=client, collection="user_preferences")
        self.assertEqual(repo.get(_UID), _STORED)

    def test_upsert_stamps_owner_version_and_timestamps_server_side(self):
        from google.cloud.firestore_v1 import SERVER_TIMESTAMP

        client, _, document = _fake_firestore(stored=None)
        repo = PreferencesRepository(firestore_client=client, collection="user_preferences")
        repo.upsert(_UID, {"display_name": "Gabriel", "user_id": "spoofed-by-client"})
        payload = document.set.call_args.args[0]
        self.assertEqual(payload["user_id"], _UID)  # server-side wins over any client value
        self.assertEqual(payload["schema_version"], PreferencesRepository.SCHEMA_VERSION)
        self.assertIs(payload["updated_at"], SERVER_TIMESTAMP)
        self.assertIs(payload["created_at"], SERVER_TIMESTAMP)  # first write only
        self.assertTrue(document.set.call_args.kwargs["merge"])

    def test_upsert_does_not_reset_created_at_on_an_existing_document(self):
        client, _, document = _fake_firestore(stored=_STORED)
        repo = PreferencesRepository(firestore_client=client, collection="user_preferences")
        repo.upsert(_UID, {"display_name": "Gabriel"})
        self.assertNotIn("created_at", document.set.call_args.args[0])


def _bare_settings(**overrides):
    return Settings(
        SUPABASE_URL="x",
        SUPABASE_KEY="x",
        BINANCE_API_KEY="x",
        BINANCE_API_SECRET="x",
        _env_file=None,
        **overrides,
    )


class FirebaseCredentialsTests(unittest.TestCase):
    def test_missing_credentials_raise_an_explicit_error(self):
        from app.clients.firebase.client import FirebaseCredentialsError, _build_credentials

        with self.assertRaises(FirebaseCredentialsError):
            _build_credentials(_bare_settings())

    def test_injected_settings_are_accepted_by_the_seam(self):
        """Settings is unhashable: it must not sit in an lru_cache key."""
        from app.clients.firebase import client as fb

        settings = _bare_settings()
        with self.assertRaises(TypeError):
            hash(settings)  # confirma a premissa do teste
        with patch.object(fb, "_initialize") as initialize, patch.object(fb, "firestore"):
            fb.build_firestore(settings)
        initialize.assert_called_once_with(settings)

    def test_concurrent_first_calls_initialize_the_app_only_once(self):
        """lru_cache não serializa cache miss concorrente; o lock serializa."""
        import threading

        from app.clients.firebase import client as fb

        apps = {}
        calls = []
        barrier = threading.Barrier(8)

        def _initialize_app(_credentials):
            calls.append(1)
            if apps:  # reproduz o ValueError real do firebase_admin
                raise ValueError("The default Firebase app already exists.")
            apps["[DEFAULT]"] = object()

        errors = []

        def _worker():
            barrier.wait()
            try:
                fb._initialize(_bare_settings())
            except Exception as error:  # noqa: BLE001
                errors.append(error)

        with (
            patch.object(fb.firebase_admin, "_apps", apps),
            patch.object(fb.firebase_admin, "initialize_app", _initialize_app),
            patch.object(fb, "_build_credentials", return_value=object()),
        ):
            threads = [threading.Thread(target=_worker) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(calls), 1)


class PreferencesApiTests(unittest.TestCase):
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

    def _client(self, repo):
        from app.controllers.deps import get_claims, get_firebase_identity, get_preferences_repo

        self.app.dependency_overrides[get_claims] = lambda: _CLAIMS
        self.app.dependency_overrides[get_preferences_repo] = lambda: repo
        # GET /preferences provisiona a conta espelho: sem este override o
        # teste construiria o servico real e sairia para a rede.
        self.app.dependency_overrides[get_firebase_identity] = lambda: MagicMock()
        return TestClient(self.app)

    def test_requires_a_token(self):
        client = TestClient(self.app)
        for method in ("GET", "PUT"):
            with self.subTest(method=method):
                response = client.request(method, "/api/v1/preferences", json={})
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")

    def test_get_returns_defaults_when_nothing_was_saved(self):
        repo = MagicMock()
        repo.get.return_value = None
        response = self._client(repo).get("/api/v1/preferences")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["display_name"])
        self.assertFalse(body["notifications"]["enabled"])
        self.assertEqual(body["notifications"]["channel"], "email")
        self.assertTrue(body["chart"]["hollow_up_candles"])  # vazada por padrao (design v2)
        self.assertEqual(body["email"], "user@example.com")  # do token, nao do Firestore
        repo.get.assert_called_once_with(_UID)

    def test_get_returns_the_stored_preferences(self):
        repo = MagicMock()
        repo.get.return_value = _STORED
        body = self._client(repo).get("/api/v1/preferences").json()
        self.assertEqual(body["display_name"], "Gabriel Castro")
        self.assertEqual(body["phone"], "+5511981234567")
        self.assertTrue(body["notifications"]["topics"]["forecast_gap"])
        self.assertTrue(body["chart"]["hollow_up_candles"])

    def test_put_persists_under_the_token_owner(self):
        repo = MagicMock()
        repo.upsert.return_value = _STORED
        payload = {
            "display_name": "Gabriel Castro",
            "phone": "+5511981234567",
            "notifications": {
                "enabled": True,
                "channel": "email",
                "topics": {
                    "forecast_gap": True,
                    "volume_movers": True,
                    "volatility": False,
                    "model_runs": False,
                },
            },
            "chart": {"hollow_up_candles": True},
        }
        response = self._client(repo).put("/api/v1/preferences", json=payload)
        self.assertEqual(response.status_code, 200)
        uid, data = repo.upsert.call_args.args
        self.assertEqual(uid, _UID)
        self.assertEqual(data["display_name"], "Gabriel Castro")
        self.assertNotIn("email", data)  # e-mail nunca vai para o Firestore
        self.assertNotIn("user_id", data)

    def test_put_accepts_an_empty_body_as_defaults(self):
        repo = MagicMock()
        repo.upsert.return_value = {}
        response = self._client(repo).put("/api/v1/preferences", json={})
        self.assertEqual(response.status_code, 200)

    def test_put_rejects_smuggled_ownership_and_invalid_values(self):
        repo = MagicMock()
        client = self._client(repo)
        cases = (
            ("user_id", {"user_id": "another-user"}),
            ("email", {"email": "attacker@example.com"}),
            ("phone_sem_ddi", {"phone": "11981234567"}),
            ("canal_invalido", {"notifications": {"channel": "telegram"}}),
            ("topico_desconhecido", {"notifications": {"topics": {"pump_alerts": True}}}),
        )
        for case, payload in cases:
            with self.subTest(case=case):
                response = client.put("/api/v1/preferences", json=payload)
                self.assertEqual(response.status_code, 422)
        repo.upsert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
