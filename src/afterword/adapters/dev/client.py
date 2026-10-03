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

BASE_URL: str = "https://dev.to"
ACCEPT: str = "application/vnd.forem.api-v1+json"
USER_AGENT: str = "afterword-probe/0.1 (read-only)"
ENV_VAR: str = "DEV_API_KEY"

# A deliberately wrong key, used once to confirm the API rejects bad credentials.
INVALID_KEY: str = "afterword-deliberately-invalid-key"

type AuthMode = Literal["key", "none", "invalid"]

_KEPT_HEADERS: frozenset[str] = frozenset(
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
_KEPT_HEADER_PREFIXES: tuple[str, ...] = ("x-ratelimit", "ratelimit", "x-rate-limit")
_RETRY_STATUSES: frozenset[int] = frozenset({429, 503})

# Keep httpx and httpcore quiet: at DEBUG they can emit request details.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class MissingCredentialError(RuntimeError):
    """Raised when ``DEV_API_KEY`` is needed but not set."""

    pass


def is_rate_limit_header(name: str) -> bool:
    """Report whether a response header carries rate-limit information.

    :param name: Header name, any case.
    :returns: ``True`` for ``Retry-After`` and the common rate-limit header families.
    """
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
        """Report whether the request succeeded with a JSON body.

        :returns: ``True`` for status 200 with a parsed JSON body.
        """
        return self.status == 200 and self.body_is_json

    def to_record(self) -> dict[str, Any]:
        """Serialize the exchange for saving. Contains no request headers.

        :returns: A JSON-ready record of the request, response, and retries.
        """
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
    """Read-only DEV client with request spacing and 429 backoff.

    The API key is held privately and attached only to outgoing request headers.
    """

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
        on_request: Callable[[], None] | None = None,
        backoff_wait: Callable[[int, float], None] | None = None,
    ) -> None:
        """Create a client.

        :param api_key: DEV API key, or ``None`` for unauthenticated use only.
        :param base_url: API host.
        :param min_interval: Minimum seconds between requests.
        :param max_retries: Retries for status 429 or 503 before giving up.
        :param backoff_base: First backoff delay in seconds when no ``Retry-After`` is sent.
        :param backoff_cap: Maximum backoff delay in seconds.
        :param sleep: Sleep function, injectable for tests.
        :param clock: Monotonic clock, injectable for tests.
        :param on_request: Called once before each HTTP request is sent, retries
            included. Receives nothing, so it cannot see the key or the path.
        :param backoff_wait: Waits out a retry delay, given the status that caused
            it and the delay in seconds (for a countdown). ``sleep`` when ``None``.
        """
        self.__api_key = api_key
        self._base_url = base_url
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_cap = backoff_cap
        self._sleep = sleep
        self._clock = clock
        self._on_request = on_request
        self._backoff_wait = backoff_wait
        self._last_request_at: float | None = None
        self._http = httpx.Client(base_url=base_url, timeout=30.0)

    @classmethod
    def from_env(cls, **kwargs: Any) -> DevClient:
        """Create a client with the key from ``DEV_API_KEY``.

        :param **kwargs: Passed to the constructor.
        :returns: A configured client.
        :raises MissingCredentialError: If ``DEV_API_KEY`` is not set.
        """
        key = os.environ.get(ENV_VAR)
        if not key:
            raise MissingCredentialError(f"{ENV_VAR} is not set")
        return cls(key, **kwargs)

    def __repr__(self) -> str:
        """Describe the client without revealing the key.

        :returns: The base URL and whether a key is present.
        """
        return f"DevClient(base_url={self._base_url!r}, has_key={self.__api_key is not None})"

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> DevClient:
        """Enter a ``with`` block.

        :returns: This client.
        """
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the client on leaving a ``with`` block.

        :param *exc: Exception information, ignored.
        """
        self.close()

    def get(
        self, path: str, params: dict[str, Any] | None = None, *, auth: AuthMode = "key"
    ) -> Exchange:
        """Send one GET, retrying on 429 and 503 within the retry limit.

        Transport errors are returned as an exchange with status 0 and the
        exception type name only, never its message.

        :param path: Request path, such as ``/api/comments``.
        :param params: Query parameters.
        :param auth: ``key`` to send the API key, ``none`` for an anonymous request,
            ``invalid`` for a deliberately wrong key.
        :returns: The final exchange, including any retries.
        """
        params = dict(params or {})
        retries: list[dict[str, Any]] = []
        attempt = 0
        while True:
            self._throttle()
            requested_at = datetime.now(UTC).isoformat(timespec="seconds")
            if self._on_request is not None:
                self._on_request()
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
                if self._backoff_wait is not None:
                    self._backoff_wait(response.status_code, delay)
                else:
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
        return min(self._backoff_base * 2.0**attempt, self._backoff_cap)

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
