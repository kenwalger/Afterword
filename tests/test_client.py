from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from afterword.adapters.dev.client import ACCEPT, DevClient, MissingCredentialError
from tests.conftest import FAKE_KEY, load


def make_client(**kwargs: Any) -> tuple[DevClient, list[float]]:
    waits: list[float] = []
    kwargs.setdefault("min_interval", 0.0)
    return DevClient(FAKE_KEY, sleep=waits.append, **kwargs), waits


def test_sends_key_and_forem_accept_header(no_live_api):
    route = no_live_api.get("https://dev.to/api/users/me").respond(200, json={"id": 1})
    client, _ = make_client()
    ex = client.get("/api/users/me")
    sent = route.calls.last.request
    assert ex.ok
    assert sent.headers["api-key"] == FAKE_KEY
    assert sent.headers["accept"] == ACCEPT


def test_unauthenticated_request_sends_no_key(no_live_api):
    route = no_live_api.get("https://dev.to/api/comments").respond(200, json=[])
    client, _ = make_client()
    client.get("/api/comments", {"a_id": 1}, auth="none")
    assert "api-key" not in route.calls.last.request.headers


def test_invalid_mode_sends_a_non_secret_placeholder(no_live_api):
    route = no_live_api.get("https://dev.to/api/users/me").respond(401, json=load("error-401.json"))
    client, _ = make_client()
    ex = client.get("/api/users/me", auth="invalid")
    assert ex.status == 401
    assert route.calls.last.request.headers["api-key"] != FAKE_KEY


def test_429_honors_retry_after(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").mock(
        side_effect=[
            httpx.Response(429, json=load("error-429.json"), headers={"retry-after": "3"}),
            httpx.Response(200, json={"id": 1}),
        ]
    )
    client, waits = make_client()
    ex = client.get("/api/users/me")
    assert ex.ok
    assert waits == [3.0]
    (retry,) = ex.retries
    assert retry["status"] == 429
    assert retry["retry_after"] == "3"
    assert retry["waited_s"] == 3.0
    assert retry["headers"]["retry-after"] == "3"
    assert retry["body"] == load("error-429.json")


def test_429_without_retry_after_backs_off_exponentially(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").mock(
        side_effect=[httpx.Response(429), httpx.Response(429), httpx.Response(200, json={})]
    )
    client, waits = make_client(backoff_base=2.0)
    assert client.get("/api/users/me").ok
    assert waits == [2.0, 4.0]


def test_gives_up_after_max_retries(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").respond(429)
    client, waits = make_client(max_retries=2)
    ex = client.get("/api/users/me")
    assert ex.status == 429
    assert len(ex.retries) == 2
    assert len(waits) == 2


def test_throttle_spaces_consecutive_requests(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").respond(200, json={})
    waits: list[float] = []
    client = DevClient(FAKE_KEY, min_interval=1.5, sleep=waits.append, clock=lambda: 100.0)
    client.get("/api/users/me")
    client.get("/api/users/me")
    assert waits == [1.5]


def test_only_allowlisted_header_values_are_kept(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").respond(
        200,
        json={},
        headers={"set-cookie": "session=secret", "x-ratelimit-remaining": "9", "server": "x"},
    )
    client, _ = make_client()
    ex = client.get("/api/users/me")
    assert ex.headers.get("x-ratelimit-remaining") == "9"
    assert "set-cookie" not in ex.headers
    assert "set-cookie" in ex.header_names
    assert "session=secret" not in json.dumps(ex.to_record())


def test_key_absent_from_repr_and_record(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").respond(200, json={})
    client, _ = make_client()
    ex = client.get("/api/users/me")
    assert FAKE_KEY not in repr(client)
    assert FAKE_KEY not in json.dumps(ex.to_record())


def test_transport_error_records_type_only(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").mock(
        side_effect=httpx.ConnectError(f"failed {FAKE_KEY}")
    )
    client, _ = make_client()
    ex = client.get("/api/users/me")
    assert ex.status == 0
    assert ex.error == "ConnectError"
    assert FAKE_KEY not in json.dumps(ex.to_record())


def test_from_env_requires_key():
    with pytest.raises(MissingCredentialError):
        DevClient.from_env()


def test_from_env_reads_key(monkeypatch, no_live_api):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    route = no_live_api.get("https://dev.to/api/users/me").respond(200, json={})
    DevClient.from_env(min_interval=0.0).get("/api/users/me")
    assert route.calls.last.request.headers["api-key"] == FAKE_KEY
