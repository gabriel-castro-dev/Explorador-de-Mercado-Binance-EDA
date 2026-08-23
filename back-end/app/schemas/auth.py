"""Schemas for the Firebase identity bridge."""

from pydantic import BaseModel


class FirebaseTokenOut(BaseModel):
    """A short-lived Firebase custom token for the signed-in user.

    Exchange it for an ID token at the Identity Toolkit:
    ``POST accounts:signInWithCustomToken?key=<web api key>``.
    """

    custom_token: str
    expires_in: int = 3600
