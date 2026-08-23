"""Firebase connection package."""

from app.clients.firebase.client import (
    FirebaseCredentialsError,
    build_firestore,
    get_auth,
    get_firestore,
)

__all__ = ["FirebaseCredentialsError", "build_firestore", "get_auth", "get_firestore"]
