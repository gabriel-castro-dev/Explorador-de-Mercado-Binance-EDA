"""Offline tests for the Firebase identity bridge.

No credentials and no network: the Firebase Auth module is faked and the
service is injected through the FastAPI dependency override.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.auth.verifier import UserClaims
from app.services.firebase_identity import FirebaseIdentityService
from config import get_settings

_ENV = {
    "SUPABASE_URL": "https://test-project.supabase.co",
    "SUPABASE_KEY": "service-role-test",
    "SUPABASE_PUBLISHABLE_KEY": "sb_publishable_test",
    "BINANCE_API_KEY": "x",
    "BINANCE_API_SECRET": "x",
    # Sem credencial: nenhum teste pode alcancar o Firebase de verdade.
    "FIREBASE_CREDENTIALS_PATH": "",
    "FIREBASE_CREDENTIALS_JSON": "",
}

_UID = "8f8f0000-0000-0000-0000-000000000001"
_CLAIMS = UserClaims(sub=_UID, role="authenticated", email="user@example.com")


class _UserNotFoundError(Exception):
    pass


class _EmailAlreadyExistsError(Exception):
    pass


def _fake_auth(existing=True):
    """Firebase auth double carrying the SDK's exception types."""
    auth = MagicMock()
    auth.UserNotFoundError = _UserNotFoundError
    auth.EmailAlreadyExistsError = _EmailAlreadyExistsError
    if existing:
        auth.get_user.return_value = MagicMock(uid=_UID)
    else:
        auth.get_user.side_effect = _UserNotFoundError("no such user")
    auth.create_custom_token.return_value = b"custom-token-bytes"
    return auth


class FirebaseIdentityServiceTests(unittest.TestCase):
    def test_existing_user_is_not_recreated(self):
        auth = _fake_auth(existing=True)
        created = FirebaseIdentityService(auth_module=auth).ensure_user(_UID, "user@example.com")
        self.assertFalse(created)
        auth.create_user.assert_not_called()

    def test_missing_user_is_created_without_a_password(self):
        auth = _fake_auth(existing=False)
        created = FirebaseIdentityService(auth_module=auth).ensure_user(_UID, "user@example.com")
        self.assertTrue(created)
        auth.create_user.assert_called_once_with(uid=_UID, email="user@example.com")
        # Supabase owns credentials: no password may reach Firebase.
        self.assertNotIn("password", auth.create_user.call_args.kwargs)

    def test_email_owned_by_another_uid_does_not_raise(self):
        auth = _fake_auth(existing=False)
        auth.create_user.side_effect = _EmailAlreadyExistsError("taken")
        created = FirebaseIdentityService(auth_module=auth).ensure_user(_UID, "user@example.com")
        self.assertFalse(created)

    def test_custom_token_is_decoded_to_str(self):
        auth = _fake_auth()
        token = FirebaseIdentityService(auth_module=auth).mint_custom_token(_UID)
        self.assertEqual(token, "custom-token-bytes")
        self.assertIsInstance(token, str)
        auth.create_custom_token.assert_called_once_with(_UID)


class FirebaseTokenRouteTests(unittest.TestCase):
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

    def _client(self, identity, repo=None):
        from app.controllers.deps import get_claims, get_firebase_identity, get_preferences_repo

        self.app.dependency_overrides[get_claims] = lambda: _CLAIMS
        self.app.dependency_overrides[get_firebase_identity] = lambda: identity
        if repo is not None:
            self.app.dependency_overrides[get_preferences_repo] = lambda: repo
        return TestClient(self.app)

    def test_requires_a_token(self):
        response = TestClient(self.app).post("/api/v1/auth/firebase-token")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")

    def test_token_is_minted_for_the_token_owner(self):
        identity = MagicMock()
        identity.mint_custom_token.return_value = "signed-token"
        response = self._client(identity).post("/api/v1/auth/firebase-token")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["custom_token"], "signed-token")
        identity.ensure_user.assert_called_once_with(_UID, "user@example.com")
        identity.mint_custom_token.assert_called_once_with(_UID)

    def test_preferences_provisions_the_mirror_account(self):
        identity = MagicMock()
        repo = MagicMock()
        repo.get.return_value = None
        response = self._client(identity, repo).get("/api/v1/preferences")
        self.assertEqual(response.status_code, 200)
        identity.ensure_user.assert_called_once_with(_UID, "user@example.com")

    def test_provisioning_failure_does_not_break_preferences(self):
        identity = MagicMock()
        identity.ensure_user.side_effect = RuntimeError("firebase down")
        repo = MagicMock()
        repo.get.return_value = None
        with self.assertLogs("app.controllers.preferences", level="ERROR"):
            response = self._client(identity, repo).get("/api/v1/preferences")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "user@example.com")


if __name__ == "__main__":
    unittest.main()
