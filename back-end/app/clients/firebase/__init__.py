"""Firebase connection package."""

from app.clients.firebase.client import FirebaseCredentialsError, get_firestore

__all__ = ["FirebaseCredentialsError", "get_firestore"]
