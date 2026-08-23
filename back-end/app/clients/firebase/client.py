"""Firebase Admin SDK connection (Firestore).

The Admin SDK runs with full privileges and **bypasses Firestore security
rules**, so this connection must never be exposed to clients: only the API
talks to Firestore, and every access is scoped by the caller's validated
Supabase token (see app/controllers/deps.py).

Credentials are resolved lazily so jobs and the offline test suite never
need a service account file.
"""

import json
import logging
from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

from config import Settings, get_settings

logger = logging.getLogger(__name__)


class FirebaseCredentialsError(RuntimeError):
    """No usable Firebase service account was configured."""


def _build_credentials(settings: Settings) -> credentials.Certificate:
    """Build the service account credentials from the configured source.

    Resolution order: a JSON file path (local dev, or a read-only volume in
    the container) and then the raw JSON contents (for runtimes where
    mounting a file is inconvenient). The key is never baked into the image.

    Args:
        settings: Application settings holding the credential configuration.

    Returns:
        Certificate credentials for the Firebase Admin SDK.

    Raises:
        FirebaseCredentialsError: If neither source is configured.
    """
    if settings.FIREBASE_CREDENTIALS_PATH:
        return credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    if settings.FIREBASE_CREDENTIALS_JSON:
        return credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
    raise FirebaseCredentialsError(
        "Configure FIREBASE_CREDENTIALS_PATH (arquivo) ou FIREBASE_CREDENTIALS_JSON "
        "(conteudo) para acessar o Firestore."
    )


@lru_cache(maxsize=1)
def get_firestore(settings: Settings | None = None) -> firestore.Client:
    """Initialize the Firebase app once per process and return a Firestore client.

    Args:
        settings: Optional pre-built settings; defaults to the cached
            application settings.

    Returns:
        A Firestore client bound to the configured project.

    Raises:
        FirebaseCredentialsError: If no service account is configured.
    """
    settings = settings or get_settings()
    if not firebase_admin._apps:  # initialize_app duas vezes levanta ValueError
        firebase_admin.initialize_app(_build_credentials(settings))
        logger.info("Firebase Admin SDK inicializado.")
    return firestore.client()
