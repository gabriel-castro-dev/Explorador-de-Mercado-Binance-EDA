"""Persistence for per-user preferences (Firestore).

One document per user, keyed by the Supabase user id, in the collection
configured by ``FIRESTORE_COLLECTION``. The document also carries a
``user_id`` field so the collection can be filtered with ``where`` (single
field indexes are automatic in Firestore).
"""

import logging
from typing import Any, Optional

from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from app.clients.firebase import get_firestore
from config import get_settings

logger = logging.getLogger(__name__)


class PreferencesRepository:
    """Data access for the user preferences documents.

    Attributes:
        client: Firestore client used for the queries.
        collection: Name of the preferences collection.
    """

    SCHEMA_VERSION = 1

    def __init__(self, firestore_client: Any = None, collection: Optional[str] = None) -> None:
        """Initialize the repository with an injected or default client.

        Args:
            firestore_client: Optional pre-built Firestore client; defaults
                to the process-wide connection.
            collection: Optional collection name; defaults to settings.
        """
        self.client = firestore_client or get_firestore()
        self.collection = collection or get_settings().FIRESTORE_COLLECTION

    def _document(self, uid: str):
        return self.client.collection(self.collection).document(uid)

    def get(self, uid: str) -> Optional[dict]:
        """Read one user's preferences.

        Args:
            uid: Supabase user id (document id).

        Returns:
            The stored document, or None when the user never saved anything.
        """
        snapshot = self._document(uid).get()
        if not snapshot.exists:
            return None
        return snapshot.to_dict()

    def upsert(self, uid: str, data: dict) -> dict:
        """Create or update one user's preferences.

        ``user_id`` and the timestamps are always written server-side: values
        coming from the request are never trusted for ownership or ordering.

        Args:
            uid: Supabase user id (document id and ``user_id`` field).
            data: Validated preference values to persist.

        Returns:
            The document as persisted (without the server timestamps, which
            are resolved by Firestore after the write).
        """
        document = self._document(uid)
        payload = {
            **data,
            "user_id": uid,
            "schema_version": self.SCHEMA_VERSION,
            "updated_at": SERVER_TIMESTAMP,
        }
        if not document.get().exists:
            payload["created_at"] = SERVER_TIMESTAMP
        document.set(payload, merge=True)
        logger.info("Preferencias salvas para o usuario %s.", uid)
        return {key: value for key, value in payload.items() if value is not SERVER_TIMESTAMP}
