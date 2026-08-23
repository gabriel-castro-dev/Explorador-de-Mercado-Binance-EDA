"""Minimal OpenRouter chat-completions client (used by the insights service).

The API key never leaves the server: the SPA is static and any key shipped in
its bundle would be public, so all text generation goes through this back end.
"""

import logging
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://openrouter.ai/api/v1"
_TIMEOUT_SECONDS = 30.0


class OpenRouterError(RuntimeError):
    """Generation failed (missing key, HTTP error, empty completion)."""


class OpenRouterClient:
    """Thin wrapper over ``POST /chat/completions`` with model fallback.

    Attributes:
        api_key: OpenRouter API key (``OPENROUTER_API_KEY``).
        timeout: Request timeout in seconds.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: float = _TIMEOUT_SECONDS) -> None:
        self.api_key = api_key if api_key is not None else get_settings().OPENROUTER_API_KEY
        self.timeout = timeout

    def complete(
        self,
        *,
        system: str,
        user: str,
        models: list[str],
        temperature: float = 0.4,
        max_tokens: int = 500,
    ) -> tuple[str, str]:
        """Generate one completion, letting OpenRouter fall back across ``models``.

        Args:
            system: System prompt (style and honesty rules).
            user: User message carrying the numeric context to summarize.
            models: Model slugs in priority order — OpenRouter's ``models``
                array routes to the next one when the previous fails.
            temperature: Sampling temperature (low: the text mirrors the data).
            max_tokens: Completion budget.

        Returns:
            Tuple ``(text, model_used)``.

        Raises:
            OpenRouterError: When the key is missing, the HTTP call fails or
                the response carries no usable content.
        """
        if not self.api_key:
            raise OpenRouterError("OPENROUTER_API_KEY is not configured")
        primary = models[0] if models else None
        if not primary:
            raise OpenRouterError("no model configured")
        payload = {
            "model": primary,
            "models": models,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = httpx.post(
                f"{_BASE_URL}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

        body = response.json()
        choices = body.get("choices") or []
        content = (choices[0].get("message") or {}).get("content") if choices else None
        if not content or not str(content).strip():
            raise OpenRouterError("OpenRouter returned an empty completion")
        return str(content).strip(), str(body.get("model") or primary)
