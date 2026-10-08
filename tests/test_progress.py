from __future__ import annotations

import io
from datetime import UTC, datetime

import httpx

from afterword import cli
from afterword.adapters.dev.client import DevClient
from afterword.progress import StatusLine, format_elapsed
from tests.conftest import FAKE_KEY
from tests.test_probe import COMMENT_TEXT_AND_NAMES


def status(interactive: bool) -> tuple[StatusLine, io.StringIO, list[float]]:
    stream = io.StringIO()
    clock = iter(float(i) for i in range(1000))
    slept: list[float] = []
    line = StatusLine(
        stream,
        interactive=interactive,
        now=lambda: datetime(2026, 10, 3, 9, 0, 0, tzinfo=UTC),
        monotonic=lambda: next(clock),
        sleep=slept.append,
    )
    return line, stream, slept


def test_format_elapsed():
    assert format_elapsed(0) == "0s"
    assert format_elapsed(42.4) == "42s"
    assert format_elapsed(307) == "5m 07s"
    assert format_elapsed(3723) == "1h 02m 03s"


def test_interactive_line_redraws_in_place_and_counts_down():
    line, stream, slept = status(interactive=True)
    line.start("probe")
    line.request()
    line.step("comments", 3, 138)
    line.wait(429, 2.5)
    line.finish("probe")
    out = stream.getvalue()
    assert out.startswith("probe started 2026-10-03 09:00:00 UTC\n")
    assert "\rrequests" not in out  # every redraw starts with the elapsed time
    assert "article 3 of 138 (comments)" in out
    # The countdown sleeps in steps of at most one second and redraws after each.
    assert "429: waiting 2s" in out
    assert "429s 1" in out
    assert slept == [1.0, 1.0, 0.5]
    assert out.rstrip("\n").splitlines()[-1].startswith("probe finished 2026-10-03 09:00:00 UTC")
    assert "elapsed" in out
    # One logical line while running: redraws use carriage returns, not newlines.
    assert out.count("\n") == 3


def test_captured_output_prints_occasional_plain_lines():
    line, stream, _ = status(interactive=False)
    line.start("probe")
    for n in range(1, 51):
        line.request()
        line.step("details", n, 50)
    line.wait(429, 3)
    line.finish("probe")
    out = stream.getvalue()
    assert "\r" not in out
    lines = out.splitlines()
    # start, phase change (1), 25, 50, one line for the wait, finish
    assert len(lines) == 6
    assert "article 25 of 50 (article details)" in out
    assert "429: waiting 3s" in out


def test_client_reports_requests_and_hands_waits_to_the_status_line(no_live_api):
    no_live_api.get("https://dev.to/api/users/me").mock(
        side_effect=[
            httpx.Response(429, headers={"retry-after": "3"}),
            httpx.Response(200, json={}),
        ]
    )
    calls: list[str] = []
    waits: list[tuple[int, float]] = []
    slept: list[float] = []
    client = DevClient(
        FAKE_KEY,
        min_interval=0.0,
        sleep=slept.append,
        on_request=lambda: calls.append("request"),
        backoff_wait=lambda status, seconds: waits.append((status, seconds)),
    )
    assert client.get("/api/users/me").ok
    assert calls == ["request", "request"]
    assert waits == [(429, 3.0)]
    assert slept == []  # the waiter did the waiting


def test_probe_console_shows_progress_times_and_nothing_private(
    tmp_path, fake_dev, monkeypatch, capsys
):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    assert cli.main(["--root", str(tmp_path), "probe", "--min-interval", "0"]) == 0
    captured = capsys.readouterr()
    # Captured output is not a terminal: plain lines only.
    assert "\r" not in captured.err
    assert "probe run " in captured.err and " started " in captured.err
    assert " finished " in captured.err and "elapsed" in captured.err
    assert "article 1 of 3 (comments)" in captured.err
    for value in (*COMMENT_TEXT_AND_NAMES, FAKE_KEY, "synthetic_author", "Synthetic Author"):
        assert value not in captured.out + captured.err


def test_unresolved_article_scope_never_prints_the_path(tmp_path, fake_dev, monkeypatch, capsys):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    url = "https://dev.to/some_handle/no-such-post"
    assert (
        cli.main(["--root", str(tmp_path), "probe", "--min-interval", "0", "--article", url]) == 1
    )
    captured = capsys.readouterr()
    assert "some_handle" not in captured.out + captured.err
    assert "scope article:unresolved" in captured.out


def test_classify_counts_comments_not_articles():
    stream = io.StringIO()
    line = StatusLine(stream, interactive=False)
    line.start("classify")
    line.step("classify", 25, 458)
    out = stream.getvalue()
    assert "comment 25 of 458 (classify)" in out and "article" not in out
