"""Offline tests for Supabase JWT verification (no network, no .env)."""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import jwt
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1, generate_private_key

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth.verifier import TokenError, TokenVerifier
from config import Settings

_URL = "https://test-project.supabase.co"
_ISSUER = f"{_URL}/auth/v1"
_HS_SECRET = "legacy-shared-secret"


def _settings(**overrides):
    values = dict(
        SUPABASE_URL=_URL,
        SUPABASE_KEY="x",
        BINANCE_API_KEY="x",
        BINANCE_API_SECRET="x",
        _env_file=None,
    )
    values.update(overrides)
    return Settings(**values)


def _claims(**overrides):
    now = int(time.time())
    payload = {
        "sub": "8f8f0000-0000-0000-0000-000000000001",
        "role": "authenticated",
        "aud": "authenticated",
        "iss": _ISSUER,
        "email": "user@test.dev",
        "exp": now + 3600,
        "iat": now,
    }
    payload.update(overrides)
    return payload


class VerifierES256Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = generate_private_key(SECP256R1())
        cls.public_key = cls.private_key.public_key()

    def _verifier(self, **settings_overrides):
        verifier = TokenVerifier(settings=_settings(**settings_overrides))
        signing_key = MagicMock()
        signing_key.key = self.public_key
        verifier._jwks = MagicMock()
        verifier._jwks.get_signing_key_from_jwt.return_value = signing_key
        return verifier

    def _token(self, **claim_overrides):
        return jwt.encode(_claims(**claim_overrides), self.private_key, algorithm="ES256")

    def test_valid_token_yields_claims(self):
        claims = self._verifier().verify(self._token())
        self.assertEqual(claims.role, "authenticated")
        self.assertEqual(claims.email, "user@test.dev")
        self.assertTrue(claims.sub.startswith("8f8f"))

    def test_audience_as_list_is_accepted(self):
        claims = self._verifier().verify(self._token(aud=["authenticated"]))
        self.assertEqual(claims.role, "authenticated")

    def test_expired_token_is_rejected(self):
        now = int(time.time())
        token = self._token(exp=now - 10, iat=now - 3600)
        with self.assertRaises(TokenError):
            self._verifier().verify(token)

    def test_wrong_audience_is_rejected(self):
        with self.assertRaises(TokenError):
            self._verifier().verify(self._token(aud="anon"))

    def test_wrong_issuer_is_rejected(self):
        with self.assertRaises(TokenError):
            self._verifier().verify(self._token(iss="https://evil.example/auth/v1"))

    def test_tampered_signature_is_rejected(self):
        other_key = generate_private_key(SECP256R1())
        token = jwt.encode(_claims(), other_key, algorithm="ES256")
        with self.assertRaises(TokenError):
            self._verifier().verify(token)


class VerifierHS256Tests(unittest.TestCase):
    def _token(self, **claim_overrides):
        return jwt.encode(_claims(**claim_overrides), _HS_SECRET, algorithm="HS256")

    def test_hs256_verified_when_secret_configured(self):
        verifier = TokenVerifier(settings=_settings(SUPABASE_JWT_SECRET=_HS_SECRET))
        claims = verifier.verify(self._token())
        self.assertEqual(claims.role, "authenticated")

    def test_hs256_without_secret_is_rejected(self):
        verifier = TokenVerifier(settings=_settings())
        with self.assertRaises(TokenError):
            verifier.verify(self._token())

    def test_hs256_with_wrong_secret_is_rejected(self):
        verifier = TokenVerifier(settings=_settings(SUPABASE_JWT_SECRET="another"))
        with self.assertRaises(TokenError):
            verifier.verify(self._token())


if __name__ == "__main__":
    unittest.main()
