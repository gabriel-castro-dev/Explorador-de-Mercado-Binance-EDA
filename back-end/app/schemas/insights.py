"""Schemas for model-generated insights (the home page's daily reading)."""

from datetime import datetime

from pydantic import BaseModel


class DailyReadingOut(BaseModel):
    """One generated market reading, cached globally per UTC day.

    Attributes:
        date: UTC day the reading refers to (``YYYY-MM-DD``).
        generated_at: When the text was generated.
        model: Model slug that actually produced the text (post-fallback).
        text: The reading itself, in pt-BR, grounded on the day's numbers.
        disclaimer: Fixed sentence every forecast surface must show.
    """

    date: str
    generated_at: datetime
    model: str
    text: str
    disclaimer: str
