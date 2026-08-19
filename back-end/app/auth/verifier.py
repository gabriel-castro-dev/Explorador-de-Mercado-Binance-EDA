"""Local verification of Supabase Auth access tokens (no per-request network call)."""

import logging
from functools import lru_cache
from typing import Optional

import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, ConfigDict

from config import Settings, get_settings

logger = logging.getLogger(__name__)

_ASYMMETRIC_ALGS = ["ES256", "RS256"]


class TokenError(Exception):
    """Raised when a bearer token is missing required claims, expired or forged."""


class UserClaims(BaseModel):
    """Validated claims extracted from a Supabase access token.

    user_metadata is intentionally NOT modeled: it is user-editable and
    must never drive authorization decisions.
    """

    model_config = ConfigDict(extra="ignore")

    sub: str  # id do usuário no Supabase (UUID)
    role: str  # "authenticated"
    email: Optional[str] = None
    session_id: Optional[str] = None


class TokenVerifier:
    """Verifies Supabase JWTs against the project JWKS (ES256/RS256).

    Falls back to the legacy HS256 shared secret only when
    SUPABASE_JWT_SECRET is configured. Supabase recommends migrating to
    asymmetric keys instead (Dashboard > Settings > JWT Signing Keys >
    "Migrate JWT secret" then "Rotate keys").
    """

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        base = self._settings.SUPABASE_URL.rstrip("/")
        self._issuer = f"{base}/auth/v1"
        # JWKS tem edge-cache de 10 min no Supabase; cachear localmente também.
        self._jwks = PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json",
            cache_keys=True,
            lifespan=600,
        )

    def verify(self, token: str) -> UserClaims:
        """Validate signature, exp, aud and iss; return the user claims.

        The header alg only selects the KEY SOURCE; the algorithms
        allow-list passed to jwt.decode prevents algorithm-confusion
        attacks (an HS256 token can never verify against a JWKS public
        key and vice versa).

        Raises:
            TokenError: If the token is invalid, expired or unverifiable.
        """
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") == "HS256":
                secret = self._settings.SUPABASE_JWT_SECRET
                if not secret:
                    raise TokenError(
                        "HS256 token received but SUPABASE_JWT_SECRET is not set; "
                        "migrate the project to asymmetric signing keys."
                    )
                key, algorithms = secret, ["HS256"]
            else:
                key = self._jwks.get_signing_key_from_jwt(token).key
                algorithms = _ASYMMETRIC_ALGS
            payload = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience="authenticated",  # aceita string ou lista
                issuer=self._issuer,
                options={"require": ["exp", "iat", "sub", "aud", "iss"]},
            )
        except TokenError:
            raise
        except jwt.PyJWTError as error:
            raise TokenError(f"Invalid token: {error}") from error
        return UserClaims.model_validate(payload)


@lru_cache
def get_verifier() -> TokenVerifier:
    """Process-wide verifier so the JWKS cache survives across requests."""
    return TokenVerifier()
