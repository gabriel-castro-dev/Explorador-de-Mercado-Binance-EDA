"""Firebase identity bridge for users authenticated by Supabase."""

from fastapi import APIRouter, Depends

from app.controllers.deps import CurrentClaimsDep, FirebaseIdentityDep, get_claims
from app.schemas.auth import FirebaseTokenOut

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
    dependencies=[Depends(get_claims)],
)


@router.post("/firebase-token")
def issue_firebase_token(
    claims: CurrentClaimsDep, identity: FirebaseIdentityDep
) -> FirebaseTokenOut:
    """Emite um custom token do Firebase para o usuário autenticado.

    O usuário é criado no Firebase (sem senha) caso ainda não exista, com o
    mesmo id do Supabase. Troque o token por um `idToken` chamando
    `accounts:signInWithCustomToken?key=<web api key>`.
    """
    identity.ensure_user(claims.sub, claims.email)
    return FirebaseTokenOut(custom_token=identity.mint_custom_token(claims.sub))
