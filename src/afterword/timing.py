"""Chronological review timing records (C-009): where they live and which count.

A timing record counts as evidence only when the reviewer confirmed it as valid
at the end of the run. Confirmed records are written to ``reports/timing/``;
everything else goes to ``reports/timing/practice/`` and is never counted.
Readers here also ignore any top-level record without ``"valid": true``, such
as records written before the confirmation step existed.

Only aggregate fields leave this module. Per-comment IDs and times stay in the
records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TIMING_ROOT: Path = Path("reports/timing")
PRACTICE_DIR: str = "practice"
# Below this average a review is unlikely to have been a real read; the tool warns.
MIN_SECONDS_PER_COMMENT: float = 2.0

_SUMMARY_FIELDS: tuple[str, ...] = (
    "week_start",
    "week_end",
    "snapshot_run_id",
    "comments_in_week",
    "comments_reviewed",
    "complete",
    "total_seconds",
    "seconds_per_comment",
    "started_at",
)


def record_dir(root: Path, *, valid: bool) -> Path:
    """Return the directory a timing record is written to.

    :param root: Repository root.
    :param valid: Whether the reviewer confirmed the run as a valid timing.
    :returns: ``reports/timing/`` for valid runs, ``reports/timing/practice/`` otherwise.
    """
    base = root / TIMING_ROOT
    return base if valid else base / PRACTICE_DIR


def seconds_per_comment(total_seconds: float, reviewed: int) -> float | None:
    """Average review time per comment.

    :param total_seconds: Total time of the review.
    :param reviewed: Comments reviewed.
    :returns: Seconds per comment, or ``None`` when nothing was reviewed.
    """
    return round(total_seconds / reviewed, 1) if reviewed else None


def load_valid(root: Path) -> dict[str, Any]:
    """Summarize the timing records that count as evidence.

    :param root: Repository root.
    :returns: ``valid``: aggregate rows of confirmed records, oldest week first;
        ``ignored``: the number of practice and unconfirmed records skipped.
    """
    base = root / TIMING_ROOT
    rows: list[dict[str, Any]] = []
    ignored = 0
    if base.exists():
        practice = base / PRACTICE_DIR
        ignored += sum(1 for _ in practice.glob("*.json")) if practice.exists() else 0
        for path in sorted(base.glob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                ignored += 1
                continue
            if not isinstance(record, dict) or record.get("valid") is not True:
                ignored += 1
                continue
            rows.append({k: record.get(k) for k in _SUMMARY_FIELDS})
    rows.sort(key=lambda r: (str(r["week_start"]), str(r["started_at"])))
    return {"valid": rows, "ignored": ignored}
