"""Chat-completions client for OpenAI-compatible LLM gateways with fallback.

Supports a chain of (gateway, model) attempts tried in order — e.g. OpenCode
Zen with a free model first, then another free model, then OpenRouter. The
API keys never leave the server: the SPA is static and any key shipped in its
bundle would be public.

Todos os modelos da cadeia atual são de raciocínio: em APIs compatíveis com
OpenAI o ``max_tokens`` é orçamento único para pensamento **e** resposta, e um
teto baixo faz o modelo gastar tudo pensando e devolver texto truncado (ou o
próprio raciocínio vazado em ``content``). Por isso o client dá orçamento
folgado, limita o raciocínio onde o gateway aceita, recusa respostas truncadas
e remove blocos ``<think>`` antes de aceitar o texto.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 60.0

# Teto do raciocínio, dentro do orçamento total de max_tokens: sobra espaço
# para o parágrafo final. Verificado em 2026-08-24 na doc do OpenRouter:
# "reasoning" aceita effort OU max_tokens (nunca os dois juntos).
_REASONING_MAX_TOKENS = 1500

# Gateways cuja documentação descreve o campo "reasoning" no corpo da
# requisição. O Zen não documenta o campo, então nada é enviado para ele.
_REASONING_CONTROL_GATEWAYS = frozenset({"openrouter"})

# Raciocínio vazado no content: bloco fechado, ou aberto e cortado no fim.
_THINK_BLOCK = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.DOTALL | re.IGNORECASE)
_UNCLOSED_THINK = re.compile(r"<think\b[^>]*>.*\Z", re.DOTALL | re.IGNORECASE)

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


def strip_reasoning(content: str) -> str:
    """Remove blocos ``<think>`` (fechados ou truncados) do texto do modelo."""
    without_blocks = _THINK_BLOCK.sub(" ", content)
    return _UNCLOSED_THINK.sub(" ", without_blocks).strip()


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
        payload: dict = {
            "model": attempt.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if attempt.provider in _REASONING_CONTROL_GATEWAYS:
            payload["reasoning"] = {"max_tokens": _REASONING_MAX_TOKENS}
        response = httpx.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {attempt.api_key}"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        choices = body.get("choices") or []
        if not choices:
            raise LlmGatewayError("empty completion")
        choice = choices[0] or {}
        if choice.get("finish_reason") == "length":
            # O modelo estourou o orçamento pensando: o que veio é raciocínio
            # ou um parágrafo cortado no meio. Nunca serve como leitura.
            raise LlmGatewayError("truncated completion")
        # Um "reasoning"/"reasoning_content" separado é ignorado de propósito:
        # só o content é resposta.
        content = (choice.get("message") or {}).get("content")
        text = strip_reasoning(str(content)) if content else ""
        if not text:
            raise LlmGatewayError("empty completion")
        return text

    def complete(
        self,
        attempts: list[GatewayAttempt],
        *,
        system: str,
        user: str,
        temperature: float = 0.4,
        max_tokens: int = 2500,
        validator: Optional[Callable[[str], bool]] = None,
    ) -> tuple[str, str]:
        """Run the fallback chain.

        Args:
            attempts: (gateway, model) steps in priority order.
            system: System prompt (style and honesty rules).
            user: User message carrying the numeric context to summarize.
            temperature: Sampling temperature (low: the text mirrors the data).
            max_tokens: Completion budget (raciocínio + resposta).
            validator: Portão opcional sobre o texto; reprovar conta como
                falha da tentativa e a cadeia avança para o próximo gateway.

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
                if validator and not validator(text):
                    raise LlmGatewayError("completion rejected by validator")
                return text, f"{attempt.provider}/{attempt.model}"
            except (httpx.HTTPError, LlmGatewayError) as exc:
                logger.warning("Falha no gateway %s (%s): %s", attempt.provider, attempt.model, exc)
                errors.append(f"{attempt.provider}/{attempt.model}: {exc}")
        raise LlmGatewayError("; ".join(errors))
