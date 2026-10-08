"""Providers under respx only: Ollama on loopback with pinned digests; Anthropic, no live calls."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from afterword.providers import (
    CONTEXT_OVERFLOW,
    LENGTH,
    REFUSAL,
    STOP,
    ModelVerificationError,
    ProviderError,
    anthropic,
    ollama,
)
from tests.fake_models import QWEN, FakeOllama, answer

SCHEMA = {"type": "object"}
CANARY = "canary-anthropic-key-7c6b5a4f3e2d"


# Ollama -------------------------------------------------------------------------------


def test_only_approved_models_on_loopback_are_accepted():
    with pytest.raises(ModelVerificationError, match="not an approved model"):
        ollama.OllamaProvider("llama3.1:70b")
    for host in ("http://192.168.1.20:11434", "http://example.com:11434", "http://0.0.0.0:11434"):
        with pytest.raises(ModelVerificationError, match="different model boundary"):
            ollama.OllamaProvider(QWEN, host=host)
    for host in ("http://localhost:11434", "http://127.0.0.1:11434", "http://[::1]:11434"):
        assert ollama.is_loopback(host)


def test_verify_checks_the_pinned_digest(no_live_api):
    fake = FakeOllama(no_live_api)
    assert ollama.OllamaProvider(QWEN).verify().digest == ollama.PINNED_DIGESTS[QWEN]
    fake.digests[QWEN] = "f" * 64
    with pytest.raises(ModelVerificationError, match="does not match"):
        ollama.OllamaProvider(QWEN).verify()
    del fake.digests[QWEN]
    with pytest.raises(ModelVerificationError, match="not installed"):
        ollama.OllamaProvider(QWEN).verify()


def test_chat_request_is_schema_constrained_deterministic_and_thinking_off(no_live_api):
    fake = FakeOllama(no_live_api)
    c = ollama.OllamaProvider(QWEN).complete("system text", "user text", SCHEMA, 200)
    assert (c.text, c.stop_reason) == (answer(), STOP)
    (body,) = fake.chats
    assert body["format"] == SCHEMA
    assert body["think"] is False
    assert body["stream"] is False
    assert body["options"] == {
        "temperature": 0,
        "seed": ollama.SEED,
        "num_ctx": ollama.NUM_CTX,
        "num_predict": 200,
    }
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


def test_length_and_context_overflow_are_reported(no_live_api):
    fake = FakeOllama(no_live_api, done_reason="length")
    provider = ollama.OllamaProvider(QWEN)
    assert provider.complete("s", "u", SCHEMA, 200).stop_reason == LENGTH
    fake.done_reason, fake.prompt_eval_count = "stop", ollama.NUM_CTX - 150
    assert provider.complete("s", "u", SCHEMA, 200).stop_reason == CONTEXT_OVERFLOW


def test_transport_failures_are_categories_without_hosts(no_live_api):
    fake = FakeOllama(no_live_api)
    fake.fail_with = 500
    provider = ollama.OllamaProvider(QWEN)
    with pytest.raises(ProviderError) as err:
        provider.complete("s", "u", SCHEMA, 200)
    assert str(err.value) == "http_500"
    no_live_api.post("http://localhost:11434/api/chat").mock(
        side_effect=httpx.ConnectTimeout("timed out")
    )
    with pytest.raises(ProviderError) as err:
        provider.complete("s", "u", SCHEMA, 200)
    assert str(err.value) == "timeout"
    assert "localhost" not in str(err.value)


# Anthropic ----------------------------------------------------------------------------


def anthropic_reply(stop: str = "end_turn", text: str | None = None) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "msg_synthetic",
            "type": "message",
            "role": "assistant",
            "model": anthropic.DEFAULT_MODEL,
            "content": [{"type": "text", "text": answer() if text is None else text}],
            "stop_reason": stop,
            "usage": {"input_tokens": 700, "output_tokens": 45},
        },
    )


def test_the_key_comes_only_from_the_environment(monkeypatch):
    with pytest.raises(anthropic.MissingCredentialError) as err:
        anthropic.AnthropicProvider.from_env()
    assert str(err.value) == "ANTHROPIC_API_KEY is not set"
    monkeypatch.setenv("ANTHROPIC_API_KEY", CANARY)
    provider = anthropic.AnthropicProvider.from_env()
    assert CANARY not in repr(provider)
    assert provider.verify().digest_state == "NOT_EXPOSED"


def test_request_uses_structured_outputs_and_keeps_the_key_in_a_header(
    no_live_api: respx.MockRouter, monkeypatch
):
    monkeypatch.setenv("ANTHROPIC_API_KEY", CANARY)
    route = no_live_api.post(anthropic.API_URL).mock(return_value=anthropic_reply())
    c = anthropic.AnthropicProvider.from_env().complete("system text", "user text", SCHEMA, 200)
    assert (c.text, c.stop_reason, c.input_tokens) == (answer(), STOP, 700)
    request = route.calls.last.request
    assert request.headers["x-api-key"] == CANARY
    assert request.headers["anthropic-version"] == "2023-06-01"
    body = json.loads(request.content)
    assert CANARY not in request.content.decode()
    assert body["model"] == "claude-haiku-4-5-20251001"
    assert body["temperature"] == 0
    assert body["max_tokens"] == 200
    assert body["system"] == "system text"
    assert body["messages"] == [{"role": "user", "content": "user text"}]
    assert body["output_config"] == {"format": {"type": "json_schema", "schema": SCHEMA}}
    assert "tools" not in body


def test_stop_reasons_and_errors_are_normalized_without_the_key(no_live_api, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", CANARY)
    route = no_live_api.post(anthropic.API_URL)
    provider = anthropic.AnthropicProvider.from_env()
    route.mock(return_value=anthropic_reply("max_tokens", '{"primary_class": "COR'))
    assert provider.complete("s", "u", SCHEMA, 200).stop_reason == LENGTH
    route.mock(return_value=anthropic_reply("refusal", ""))
    assert provider.complete("s", "u", SCHEMA, 200).stop_reason == REFUSAL
    route.mock(return_value=httpx.Response(401, json={"error": {"type": "authentication_error"}}))
    with pytest.raises(ProviderError) as err:
        provider.complete("s", "u", SCHEMA, 200)
    assert str(err.value) == "http_401" and CANARY not in repr(err.value)
