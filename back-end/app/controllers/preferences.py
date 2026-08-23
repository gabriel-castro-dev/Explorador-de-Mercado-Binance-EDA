"""Read and write endpoints for the signed-in user's preferences."""

from fastapi import APIRouter, Depends

from app.controllers.deps import CurrentClaimsDep, PreferencesRepoDep, get_claims
from app.schemas.preferences import PreferencesIn, PreferencesOut

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
def get_preferences(claims: CurrentClaimsDep, repo: PreferencesRepoDep) -> PreferencesOut:
    """Preferências do usuário autenticado.

    Um usuário que nunca salvou nada recebe os valores padrão (200, não 404),
    para o app abrir sem tratamento especial na primeira visita. O e-mail é
    somente leitura e vem do token do Supabase, não do Firestore.
    """
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
