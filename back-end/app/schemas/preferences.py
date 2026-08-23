"""Schemas for the user preferences stored in Firestore.

The email is deliberately absent from the input schema: it belongs to
Supabase Auth (the identity provider) and is echoed back on reads as a
read-only convenience field taken from the validated token.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

NotificationChannel = Literal["email", "sms", "whatsapp"]

_PHONE_E164 = r"^\+[1-9]\d{7,14}$"


class NotificationTopics(BaseModel):
    """Which daily digest topics the user opted into."""

    model_config = ConfigDict(extra="forbid")

    forecast_gap: bool = False
    volume_movers: bool = False
    volatility: bool = False
    model_runs: bool = False


class NotificationSettings(BaseModel):
    """Digest switch, delivery channel and selected topics."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    channel: NotificationChannel = "email"
    topics: NotificationTopics = Field(default_factory=NotificationTopics)


class ChartSettings(BaseModel):
    """Chart rendering preferences (accessibility)."""

    model_config = ConfigDict(extra="forbid")

    hollow_up_candles: bool = False


class PreferencesIn(BaseModel):
    """Payload accepted when saving preferences.

    ``extra="forbid"`` is deliberate: it rejects any attempt to smuggle
    ``user_id`` or ``email`` into the document. The owner of the document
    always comes from the validated token, never from the request body.
    """

    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, pattern=_PHONE_E164)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    chart: ChartSettings = Field(default_factory=ChartSettings)


class PreferencesOut(PreferencesIn):
    """Preferences returned to the client.

    ``extra="ignore"`` (not ``forbid``): documents written by an older
    schema version must never break a read.
    """

    model_config = ConfigDict(extra="ignore")

    email: Optional[str] = None  # read-only: vem do token do Supabase, nao do Firestore
