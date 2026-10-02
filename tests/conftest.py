"""Test harness. No test may reach the live DEV API.

`no_live_api` is autouse: it removes DEV_API_KEY from the environment and
installs a respx router that fails any request without a matching mock.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "dev-api" / "source"
FAKE_KEY = "canary-dev-key-0f9e8d7c6b5a4f3e"


def load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def no_live_api(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DEV_API_KEY", raising=False)
    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        yield router


class FakeDev:
    """In-memory DEV API built from the synthetic fixtures."""

    def __init__(self, router: respx.MockRouter) -> None:
        self.me = load("users-me.json")
        self.articles = load("articles-me-published.json")
        self.article = load("article.json")
        second = copy.deepcopy(load("comments-by-article.json")[1])
        # Real id_codes are strings but some are all digits; they must never become ints.
        second.update(id_code="4821", created_at="2026-08-18T11:00:00Z")
        self.comments: dict[int, list[dict[str, Any]]] = {
            9000001: load("comments-by-article.json"),
            9000002: [second],
            9000003: [],
        }
        self.single = {"s1a1": load("comment-with-descendants.json")}
        self.calls: list[httpx.Request] = []

        host = {"method": "GET", "host": "dev.to"}
        router.route(**host, path="/api/users/me").mock(side_effect=self._me)
        router.route(**host, path="/api/articles/me/published").mock(side_effect=self._list)
        router.route(**host, path__regex=r"^/api/articles/\d+$").mock(side_effect=self._article)
        router.route(**host, path__regex=r"^/api/articles/[^/]+/[^/]+$").mock(
            side_effect=self._article_by_path
        )
        router.route(**host, path="/api/comments").mock(side_effect=self._comments)
        router.route(**host, path__regex=r"^/api/comments/[^/]+$").mock(side_effect=self._single)

    def _authorized(self, request: httpx.Request) -> bool:
        self.calls.append(request)
        return request.headers.get("api-key") == FAKE_KEY

    def _me(self, request: httpx.Request) -> httpx.Response:
        if not self._authorized(request):
            return httpx.Response(401, json=load("error-401.json"))
        return httpx.Response(200, json=self.me, headers={"set-cookie": "session=abc"})

    def _list(self, request: httpx.Request) -> httpx.Response:
        if not self._authorized(request):
            return httpx.Response(401, json=load("error-401.json"))
        page = int(request.url.params.get("page", 1))
        per_page = int(request.url.params.get("per_page", 30))
        start = (page - 1) * per_page
        return httpx.Response(200, json=self.articles[start : start + per_page])

    def _article(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        article_id = int(request.url.path.rsplit("/", 1)[1])
        listed = {a["id"]: a for a in self.articles}
        if article_id not in listed:
            return httpx.Response(404, json={"error": "not found", "status": 404})
        body = copy.deepcopy(self.article)
        body.update(id=article_id, comments_count=listed[article_id]["comments_count"])
        return httpx.Response(200, json=body)

    def _article_by_path(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        path = request.url.path.removeprefix("/api/articles")
        match = next((a for a in self.articles if a["path"] == path), None)
        if match is None:
            return httpx.Response(404, json={"error": "not found", "status": 404})
        return httpx.Response(200, json=match)

    def _comments(self, request: httpx.Request) -> httpx.Response:
        # Public. Returns every thread by default, but pages top-level threads when
        # page/per_page are sent (observed live on 2026-10-02; not documented).
        self.calls.append(request)
        params = request.url.params
        roots = self.comments.get(int(params["a_id"]), [])
        if "per_page" in params:
            per_page = int(params["per_page"])
            start = (int(params.get("page", 1)) - 1) * per_page
            roots = roots[start : start + per_page]
        return httpx.Response(
            200,
            json=roots,
            headers={"x-ratelimit-remaining": "29", "cache-control": "public, max-age=0"},
        )

    def _single(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        id_code = request.url.path.rsplit("/", 1)[1]
        if id_code not in self.single:
            return httpx.Response(404, json={"error": "not found", "status": 404})
        return httpx.Response(200, json=self.single[id_code])


@pytest.fixture
def fake_dev(no_live_api: respx.MockRouter) -> FakeDev:
    return FakeDev(no_live_api)
