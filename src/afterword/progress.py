"""Console progress for long commands: one updating status line.

The line carries counts only (requests sent, article N of total, 429 waits),
never comment text, names, handles, or the API key, so the console stays safe
to share. On a terminal the line is redrawn in place. When output is captured
(not a terminal), only occasional plain lines are printed, so a captured log
stays short.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TextIO

# Without a terminal, print one line per this many articles, plus phase changes and waits.
CAPTURED_EVERY: int = 25

_PHASES: dict[str, str] = {
    "account": "checking account",
    "listing": "listing articles",
    "details": "article details",
    "comments": "comments",
    "thread checks": "thread checks",
}


def format_elapsed(seconds: float) -> str:
    """Format a duration for people.

    :param seconds: Duration in seconds.
    :returns: Such as ``42s``, ``5m 07s``, or ``1h 02m 03s``.
    """
    total = max(round(seconds), 0)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def _clock_time(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


class StatusLine:
    """A single status line for a running probe."""

    def __init__(
        self,
        stream: TextIO | None = None,
        *,
        interactive: bool | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a status line.

        :param stream: Where to write; standard error when ``None``.
        :param interactive: Redraw in place; detected from the stream when ``None``.
        :param now: Wall clock for start and end times.
        :param monotonic: Clock for elapsed time.
        :param sleep: Sleep function for waits, injectable for tests.
        """
        self._stream = stream if stream is not None else sys.stderr
        if interactive is None:
            isatty = getattr(self._stream, "isatty", None)
            interactive = bool(isatty and isatty())
        self._interactive = interactive
        self._now = now
        self._monotonic = monotonic
        self._sleep = sleep
        self._t0: float | None = None
        self._width = 0
        self.requests = 0
        self.waits_429 = 0
        self._phase = ""
        self._current = 0
        self._total = 0
        self._waiting: str = ""

    # Lifecycle ----------------------------------------------------------------

    def start(self, label: str) -> datetime:
        """Print the start time and begin timing.

        :param label: What is starting, such as ``probe``.
        :returns: The start time.
        """
        started = self._now()
        self._t0 = self._monotonic()
        self._print(f"{label} started {_clock_time(started)}")
        return started

    def finish(self, label: str) -> float:
        """End the status line and print the end time and elapsed time.

        :param label: What has finished, such as ``probe``.
        :returns: Elapsed seconds.
        """
        elapsed = self._elapsed()
        if self._interactive and self._width:
            self._stream.write("\n")
            self._width = 0
        self._print(
            f"{label} finished {_clock_time(self._now())}, elapsed {format_elapsed(elapsed)}"
        )
        return elapsed

    # Events -------------------------------------------------------------------

    def request(self) -> None:
        """Count one HTTP request sent, including retries."""
        self.requests += 1
        self._draw()

    def step(self, phase: str, current: int = 0, total: int = 0) -> None:
        """Report the current step.

        :param phase: Step name, such as ``comments``.
        :param current: Article number within the step (1-based), or page number.
        :param total: Number of articles in the step, or 0 when not counted.
        """
        changed = phase != self._phase
        self._phase, self._current, self._total = phase, current, total
        if self._interactive:
            self._draw()
        elif changed or (total and (current % CAPTURED_EVERY == 0 or current == total)):
            self._print(self._text())

    def wait(self, status: int, seconds: float) -> None:
        """Wait out a retry delay, counting down on the status line.

        :param status: HTTP status that caused the wait, such as 429.
        :param seconds: Delay in seconds.
        """
        if status == 429:
            self.waits_429 += 1
        if not self._interactive:
            self._print(f"{self._text()} | {status}: waiting {format_elapsed(seconds)}")
        remaining = seconds
        while remaining > 0:
            self._waiting = f"{status}: waiting {format_elapsed(remaining)}"
            self._draw()
            step = min(1.0, remaining)
            self._sleep(step)
            remaining -= step
        self._waiting = ""
        self._draw()

    # Output -------------------------------------------------------------------

    def _elapsed(self) -> float:
        return 0.0 if self._t0 is None else self._monotonic() - self._t0

    def _text(self) -> str:
        parts = [f"[{format_elapsed(self._elapsed())}]", f"requests {self.requests}"]
        name = _PHASES.get(self._phase, self._phase)
        if self._total:
            parts.append(f"article {self._current} of {self._total} ({name})")
        elif self._phase == "listing" and self._current:
            parts.append(f"{name}, page {self._current}")
        elif name:
            parts.append(name)
        parts.append(f"429s {self.waits_429}")
        if self._waiting:
            parts.append(self._waiting)
        return " | ".join(parts)

    def _draw(self) -> None:
        if not self._interactive:
            return
        text = self._text()
        pad = max(self._width - len(text), 0)
        self._stream.write("\r" + text + " " * pad)
        self._stream.flush()
        self._width = len(text)

    def _print(self, text: str) -> None:
        if self._interactive and self._width:
            # Finish the status line before a plain line, then redraw it after.
            self._stream.write("\r" + " " * self._width + "\r")
            self._width = 0
        self._stream.write(text + "\n")
        self._stream.flush()
