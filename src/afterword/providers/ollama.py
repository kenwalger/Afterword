"""Local models through Ollama (model-boundary path A, ``PRIVACY-AND-BOUNDARIES.md``).

Requests go to the loopback interface only, so no comment data leaves the
machine. A non-loopback host is refused unless the caller names it explicitly,
because it would be a different boundary needing its own record.

Each model is pinned by its content digest (``docs/FRICTION-LOG.md``, session 4,
07:55) and checked against ``/api/tags`` before any run. Generation is as
deterministic as Ollama allows: temperature 0, a fixed seed, a fixed context
size, an output cap, and thinking off. These options are part of every cache
key (:func:`options_key`), so changing one reclassifies rather than reusing.
"""

from __future__ import annotations

import ipaddress
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

import httpx

from afterword.providers import (
    CONTEXT_OVERFLOW,
    LENGTH,
    STOP,
    Completion,
    ModelIdentity,
    ModelVerificationError,
    ProviderError,
)

PROVIDER: str = "ollama"
DEFAULT_HOST: str = "http://localhost:11434"
# Approved models and their pinned digests (session 4, 07:55 entry).
PINNED_DIGESTS: dict[str, str] = {
    "qwen3:4b-instruct-2507-q4_K_M": (
        "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"
    ),
    "llama3.1:8b-instruct-q4_K_M": (
        "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e"
    ),
}
SEED: int = 20261003
# 4096 from 2026-10-08 (2048 before). The longest model input among the 458 `dev`
# comments is 5,953 characters, at most about 1,984 tokens at the guard's
# conservative 3 characters per token; at 2048 the guard refused 3 of them.
NUM_CTX: int = 4096
NUM_PREDICT: int = 200
# Prompt characters allowed: the context left after the output cap, at a
# conservative 3 characters per token. Longer inputs are not sent.
MAX_INPUT_CHARS: int = (NUM_CTX - NUM_PREDICT) * 3
TIMEOUT_S: float = 300.0


def options_key(num_ctx: int = NUM_CTX) -> str:
    """Name the generation options that can change a model's answer, for the cache key.

    :param num_ctx: Context size, in tokens.
    :returns: A stable string such as ``num_ctx=4096;num_predict=200;seed=20261003;temperature=0``.
    """
    return f"num_ctx={num_ctx};num_predict={NUM_PREDICT};seed={SEED};temperature=0"


def is_loopback(host_url: str) -> bool:
    """Report whether a URL's host is the loopback interface.

    :param host_url: Base URL, such as ``http://localhost:11434``.
    :returns: ``True`` for ``localhost`` or a loopback address.
    """
    host = urlparse(host_url).hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class OllamaProvider:
    """One pinned local model."""

    def __init__(
        self,
        model: str,
        *,
        host: str = DEFAULT_HOST,
        allow_non_loopback: bool = False,
        client: httpx.Client | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Create a provider for one approved model.

        :param model: Ollama model tag; must be in :data:`PINNED_DIGESTS`.
        :param host: Ollama base URL.
        :param allow_non_loopback: Permit a host off this machine (a different boundary).
        :param client: HTTP client, injectable for tests.
        :param clock: Monotonic clock for latency.
        :raises ModelVerificationError: If the model is not approved or the host is not
            loopback and not explicitly allowed.
        """
        if model not in PINNED_DIGESTS:
            raise ModelVerificationError(f"{model} is not an approved model")
        if not is_loopback(host) and not allow_non_loopback:
            raise ModelVerificationError(
                "the Ollama host is not on this machine; that is a different model boundary"
            )
        self.model = model
        self.host = host.rstrip("/")
        self.client = client or httpx.Client(timeout=TIMEOUT_S)
        self.clock = clock
        self.identity = ModelIdentity(PROVIDER, model, PINNED_DIGESTS[model], "PRESENT")
        self.max_input_chars: int | None = MAX_INPUT_CHARS
        self.options_key: str | None = options_key()

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        try:
            response = self.client.request(method, self.host + path, json=body)
        except httpx.TimeoutException:
            raise ProviderError("timeout") from None
        except httpx.HTTPError:
            raise ProviderError("connect") from None
        if response.status_code != 200:
            raise ProviderError(f"http_{response.status_code}")
        try:
            return response.json()
        except ValueError:
            raise ProviderError("bad_response") from None

    def installed_digest(self) -> str | None:
        """Read the installed digest of this provider's model.

        :returns: The digest, or ``None`` when the model is not installed.
        """
        tags = self._request("GET", "/api/tags")
        for m in tags.get("models", []) if isinstance(tags, dict) else []:
            if isinstance(m, dict) and self.model in (m.get("name"), m.get("model")):
                digest = m.get("digest")
                return digest if isinstance(digest, str) else None
        return None

    def verify(self) -> ModelIdentity:
        """Check the installed model's digest against the pin.

        :returns: The verified identity.
        :raises ModelVerificationError: If the model is missing or its digest differs.
        """
        installed = self.installed_digest()
        if installed is None:
            raise ModelVerificationError(f"{self.model} is not installed")
        if installed != PINNED_DIGESTS[self.model]:
            raise ModelVerificationError(
                f"{self.model} digest {installed[:12]} does not match the pinned "
                f"{PINNED_DIGESTS[self.model][:12]}; refusing to run"
            )
        return self.identity

    def unload(self) -> None:
        """Unload the model, so the next request measures a cold start."""
        self._request("POST", "/api/generate", {"model": self.model, "keep_alive": 0})

    def complete(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> Completion:
        """Ask the model for one schema-constrained answer through ``/api/chat``.

        :param system: Fixed instructions.
        :param user: The delimited data.
        :param schema: JSON schema, passed as Ollama's ``format``.
        :param max_tokens: Output cap (``num_predict``).
        :returns: The response. A prompt that filled the context is reported as
            ``context_overflow``, because Ollama would have dropped part of it.
        :raises ProviderError: On a transport failure or a non-200 status.
        """
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": schema,
            "think": False,
            "options": {
                "temperature": 0,
                "seed": SEED,
                "num_ctx": NUM_CTX,
                "num_predict": max_tokens,
            },
        }
        started = self.clock()
        data = self._request("POST", "/api/chat", body)
        latency = int((self.clock() - started) * 1000)
        if not isinstance(data, dict):
            raise ProviderError("bad_response")
        message = data.get("message")
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str):
            raise ProviderError("bad_response")
        prompt_tokens = data.get("prompt_eval_count")
        stop = LENGTH if data.get("done_reason") == "length" else STOP
        if isinstance(prompt_tokens, int) and prompt_tokens + max_tokens > NUM_CTX:
            stop = CONTEXT_OVERFLOW
        load_ns = data.get("load_duration")
        output_tokens = data.get("eval_count")
        return Completion(
            text=text,
            stop_reason=stop,
            latency_ms=latency,
            input_tokens=prompt_tokens if isinstance(prompt_tokens, int) else None,
            output_tokens=output_tokens if isinstance(output_tokens, int) else None,
            load_ms=int(load_ns / 1_000_000) if isinstance(load_ns, int) else None,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
