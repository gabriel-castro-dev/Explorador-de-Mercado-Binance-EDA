"""Firebase identity provisioning for users authenticated by Supabase.

Supabase Auth is the only authority on credentials: the Firebase user is
created **without a password**, keyed by the Supabase user id, so there is
never a second password to keep in sync. Clients that need a Firebase
session get a short-lived custom token minted from their validated Supabase
token, and exchange it for an ID token through the Identity Toolkit.

Provisioning happens on the first authenticated request rather than at
signup: Supabase requires email confirmation, so there is no session (and
therefore no way to call this API) at the moment the account is created.
"""

import logging
from typing import Any, Optional

from app.clients.firebase import get_auth

logger = logging.getLogger(__name__)


class FirebaseIdentityService:
    """Create and address Firebase users that mirror Supabase identities.

    Attributes:
        auth: The Firebase Auth module (injectable for offline tests).
    """

    def __init__(self, auth_module: Any = None) -> None:
        """Initialize the service with an injected or default auth module.

        Args:
            auth_module: Optional pre-built ``firebase_admin.auth`` module;
                defaults to the process-wide connection.
        """
        self.auth = auth_module or get_auth()

    def ensure_user(self, uid: str, email: Optional[str] = None) -> bool:
        """Make sure a Firebase user exists for this Supabase identity.

        Idempotent: the Firebase uid is the Supabase ``sub``, so repeated
        calls find the existing user. The user is created without a password
        on purpose — signing in with a password against Firebase must fail,
        Supabase owns credentials.

        Args:
            uid: Supabase user id (``claims.sub``), reused as the Firebase uid.
            email: Address to attach to the Firebase user, when known.

        Returns:
            True when a user was created, False when it already existed.
        """
        try:
            self.auth.get_user(uid)
            return False
        except self.auth.UserNotFoundError:
            pass
        try:
            self.auth.create_user(uid=uid, email=email)
            logger.info("Usuario Firebase provisionado para %s.", uid)
            return True
        except self.auth.EmailAlreadyExistsError:
            # O e-mail pertence a outro uid (ex.: conta criada a mao no console).
            # Nao ha o que reconciliar com seguranca aqui: registra e segue.
            logger.warning(
                "E-mail ja usado por outro usuario Firebase; %s segue sem conta espelhada.", uid
            )
            return False

    def mint_custom_token(self, uid: str) -> str:
        """Mint a short-lived Firebase custom token for this user.

        Args:
            uid: Supabase user id, reused as the Firebase uid.

        Returns:
            The signed custom token, ready to be exchanged for an ID token.
        """
        token = self.auth.create_custom_token(uid)
        return token.decode("utf-8") if isinstance(token, bytes) else token
