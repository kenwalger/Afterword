"""Shadow mode on the sealed test set (ADR-010): sealed files, their hashes, and the reveal.

Each weekly shadow run classifies the new test comments with B1 and B2 and
seals the outputs in a git-ignored file under :data:`SEALED_ROOT`. The file's
SHA-256 goes to a committed ledger, :data:`LEDGER_PATH`, which the author
commits that week; the outputs themselves are never shown. A sealed record
holds the classifier's identity and versions, the class, flags, outcome, and
the registered policy's tier and rule: no comment text, explanation, or raw
model output.

Nothing reads a sealed file's contents for display until the reveal record,
:data:`REVEAL_PATH`, exists. The reveal is allowed only once the stopping rule
is met (:func:`stopping_rule`), and every scoring step first checks every
sealed file against the ledger.

This module is pure: file layout, canonical bytes, hashes, the ledger, and the
stopping rule. The store, the classifiers, and the labels are reached through
:mod:`afterword.service`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

SEALED_ROOT: Path = Path("reports/shadow")
LEDGER_PATH: Path = Path("registry/shadow-ledger.jsonl")
REVEAL_PATH: Path = Path("registry/reveal.json")
SEALED_SUFFIX: str = ".jsonl"
# The stopping rule (ADR-010; EVALUATION.md, "Stopping rule").
TARGET_CONSEQUENTIAL: int = 20
TARGET_TOTAL: int = 100
CAP: timedelta = timedelta(weeks=16)


def canonical_bytes(records: list[dict[str, Any]]) -> bytes:
    """Serialize sealed records the one way their hash is taken.

    Records are sorted by condition, then comment ID; each is compact JSON with
    sorted keys, one per line, with LF endings.

    :param records: Sealed records, each with ``condition`` and ``comment_id``.
    :returns: UTF-8 bytes.
    """
    ordered = sorted(records, key=lambda r: (str(r["condition"]), str(r["comment_id"])))
    lines = [
        json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) for r in ordered
    ]
    return "".join(f"{line}\n" for line in lines).encode("utf-8")


def sha256(data: bytes) -> str:
    """Return the hex SHA-256 of some bytes.

    :param data: Bytes.
    :returns: Lower-case hex digest.
    """
    return hashlib.sha256(data).hexdigest()


def sealed_file_name(sealed_at: datetime) -> str:
    """Name a sealed file by its sealing time.

    :param sealed_at: UTC sealing time.
    :returns: ``shadow-<YYYYMMDDTHHMMSSZ>.jsonl``.
    """
    return f"shadow-{sealed_at:%Y%m%dT%H%M%SZ}{SEALED_SUFFIX}"


def read_ledger(root: Path) -> list[dict[str, Any]]:
    """Read the committed ledger of sealed files.

    :param root: Repository root.
    :returns: Ledger entries, oldest first; empty before the first shadow run.
    """
    path = root / LEDGER_PATH
    if not path.exists():
        return []
    # LF only: splitlines would also split at U+2028 and U+2029 inside text.
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line]


def append_ledger(root: Path, entry: dict[str, Any]) -> None:
    """Append one sealed file's entry to the ledger.

    :param root: Repository root.
    :param entry: The entry (file name, SHA-256, counts, times).
    """
    path = root / LEDGER_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def read_sealed(path: Path) -> list[dict[str, Any]]:
    """Read one sealed file's records. Only for verification, sealing, and scoring after the reveal.

    :param path: A sealed file.
    :returns: Its records.
    """
    # LF only: splitlines would also split at U+2028 and U+2029 inside text.
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line]


@dataclass(frozen=True)
class Verification:
    """Sealed files checked against the ledger. File names only, no contents."""

    entries: int
    matched: int
    mismatched: tuple[str, ...]
    missing: tuple[str, ...]
    unlisted: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Report whether every sealed file matches its ledger entry and none is unlisted.

        :returns: ``True`` when verification passed.
        """
        return not (self.mismatched or self.missing or self.unlisted)


def verify(root: Path) -> Verification:
    """Check every sealed file against the SHA-256 the ledger recorded for it.

    :param root: Repository root.
    :returns: Which files match, differ, are missing, or are not in the ledger.
    """
    entries = read_ledger(root)
    sealed_dir = root / SEALED_ROOT
    on_disk = (
        {p.name for p in sealed_dir.glob(f"shadow-*{SEALED_SUFFIX}")}
        if sealed_dir.exists()
        else set()
    )
    listed = {str(e["file"]) for e in entries}
    mismatched: list[str] = []
    missing: list[str] = []
    for entry in entries:
        path = sealed_dir / str(entry["file"])
        if not path.exists():
            missing.append(path.name)
        elif sha256(path.read_bytes()) != entry["sha256"]:
            mismatched.append(path.name)
    return Verification(
        entries=len(entries),
        matched=len(entries) - len(mismatched) - len(missing),
        mismatched=tuple(mismatched),
        missing=tuple(missing),
        unlisted=tuple(sorted(on_disk - listed)),
    )


@dataclass(frozen=True)
class StopDecision:
    """Whether accrual may stop, from label counts and the calendar only."""

    met: bool
    reason: str
    test_labels: int
    consequential: int
    weeks_elapsed: float
    cap_reached_at: datetime


def stopping_rule(
    *, test_labels: int, consequential: int, registered_at: datetime, now: datetime
) -> StopDecision:
    """Apply the stopping rule: both targets met, or 16 weeks after preregistration.

    :param test_labels: Test comments with an analysis label.
    :param consequential: Of those, prospectively graded 2 or 3.
    :param registered_at: The preregistration time.
    :param now: The current time.
    :returns: Whether accrual stops, and why.
    """
    cap = registered_at + CAP
    weeks = (now - registered_at) / timedelta(weeks=1)
    if consequential >= TARGET_CONSEQUENTIAL and test_labels >= TARGET_TOTAL:
        reason = "targets_met"
    elif now >= cap:
        reason = "sixteen_week_cap"
    else:
        reason = "not_met"
    return StopDecision(
        met=reason != "not_met",
        reason=reason,
        test_labels=test_labels,
        consequential=consequential,
        weeks_elapsed=round(weeks, 2),
        cap_reached_at=cap,
    )


def read_reveal(root: Path) -> dict[str, Any] | None:
    """Read the reveal record, if the sealed outputs have been revealed.

    :param root: Repository root.
    :returns: The record, or ``None`` while the outputs are sealed.
    """
    path = root / REVEAL_PATH
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def write_reveal(root: Path, record: dict[str, Any]) -> Path:
    """Write the reveal record, once.

    :param root: Repository root.
    :param record: When, why the stopping rule was met, and the verification counts.
    :returns: The record's path.
    :raises FileExistsError: If the outputs were already revealed.
    """
    path = root / REVEAL_PATH
    if path.exists():
        raise FileExistsError(f"{REVEAL_PATH} exists: the outputs were already revealed")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path
