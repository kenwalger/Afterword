"""Model providers: one protocol over httpx, with Ollama (local) and Anthropic (remote).

A provider sends a fixed system text, one user message, and a JSON schema, and
returns the model's text with a normalized stop reason. It has no tools and no
write access to anything (ADR-008). Errors carry a category, never a message
that could hold a URL, host name, path, or credential.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

# Normalized stop reasons.
STOP: str = "stop"
LENGTH: str = "length"
REFUSAL: str = "refusal"
CONTEXT_OVERFLOW: str = "context_overflow"


class ProviderError(Exception):
    """A transport or service failure: the classification is FAILED and retried later."""

    def __init__(self, kind: str) -> None:
        """Create an error.

        :param kind: A category such as ``timeout``, ``connect``, or ``http_500``.
        """
        super().__init__(kind)
        self.kind = kind


class ModelVerificationError(Exception):
    """The installed model is not the pinned one, or is not approved. The message is safe."""


@dataclass(frozen=True)
class ModelIdentity:
    """Which model answered, as recorded on every classification."""

    provider: str
    model_id: str
    # A local model's content digest pins it; a remote model is pinned by its dated ID.
    digest: str | None
    digest_state: str


@dataclass(frozen=True)
class Completion:
    """One model response."""

    text: str
    stop_reason: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    load_ms: int | None = None


class Provider(Protocol):
    """A model behind an HTTP API."""

    identity: ModelIdentity
    # A conservative cap on prompt characters, or None when the context is large.
    max_input_chars: int | None
    # Generation options that can change the answer, recorded in the cache key;
    # None when the provider has none beyond the model, prompt, and output cap.
    options_key: str | None

    def verify(self) -> ModelIdentity:
        """Check that the model to be used is the pinned, approved one.

        :returns: The verified identity.
        """
        ...

    def complete(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> Completion:
        """Ask the model for one schema-constrained answer.

        :param system: Fixed instructions.
        :param user: The delimited data.
        :param schema: JSON schema the output must follow.
        :param max_tokens: Output cap.
        :returns: The response.
        """
        ...

    def close(self) -> None:
        """Release connections."""
        ...
