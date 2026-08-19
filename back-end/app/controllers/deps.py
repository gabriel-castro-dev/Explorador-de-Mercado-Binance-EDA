"""Shared FastAPI dependencies: auth, RLS-scoped Supabase client, repositories."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.verifier import TokenError, UserClaims, get_verifier
from app.repositories.features_repository import FeaturesRepository
from app.repositories.klines_repository import KlinesRepository
from app.repositories.symbols_repository import SymbolsRepository
from app.repositories.tickers_repository import TickersRepository
from config import get_settings
from supabase import Client, ClientOptions, create_client

_bearer = HTTPBearer(auto_error=False)  # auto_error=False -> controlamos o formato do 401
_BearerDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_claims(credentials: _BearerDep) -> UserClaims:
    """Validate the bearer token locally and return the user claims (401 otherwise)."""
    if credentials is None:
        raise _unauthorized("Not authenticated")
    try:
        return get_verifier().verify(credentials.credentials)
    except TokenError:
        raise _unauthorized("Invalid or expired token") from None


CurrentClaimsDep = Annotated[UserClaims, Depends(get_claims)]


def get_rls_supabase(credentials: _BearerDep, _claims: CurrentClaimsDep) -> Client:
    """Per-request client carrying the USER JWT so PostgREST enforces RLS.

    Built on SUPABASE_PUBLISHABLE_KEY (apikey header); the Authorization
    header set here is preserved by supabase-py v2 and makes PostgREST
    run the query as the `authenticated` role.
    """
    settings = get_settings()
    options = ClientOptions(
        headers={"Authorization": f"Bearer {credentials.credentials}"},
        auto_refresh_token=False,
        persist_session=False,
    )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY, options)


SupabaseDep = Annotated[Client, Depends(get_rls_supabase)]


def get_klines_repo(supabase: SupabaseDep) -> KlinesRepository:
    return KlinesRepository(supabase=supabase)


def get_features_repo(supabase: SupabaseDep) -> FeaturesRepository:
    return FeaturesRepository(supabase=supabase)


def get_symbols_repo(supabase: SupabaseDep) -> SymbolsRepository:
    return SymbolsRepository(supabase=supabase)


def get_tickers_repo(supabase: SupabaseDep) -> TickersRepository:
    return TickersRepository(supabase=supabase)


KlinesRepoDep = Annotated[KlinesRepository, Depends(get_klines_repo)]
FeaturesRepoDep = Annotated[FeaturesRepository, Depends(get_features_repo)]
SymbolsRepoDep = Annotated[SymbolsRepository, Depends(get_symbols_repo)]
TickersRepoDep = Annotated[TickersRepository, Depends(get_tickers_repo)]
