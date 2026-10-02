"""Read-only HTTP client for the DEV (Forem v1) API.

This is the only module that reads DEV_API_KEY (ADR-006). The key is attached
to outgoing requests and nowhere else: it is not stored on the httpx client
defaults, not included in reprs or exceptions, and never part of the request
metadata that the probe saves. Only allowlisted response headers are kept.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any, Literal

import httpx

BASE_URL = "https://dev.to"
ACCEPT = "application/vnd.forem.api-v1+json"
USER_AGENT = "afterword-probe/0.1 (read-only)"
ENV_VAR = "DEV_API_KEY"

# A deliberately wrong key, used once to confirm the API rejects bad credentials.
INVALID_KEY = "afterword-deliberately-invalid-key"

AuthMode = Literal["key", "none", "invalid"]

_KEPT_HEADERS = frozenset(
    {
        "age",
        "cache-control",
        "content-type",
        "date",
        "etag",
        "last-modified",
        "link",
        "retry-after",
        "vary",
        "via",
        "warning",
        "x-cache",
        "x-cache-hits",
        "x-total-count",
    }
)
_KEPT_HEADER_PREFIXES = ("x-ratelimit", "ratelimit", "x-rate-limit")
_RETRY_STATUSES = frozenset({429, 503})

# Keep httpx and httpcore quiet: at DEBUG they can emit request details.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class MissingCredentialError(RuntimeError):
    pass


def is_rate_limit_header(name: str) -> bool:
    return name.lower().startswith(_KEPT_HEADER_PREFIXES) or name.lower() == "retry-after"


def _kept_headers(headers: httpx.Headers) -> dict[str, str]:
    kept = {}
    for name, value in headers.items():
        lower = name.lower()
        if lower in _KEPT_HEADERS or lower.startswith(_KEPT_HEADER_PREFIXES):
            kept[lower] = value
    return kept


@dataclass
class Exchange:
    """One logical GET, including any retries. Safe to persist."""

    path: str
    params: dict[str, Any]
    auth: AuthMode
    requested_at: str
    status: int
    headers: dict[str, str]
    header_names: list[str]
    body: Any
    body_is_json: bool
    body_bytes: int
    error: str | None = None
    retries: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == 200 and self.body_is_json

    def to_record(self) -> dict[str, Any]:
        return {
            "request": {
                "method": "GET",
                "path": self.path,
                "params": self.params,
                "auth": self.auth,
                "requested_at": self.requested_at,
            },
            "response": {
                "status": self.status,
                "headers": self.headers,
                "header_names": self.header_names,
                "body_is_json": self.body_is_json,
                "body_bytes": self.body_bytes,
                "body": self.body,
                "error": self.error,
            },
            "retries": self.retries,
        }


class DevClient:
    def __init__(
        self,
        api_key: str | None,
        *,
        base_url: str = BASE_URL,
        min_interval: float = 1.0,
        max_retries: int = 4,
        backoff_base: float = 2.0,
        backoff_cap: float = 120.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.__api_key = api_key
        self._base_url = base_url
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_cap = backoff_cap
        self._sleep = sleep
        self._clock = clock
        self._last_request_at: float | None = None
        self._http = httpx.Client(base_url=base_url, timeout=30.0)

    @classmethod
    def from_env(cls, **kwargs: Any) -> DevClient:
        key = os.environ.get(ENV_VAR)
        if not key:
            raise MissingCredentialError(f"{ENV_VAR} is not set")
        return cls(key, **kwargs)

    def __repr__(self) -> str:
        return f"DevClient(base_url={self._base_url!r}, has_key={self.__api_key is not None})"

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> DevClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def get(
        self, path: str, params: dict[str, Any] | None = None, *, auth: AuthMode = "key"
    ) -> Exchange:
        params = dict(params or {})
        retries: list[dict[str, Any]] = []
        attempt = 0
        while True:
            self._throttle()
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            try:
                response = self._http.get(path, params=params, headers=self._headers(auth))
            except httpx.HTTPError as exc:
                # The exception type is enough; its message is not persisted.
                return Exchange(
                    path=path,
                    params=params,
                    auth=auth,
                    requested_at=requested_at,
                    status=0,
                    headers={},
                    header_names=[],
                    body=None,
                    body_is_json=False,
                    body_bytes=0,
                    error=type(exc).__name__,
                    retries=retries,
                )
            if response.status_code in _RETRY_STATUSES and attempt < self._max_retries:
                delay = self._retry_delay(response, attempt)
                try:
                    error_body: Any = response.json()  # server-generated error, not user content
                except ValueError:
                    error_body = None
                retries.append(
                    {
                        "status": response.status_code,
                        "retry_after": response.headers.get("retry-after"),
                        "waited_s": round(delay, 3),
                        "headers": _kept_headers(response.headers),
                        "body": error_body,
                    }
                )
                self._sleep(delay)
                attempt += 1
                continue
            return self._exchange(path, params, auth, requested_at, response, retries)

    def _headers(self, auth: AuthMode) -> dict[str, str]:
        headers = {"accept": ACCEPT, "user-agent": USER_AGENT}
        if auth == "key":
            if not self.__api_key:
                raise MissingCredentialError(f"{ENV_VAR} is not set")
            headers["api-key"] = self.__api_key
        elif auth == "invalid":
            headers["api-key"] = INVALID_KEY
        return headers

    def _throttle(self) -> None:
        if self._last_request_at is not None:
            wait = self._min_interval - (self._clock() - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
        self._last_request_at = self._clock()

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return min(max(float(retry_after), 0.0), self._backoff_cap)
            except ValueError:
                try:
                    when = parsedate_to_datetime(retry_after)
                    delta = (when - datetime.now(UTC)).total_seconds()
                    return min(max(delta, 0.0), self._backoff_cap)
                except (TypeError, ValueError):
                    pass
        return min(self._backoff_base * (2**attempt), self._backoff_cap)

    @staticmethod
    def _exchange(
        path: str,
        params: dict[str, Any],
        auth: AuthMode,
        requested_at: str,
        response: httpx.Response,
        retries: list[dict[str, Any]],
    ) -> Exchange:
        try:
            body: Any = response.json()
            body_is_json = True
        except ValueError:
            body = None
            body_is_json = False
        return Exchange(
            path=path,
            params=params,
            auth=auth,
            requested_at=requested_at,
            status=response.status_code,
            headers=_kept_headers(response.headers),
            header_names=sorted({name.lower() for name in response.headers}),
            body=body,
            body_is_json=body_is_json,
            body_bytes=len(response.content),
            retries=retries,
        )
