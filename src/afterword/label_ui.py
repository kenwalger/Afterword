"""Browser labeling interface (``afterword label-ui``): a local HTTP transport.

Another transport over the same service functions as ``afterword label``
(ADR-012). Batches, their order, label records, notes, and resumability are
those of :class:`afterword.labeling.LabelBatch`; this module only serves one
page and turns its requests into service calls.

The server is for the author's own machine and nothing else:

- it binds to ``127.0.0.1`` only;
- every request must name that host in its ``Host`` header (a defense against
  DNS rebinding);
- every request must carry a random per-session token, given in the URL
  printed at start, so another page in the browser cannot read or write labels;
- writes accept only ``application/json`` bodies, which a cross-site form
  cannot send without a preflight this server never answers;
- request logging is off, and the page loads nothing from the network.

Comment text reaches the page as JSON and is inserted with ``textContent``
only, never as HTML.
"""

from __future__ import annotations

import json
import secrets
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from afterword import labeling, service, taxonomy
from afterword.label_ui_page import PAGE

HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8765
MAX_BODY: int = 64 * 1024
TOKEN_HEADER: str = "X-Afterword-Token"

# Keyboard: digits choose the class in TAXONOMY.md precedence order (0 is the tenth).
CLASS_KEYS: tuple[str, ...] = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")
# Letters toggle labeler flags. h, t, s, q, g, e, w are commands on the page.
FLAG_KEYS: dict[str, str] = {
    "NEEDS_THREAD_CONTEXT": "n",
    "CONTAINS_CODE": "c",
    "CONTAINS_LINK": "l",
    "REFERENCES_SPECIFIC_CLAIM": "r",
    "ADDRESSED_TO_OTHER_COMMENTER": "o",
    "HOSTILE_TONE": "x",
    "POSSIBLE_INSTRUCTION_TEXT": "i",
}
COMMAND_KEYS: frozenset[str] = frozenset("htsqgew")


def taxonomy_payload() -> dict[str, Any]:
    """Describe the classes and labeler flags with their keys and one-line definitions.

    :returns: JSON-ready lists, classes in precedence order, flags in table order.
    """
    return {
        "classes": [
            {"name": name, "key": key, "definition": taxonomy.CLASS_DEFINITIONS[name]}
            for name, key in zip(labeling.CLASSES, CLASS_KEYS, strict=True)
        ],
        "flags": [
            {"name": name, "key": FLAG_KEYS[name], "definition": taxonomy.FLAG_DEFINITIONS[name]}
            for name in labeling.LABELER_FLAGS
        ],
        "structural_flag": {
            "name": taxonomy.REPLY_TO_AUTHOR,
            "definition": taxonomy.FLAG_DEFINITIONS[taxonomy.REPLY_TO_AUTHOR],
        },
    }


@dataclass
class BatchOptions:
    """How batches are chosen: the same options as ``afterword label``."""

    pass_name: str = "initial"
    corpus_version: str = labeling.DEFAULT_CORPUS_VERSION
    corpus_set: str = labeling.DEFAULT_CORPUS_SET
    batch_size: int = labeling.MAX_BATCH
    only_ids: set[str] | None = None
    post_order: str = "published"
    seed: int | None = None


class RequestError(Exception):
    """A request the page should be told was refused. The message is safe to show."""


@dataclass
class LabelUI:
    """State of one browser labeling session: the current batch and position.

    Requests are handled one at a time (a single-threaded server), so no lock
    is needed.
    """

    session: service.LabelingSession
    root: Path
    options: BatchOptions
    monotonic: Callable[[], float] = time.monotonic
    batch: labeling.LabelBatch | None = None
    index: int = 0
    shown_at: float | None = None
    stopped: bool = False
    batches_started: int = 0
    labeled_total: int = 0
    _taxonomy: dict[str, Any] = field(default_factory=taxonomy_payload)

    def start_batch(self) -> None:
        """Start the next batch, if any comment is left to label."""
        self.batch = service.start_label_batch(
            self.session,
            root=self.root,
            pass_name=self.options.pass_name,
            corpus_version=self.options.corpus_version,
            corpus_set=self.options.corpus_set,
            batch_size=self.options.batch_size,
            only_ids=self.options.only_ids,
            post_order=self.options.post_order,
            seed=self.options.seed,
        )
        self.index = 0
        self.shown_at = None
        if self.batch is not None:
            self.batches_started += 1

    def _finished(self) -> bool:
        return self.batch is None or self.index >= len(self.batch.items)

    def _complete_if_done(self) -> None:
        if self.batch is not None and self.index >= len(self.batch.items):
            service.end_label_batch(self.batch, ended_by="complete")

    def state(self) -> dict[str, Any]:
        """Describe what the page should show now, starting the clock on a new comment.

        :returns: JSON-ready state.
        """
        base: dict[str, Any] = {
            "taxonomy": self._taxonomy,
            "pass": self.options.pass_name,
            "progress": self.progress(),
        }
        if self.stopped:
            return base | {"status": "stopped", "labeled_total": self.labeled_total}
        if self.batch is None:
            return base | {"status": "nothing_left", "labeled_total": self.labeled_total}
        batch = self.batch
        counts = {
            "batch_id": batch.context().batch_id,
            "batch_size": len(batch.items),
            "labeled": batch.saved,
            "skipped": batch.skipped,
            "still_unlabeled": batch.still_unlabeled,
            "labeled_total": self.labeled_total,
        }
        if self._finished():
            return base | counts | {"status": "batch_done"}
        if self.shown_at is None:
            self.shown_at = self.monotonic()
        return (
            base
            | counts
            | {
                "status": "labeling",
                "position": self.index + 1,
                "comment": service.label_view(batch, self.index),
            }
        )

    def progress(self) -> dict[str, int]:
        """Count progress for the badge: totals only, never classes or grades.

        :returns: ``labeled`` (initial pass), ``relabeled`` (calibration pass),
            and ``eligible`` comments in the run.
        """
        counts = service.label_progress(
            self.session, root=self.root, corpus_version=self.options.corpus_version
        )
        return {
            "labeled": counts.labeled,
            "relabeled": counts.relabeled,
            "eligible": counts.eligible,
        }

    def _current(self, comment_id: Any) -> labeling.LabelBatch:
        if self.stopped or self.batch is None or self._finished():
            raise RequestError("no comment is open for labeling")
        if comment_id != self.batch.items[self.index].source_object_id:
            raise RequestError("this comment is no longer the current one; reload the page")
        return self.batch

    def submit(self, body: dict[str, Any]) -> None:
        """Save the label for the current comment and move on.

        :param body: The page's fields.
        :raises RequestError: If the comment is not current or a field is invalid.
        """
        batch = self._current(body.get("comment_id"))
        primary = body.get("primary_class")
        flags = body.get("flags")
        prospective = body.get("prospective")
        retrospective = body.get("retrospective")
        reason = body.get("reason", "")
        note = body.get("note", "")
        if not isinstance(primary, str):
            raise RequestError("choose a class")
        if not isinstance(flags, list) or not all(isinstance(f, str) for f in flags):
            raise RequestError("flags must be a list of names")
        if not isinstance(prospective, int) or isinstance(prospective, bool):
            raise RequestError("set the prospective grade")
        if retrospective is not None and (
            not isinstance(retrospective, int) or isinstance(retrospective, bool)
        ):
            raise RequestError("the retrospective grade must be 0 to 3 or empty")
        if not isinstance(reason, str) or not isinstance(note, str):
            raise RequestError("reason and note must be text")
        started = self.shown_at if self.shown_at is not None else self.monotonic()
        try:
            service.save_label(
                batch,
                self.index,
                primary=primary,
                flags=flags,
                prospective=prospective,
                retrospective=retrospective,
                reason=reason,
                note=note,
                duration_seconds=self.monotonic() - started,
            )
        except service.ServiceError as exc:
            raise RequestError(str(exc)) from None
        self.labeled_total += 1
        self._advance()

    def skip(self, body: dict[str, Any]) -> None:
        """Pass over the current comment without a label.

        Refused with :class:`RequestError` if the comment is not the current one.

        :param body: The page's fields: ``comment_id`` and an optional ``note``.
        """
        batch = self._current(body.get("comment_id"))
        note = body.get("note", "")
        service.skip_label(batch, self.index, note=note if isinstance(note, str) else "")
        self._advance()

    def _advance(self) -> None:
        self.index += 1
        self.shown_at = None
        self._complete_if_done()

    def next_batch(self) -> None:
        """Start another batch after the current one is done.

        :raises RequestError: If the current batch is still in progress.
        """
        if self.stopped:
            raise RequestError("the session has stopped")
        if not self._finished():
            raise RequestError("the current batch is not done")
        self.start_batch()

    def stop(self) -> None:
        """End the session, closing an unfinished batch as quit."""
        if self.batch is not None and not self._finished():
            service.end_label_batch(self.batch, ended_by="quit")
        self.stopped = True


def make_handler(
    ui: LabelUI, token: str, port: Callable[[], int], on_stop: Callable[[], None]
) -> type[BaseHTTPRequestHandler]:
    """Build the request handler class for one session.

    :param ui: Session state.
    :param token: The per-session secret every request must carry.
    :param port: The bound port, for the ``Host`` check.
    :param on_stop: Called after the stop request is answered.
    :returns: A handler class for :class:`http.server.HTTPServer`.
    """

    class Handler(BaseHTTPRequestHandler):
        server_version = "afterword-label-ui"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            """Log nothing: request lines carry the session token.

            :param format: Unused.
            :param *args: Unused.
            """

        def _host_ok(self) -> bool:
            allowed = {f"{HOST}:{port()}", f"localhost:{port()}"}
            return self.headers.get("Host", "") in allowed

        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        def _refuse(self, status: HTTPStatus, message: str) -> None:
            self._json(status, {"error": message})

        def do_GET(self) -> None:
            """Serve the page or the current state."""
            if not self._host_ok():
                self._refuse(HTTPStatus.FORBIDDEN, "wrong host")
                return
            url = urlparse(self.path)
            if url.path == "/":
                if parse_qs(url.query).get("t", [""])[0] != token:
                    self._refuse(HTTPStatus.FORBIDDEN, "open the URL printed in the terminal")
                    return
                page = PAGE.replace("__TOKEN__", token).encode("utf-8")
                self._send(HTTPStatus.OK, page, "text/html; charset=utf-8")
                return
            if url.path == "/api/state":
                if self.headers.get(TOKEN_HEADER) != token:
                    self._refuse(HTTPStatus.FORBIDDEN, "missing session token")
                    return
                self._json(HTTPStatus.OK, ui.state())
                return
            self._refuse(HTTPStatus.NOT_FOUND, "not found")

        def do_POST(self) -> None:
            """Apply one write: label, skip, next batch, or stop."""
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if not 0 <= length <= MAX_BODY:
                self.close_connection = True
                self._refuse(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "request too large")
                return
            # Read the body before any refusal: a socket closed with unread data
            # resets the connection on Windows, and the page sees no answer.
            raw = self.rfile.read(length)
            if not self._host_ok():
                self._refuse(HTTPStatus.FORBIDDEN, "wrong host")
                return
            if self.headers.get(TOKEN_HEADER) != token:
                self._refuse(HTTPStatus.FORBIDDEN, "missing session token")
                return
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                self._refuse(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "JSON only")
                return
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                self._refuse(HTTPStatus.BAD_REQUEST, "not JSON")
                return
            if not isinstance(body, dict):
                self._refuse(HTTPStatus.BAD_REQUEST, "expected an object")
                return
            actions: dict[str, Callable[[], None]] = {
                "/api/label": lambda: ui.submit(body),
                "/api/skip": lambda: ui.skip(body),
                "/api/next-batch": ui.next_batch,
                "/api/stop": ui.stop,
            }
            action = actions.get(urlparse(self.path).path)
            if action is None:
                self._refuse(HTTPStatus.NOT_FOUND, "not found")
                return
            try:
                action()
            except RequestError as exc:
                self._refuse(HTTPStatus.CONFLICT, str(exc))
                return
            self._json(HTTPStatus.OK, ui.state())
            if ui.stopped:
                on_stop()

    return Handler


@dataclass
class Server:
    """A running label UI server and its session URL."""

    httpd: HTTPServer
    ui: LabelUI
    token: str

    @property
    def url(self) -> str:
        """The session URL, including its token.

        :returns: An ``http://127.0.0.1`` URL.
        """
        return f"http://{HOST}:{self.httpd.server_address[1]}/?t={self.token}"

    def serve(self) -> None:
        """Serve until the page stops the session or the process is interrupted.

        An unfinished batch is closed as quit either way.
        """
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.ui.stop()
            self.httpd.server_close()


def create_server(ui: LabelUI, *, port: int = DEFAULT_PORT) -> Server:
    """Bind the server to 127.0.0.1 and create its session token.

    :param ui: Session state; its first batch should already be started.
    :param port: TCP port, or 0 for any free port.
    :returns: The server, not yet serving.
    """
    token = secrets.token_urlsafe(24)
    holder: list[HTTPServer] = []

    def bound_port() -> int:
        return int(holder[0].server_address[1])

    def on_stop() -> None:
        threading.Thread(target=holder[0].shutdown, daemon=True).start()

    httpd = HTTPServer((HOST, port), make_handler(ui, token, bound_port, on_stop))
    holder.append(httpd)
    return Server(httpd, ui, token)
