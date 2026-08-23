"""Chat-completions client for OpenAI-compatible LLM gateways with fallback.

Supports a chain of (gateway, model) attempts tried in order — e.g. OpenCode
Zen with a free model first, then another free model, then OpenRouter. The
API keys never leave the server: the SPA is static and any key shipped in its
bundle would be public.
"""

import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 30.0

GATEWAY_BASE_URLS = {
    "opencode-zen": "https://opencode.ai/zen/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


class LlmGatewayError(RuntimeError):
    """Every attempt in the chain failed (or the chain is empty)."""


@dataclass(frozen=True)
class GatewayAttempt:
    """One (gateway, model) step of the fallback chain.

    Attributes:
        provider: Key into ``GATEWAY_BASE_URLS`` (used in logs and in the
            ``model`` field of the stored reading).
        api_key: Bearer token for that gateway.
        model: Model slug as the gateway spells it.
    """

    provider: str
    api_key: str
    model: str


class LlmGatewayClient:
    """Tries each attempt in order and returns the first completion."""

    def __init__(self, timeout: float = _TIMEOUT_SECONDS) -> None:
        self.timeout = timeout

    def _complete_once(
        self,
        attempt: GatewayAttempt,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        base_url = GATEWAY_BASE_URLS.get(attempt.provider)
        if not base_url:
            raise LlmGatewayError(f"unknown gateway: {attempt.provider}")
        response = httpx.post(
            f"{base_url}/chat/completions",
            json={
                "model": attempt.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            headers={"Authorization": f"Bearer {attempt.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        content = (choices[0].get("message") or {}).get("content") if choices else None
        if not content or not str(content).strip():
            raise LlmGatewayError("empty completion")
        return str(content).strip()

    def complete(
        self,
        attempts: list[GatewayAttempt],
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 500,
    ) -> tuple[str, str]:
        """Run the fallback chain.

        Args:
            attempts: (gateway, model) steps in priority order.
            system: System prompt (style and honesty rules).
            user: User message carrying the numeric context to summarize.
            temperature: Sampling temperature (low: the text mirrors the data).
            max_tokens: Completion budget.

        Returns:
            Tuple ``(text, "provider/model")`` of the attempt that succeeded.

        Raises:
            LlmGatewayError: When the chain is empty or every attempt failed.
        """
        if not attempts:
            raise LlmGatewayError("no LLM gateway configured (set the API keys)")
        errors: list[str] = []
        for attempt in attempts:
            try:
                text = self._complete_once(
                    attempt,
                    system=system,
                    user=user,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return text, f"{attempt.provider}/{attempt.model}"
            except (httpx.HTTPError, LlmGatewayError) as exc:
                logger.warning("Falha no gateway %s (%s): %s", attempt.provider, attempt.model, exc)
                errors.append(f"{attempt.provider}/{attempt.model}: {exc}")
        raise LlmGatewayError("; ".join(errors))
