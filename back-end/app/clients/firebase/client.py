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
import threading
from functools import lru_cache

import firebase_admin
from firebase_admin import auth, credentials, firestore

from config import Settings, get_settings

logger = logging.getLogger(__name__)

# Sync handlers run in a threadpool, so two first requests can race here.
# lru_cache does not serialize concurrent misses: without this lock both
# threads pass the _apps check and the second initialize_app raises.
_init_lock = threading.Lock()


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


def _initialize(settings: Settings | None = None) -> None:
    """Initialize the default Firebase app once per process.

    Guarded by a lock: initialize_app raises when the default app already
    exists, and concurrent first requests would otherwise both get past the
    check.

    Args:
        settings: Optional pre-built settings; defaults to the cached
            application settings.

    Raises:
        FirebaseCredentialsError: If no service account is configured.
    """
    if firebase_admin._apps:
        return
    with _init_lock:
        if not firebase_admin._apps:  # double-check dentro do lock
            firebase_admin.initialize_app(_build_credentials(settings or get_settings()))
            logger.info("Firebase Admin SDK inicializado.")


def build_firestore(settings: Settings | None = None) -> firestore.Client:
    """Build a Firestore client, initializing the app if needed.

    Kept uncached on purpose: ``Settings`` is not hashable, so it cannot be
    part of an lru_cache key. This is the seam callers use to inject
    settings; ``get_firestore()`` is the cached no-argument entry point.

    Args:
        settings: Optional pre-built settings; defaults to the cached
            application settings.

    Returns:
        A Firestore client bound to the configured project.

    Raises:
        FirebaseCredentialsError: If no service account is configured.
    """
    _initialize(settings)
    return firestore.client()


@lru_cache(maxsize=1)
def get_firestore() -> firestore.Client:
    """Process-wide Firestore client (cached).

    Returns:
        A Firestore client bound to the configured project.
    """
    return build_firestore()


def get_auth(settings: Settings | None = None):
    """Return the Firebase Auth module with the app initialized.

    ``firebase_admin.auth`` is stateless: it only requires the default app
    to exist, so there is nothing to cache here.

    Args:
        settings: Optional pre-built settings; defaults to the cached
            application settings.

    Returns:
        The ``firebase_admin.auth`` module.

    Raises:
        FirebaseCredentialsError: If no service account is configured.
    """
    _initialize(settings)
    return auth
