"""Anthropic Messages API (model-boundary path B, ``PRIVACY-AND-BOUNDARIES.md``): secondary only.

Raw HTTP over httpx. Output is constrained with structured outputs
(``output_config.format`` with a JSON schema), which ``claude-haiku-4-5``
supports without a beta header (checked against current documentation on
2026-10-03). That schema dialect has no string-length or array constraints, so
the stdlib validator enforces them for every provider alike.

The key is read from ``ANTHROPIC_API_KEY`` here and nowhere else, and goes in a
request header only (ADR-006). It is never printed, logged, stored, or put in
an exception. This path's boundary record is not signed off: in this session
the provider runs only under respx in tests.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx

from afterword.providers import (
    LENGTH,
    REFUSAL,
    STOP,
    Completion,
    ModelIdentity,
    ProviderError,
)

PROVIDER: str = "anthropic"
ENV_VAR: str = "ANTHROPIC_API_KEY"
API_URL: str = "https://api.anthropic.com/v1/messages"
API_VERSION: str = "2023-06-01"
# Pinned by its dated ID (EVALUATION.md: a remote model has no content digest).
DEFAULT_MODEL: str = "claude-haiku-4-5-20251001"
TIMEOUT_S: float = 60.0


class MissingCredentialError(RuntimeError):
    """Raised when the API key is not in the environment. The message names only the variable."""


class AnthropicProvider:
    """One pinned Anthropic model."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_MODEL,
        client: httpx.Client | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a provider.

        :param api_key: The key; held in memory only.
        :param model: Dated model ID.
        :param client: HTTP client, injectable for tests.
        :param clock: Monotonic clock for latency.
        """
        self._key = api_key
        self.client = client or httpx.Client(timeout=TIMEOUT_S)
        self.clock = clock
        self.identity = ModelIdentity(PROVIDER, model, None, "NOT_EXPOSED")
        self.max_input_chars: int | None = None

    @classmethod
    def from_env(cls, **kwargs: Any) -> AnthropicProvider:
        """Create a provider with the key from the environment.

        :param **kwargs: Passed to the constructor.
        :returns: The provider.
        :raises MissingCredentialError: If the variable is unset or empty.
        """
        key = os.environ.get(ENV_VAR, "").strip()
        if not key:
            raise MissingCredentialError(f"{ENV_VAR} is not set")
        return cls(key, **kwargs)

    def __repr__(self) -> str:
        """Describe the provider without its key.

        :returns: Provider and model.
        """
        return f"AnthropicProvider(model={self.identity.model_id!r})"

    def verify(self) -> ModelIdentity:
        """Return the identity; a remote model is pinned by its dated ID, not checked here.

        :returns: The identity, with digest ``NOT_EXPOSED``.
        """
        return self.identity

    def complete(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> Completion:
        """Ask the model for one schema-constrained answer.

        :param system: Fixed instructions.
        :param user: The delimited data.
        :param schema: JSON schema for ``output_config.format``.
        :param max_tokens: Output cap.
        :returns: The response; ``refusal`` and ``max_tokens`` stops are normalized.
        :raises ProviderError: On a transport failure, a non-200 status, or an
            unreadable response.
        """
        body = {
            "model": self.identity.model_id,
            "max_tokens": max_tokens,
            "temperature": 0,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "output_config": {"format": {"type": "json_schema", "schema": schema}},
        }
        headers = {
            "x-api-key": self._key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        started = self.clock()
        try:
            response = self.client.post(API_URL, json=body, headers=headers)
        except httpx.TimeoutException:
            raise ProviderError("timeout") from None
        except httpx.HTTPError:
            raise ProviderError("connect") from None
        latency = int((self.clock() - started) * 1000)
        if response.status_code != 200:
            raise ProviderError(f"http_{response.status_code}")
        try:
            data = response.json()
        except ValueError:
            raise ProviderError("bad_response") from None
        blocks = data.get("content") if isinstance(data, dict) else None
        if not isinstance(blocks, list):
            raise ProviderError("bad_response")
        text = "".join(
            b["text"]
            for b in blocks
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
        )
        stop = {"end_turn": STOP, "max_tokens": LENGTH, "refusal": REFUSAL}.get(
            str(data.get("stop_reason")), STOP
        )
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return Completion(
            text=text,
            stop_reason=stop,
            latency_ms=latency,
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
