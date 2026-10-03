"""Mocked model providers for tests (respx). No test reaches Ollama or Anthropic."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import respx

from afterword.providers import ollama

QWEN = "qwen3:4b-instruct-2507-q4_K_M"
LLAMA = "llama3.1:8b-instruct-q4_K_M"


def answer(
    primary: str = "TECHNICAL_QUESTION",
    flags: list[str] | None = None,
    confidence: str = "MEDIUM",
    explanation: str = "Asks how a step works.",
) -> str:
    return json.dumps(
        {
            "primary_class": primary,
            "flags": flags or [],
            "confidence": confidence,
            "explanation": explanation,
        }
    )


class FakeOllama:
    """A loopback Ollama with the pinned models installed, answering from a function."""

    def __init__(
        self,
        router: respx.MockRouter,
        reply: Callable[[dict[str, Any]], str] | None = None,
        *,
        digests: dict[str, str] | None = None,
        done_reason: str = "stop",
        prompt_eval_count: int = 900,
    ) -> None:
        self.reply = reply or (lambda body: answer())
        self.digests = dict(ollama.PINNED_DIGESTS) if digests is None else digests
        self.done_reason = done_reason
        self.prompt_eval_count = prompt_eval_count
        self.chats: list[dict[str, Any]] = []
        self.unloads = 0
        self.fail_with: int | None = None
        base = "http://localhost:11434"
        router.get(f"{base}/api/tags").mock(side_effect=self._tags)
        router.post(f"{base}/api/chat").mock(side_effect=self._chat)
        router.post(f"{base}/api/generate").mock(side_effect=self._generate)

    def _tags(self, request: httpx.Request) -> httpx.Response:
        models = [
            {"name": name, "model": name, "digest": digest} for name, digest in self.digests.items()
        ]
        return httpx.Response(200, json={"models": models})

    def _chat(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        self.chats.append(body)
        if self.fail_with is not None:
            return httpx.Response(self.fail_with, json={"error": "synthetic failure"})
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "message": {"role": "assistant", "content": self.reply(body)},
                "done": True,
                "done_reason": self.done_reason,
                "prompt_eval_count": self.prompt_eval_count,
                "eval_count": 40,
                "load_duration": 1_500_000_000 if self.unloads else 0,
            },
        )

    def _generate(self, request: httpx.Request) -> httpx.Response:
        self.unloads += 1
        return httpx.Response(200, json={"done": True})

    @staticmethod
    def user_message(body: dict[str, Any]) -> str:
        return str(body["messages"][1]["content"])
