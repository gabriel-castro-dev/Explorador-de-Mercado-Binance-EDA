"""Read and write endpoints for the signed-in user's preferences."""

import logging

from fastapi import APIRouter, Depends

from app.controllers.deps import (
    CurrentClaimsDep,
    FirebaseIdentityDep,
    PreferencesRepoDep,
    get_claims,
)
from app.schemas.preferences import PreferencesIn, PreferencesOut

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/preferences",
    tags=["preferences"],
    dependencies=[Depends(get_claims)],
)


def _to_response(stored: dict | None, email: str | None) -> PreferencesOut:
    """Merge a stored document (or the defaults) with the token's email."""
    values = PreferencesOut.model_validate(stored) if stored else PreferencesOut()
    return values.model_copy(update={"email": email})


@router.get("")
def get_preferences(
    claims: CurrentClaimsDep, repo: PreferencesRepoDep, identity: FirebaseIdentityDep
) -> PreferencesOut:
    """Preferências do usuário autenticado.

    Um usuário que nunca salvou nada recebe os valores padrão (200, não 404),
    para o app abrir sem tratamento especial na primeira visita. O e-mail é
    somente leitura e vem do token do Supabase, não do Firestore.

    Esta é a primeira rota que o app chama, então é aqui que a conta espelho
    no Firebase é criada (sem senha, com o mesmo id do Supabase) — o cadastro
    continua sendo um só, feito no Supabase.
    """
    try:
        identity.ensure_user(claims.sub, claims.email)
    except Exception:  # noqa: BLE001 - provisionar é acessório: nunca derruba a leitura
        logger.exception("Falha ao provisionar o usuario %s no Firebase.", claims.sub)
    return _to_response(repo.get(claims.sub), claims.email)


@router.put("")
def save_preferences(
    payload: PreferencesIn, claims: CurrentClaimsDep, repo: PreferencesRepoDep
) -> PreferencesOut:
    """Substitui as preferências do usuário autenticado.

    Idempotente: reenviar o mesmo payload produz o mesmo documento. O dono do
    documento vem sempre do token — `user_id` ou `email` no corpo são
    rejeitados com 422.
    """
    stored = repo.upsert(claims.sub, payload.model_dump())
    return _to_response(stored, claims.email)
