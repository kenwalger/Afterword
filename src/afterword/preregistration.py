"""The preregistration record, and which corpus set a comment belongs to (ADR-010).

The record is a small committed JSON file, :data:`RECORD_PATH`, written when the
experiment is preregistered and sealed by the preregistration commit. It holds
the preregistration time, the registered conditions (B1's heuristic, B2's
provider, model, and digest, the policy), and the posts excluded from the test
set. Nothing in it is comment data.

Set membership follows ADR-010 (amended 2026-10-18). Before a record exists
every comment is ``dev``. Once it exists, with ``T`` its ``registered_at``:

- a comment on a post published after ``T`` is ``test``, unless the post is in
  the record's ``excluded_posts`` (posts about Afterword itself), when it
  belongs to neither set;
- a comment created at or before ``T`` on a post published at or before ``T``
  is ``dev``;
- a comment created after ``T`` on a post published at or before ``T`` belongs
  to neither set: it is counted, never labeled or scored.

The record is committed a few minutes after ``registered_at``; the runbook
(``docs/PREREGISTRATION.md``) requires that nothing be published in between.
An exclusion added after preregistration is an amendment: it is appended with
the time it was recorded, never edited in, and committed like the record.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

RECORD_PATH: Path = Path("registry/preregistration.json")
DEV: str = "dev"
TEST: str = "test"
CORPUS_SETS: tuple[str, ...] = (DEV, TEST)
_REQUIRED: tuple[str, ...] = (
    "registered_at",
    "b1_heuristic",
    "b2_provider",
    "b2_model",
    "b2_model_digest",
    "policy_version",
)


class PreregistrationError(ValueError):
    """The preregistration record is missing a field or holds an invalid value."""


@dataclass(frozen=True)
class ExcludedPost:
    """A post excluded from the test set, with when and why it was recorded."""

    post_id: str
    reason: str
    recorded_at: datetime
    # True when the exclusion was recorded after test comments on the post had
    # been labeled: a deviation from the runbook, kept visible.
    after_labeling: bool = False


@dataclass(frozen=True)
class Preregistration:
    """What was registered: the time accrual starts, the conditions, and the exclusions."""

    registered_at: datetime
    b1_heuristic: str
    b2_provider: str
    b2_model: str
    b2_model_digest: str
    policy_version: str
    num_ctx: int | None = None
    excluded_posts: tuple[ExcludedPost, ...] = field(default_factory=tuple)

    @property
    def excluded_ids(self) -> frozenset[str]:
        """Return the IDs of the excluded posts.

        :returns: Post source IDs.
        """
        return frozenset(p.post_id for p in self.excluded_posts)


def _utc(value: Any, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise PreregistrationError(f"{field_name} must be an RFC 3339 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise PreregistrationError(f"{field_name} is not an RFC 3339 time") from None
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise PreregistrationError(f"{field_name} must be UTC with an explicit offset")
    return parsed


def _excluded(value: Any) -> tuple[ExcludedPost, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise PreregistrationError("excluded_posts must be a list")
    out: list[ExcludedPost] = []
    seen: set[str] = set()
    for i, entry in enumerate(value):
        where = f"excluded_posts[{i}]"
        if not isinstance(entry, dict):
            raise PreregistrationError(f"{where} must be an object")
        post_id, reason = entry.get("post_id"), entry.get("reason")
        if not isinstance(post_id, str) or not post_id:
            raise PreregistrationError(f"{where}.post_id must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise PreregistrationError(f"{where}.reason must be a non-empty string")
        if post_id in seen:
            raise PreregistrationError(f"{where}: post {post_id} is listed twice")
        seen.add(post_id)
        after = entry.get("after_labeling", False)
        if not isinstance(after, bool):
            raise PreregistrationError(f"{where}.after_labeling must be true or false")
        out.append(
            ExcludedPost(
                post_id=post_id,
                reason=reason,
                recorded_at=_utc(entry.get("recorded_at"), f"{where}.recorded_at"),
                after_labeling=after,
            )
        )
    return tuple(out)


def parse(data: dict[str, Any]) -> Preregistration:
    """Validate a decoded preregistration record.

    :param data: The decoded JSON object.
    :returns: The record.
    :raises PreregistrationError: If a required field is missing or invalid.
    """
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise PreregistrationError(f"preregistration record lacks {', '.join(missing)}")
    for key in _REQUIRED[1:]:
        if not isinstance(data[key], str) or not data[key]:
            raise PreregistrationError(f"{key} must be a non-empty string")
    num_ctx = data.get("num_ctx")
    if num_ctx is not None and (not isinstance(num_ctx, int) or num_ctx < 1):
        raise PreregistrationError("num_ctx must be a positive integer")
    return Preregistration(
        registered_at=_utc(data["registered_at"], "registered_at"),
        b1_heuristic=data["b1_heuristic"],
        b2_provider=data["b2_provider"],
        b2_model=data["b2_model"],
        b2_model_digest=data["b2_model_digest"],
        policy_version=data["policy_version"],
        num_ctx=num_ctx,
        excluded_posts=_excluded(data.get("excluded_posts")),
    )


def _read(root: Path) -> dict[str, Any] | None:
    path = root / RECORD_PATH
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PreregistrationError(f"{RECORD_PATH} is not valid JSON: {exc.msg}") from None
    if not isinstance(data, dict):
        raise PreregistrationError(f"{RECORD_PATH} must hold a JSON object")
    return data


def load(root: Path) -> Preregistration | None:
    """Read the preregistration record, if there is one.

    :param root: Repository root.
    :returns: The record, or ``None`` before preregistration.
    :raises PreregistrationError: If the file exists but is not a valid record.
    """
    path = root / RECORD_PATH
    if not path.exists():
        return None
    data = _read(root)
    if data is None:
        raise PreregistrationError(f"{RECORD_PATH} disappeared while it was read")
    return parse(data)


def write_record(root: Path, data: dict[str, Any]) -> Preregistration:
    """Write the preregistration record, once: an existing record is never replaced.

    :param root: Repository root.
    :param data: The record's fields, with ``registered_at`` as a UTC ``datetime``.
    :returns: The record as written.
    :raises PreregistrationError: If a record already exists, ``registered_at`` is
        not a UTC time, or any field is invalid. Nothing is written then.
    :raises OSError: If writing fails partway; the partly written file is removed.
    """
    when = data.get("registered_at")
    offset = when.utcoffset() if isinstance(when, datetime) else None
    if not isinstance(when, datetime) or offset is None or offset.total_seconds() != 0:
        raise PreregistrationError("registered_at must be a UTC time")
    out = data | {"registered_at": when.isoformat().replace("+00:00", "Z")}
    record = parse(out)
    text = json.dumps(out, indent=2) + "\n"
    path = root / RECORD_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Mode "x" creates the file or fails, so a record is never overwritten.
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except FileExistsError:
        raise PreregistrationError(f"{RECORD_PATH} already exists; it is never rewritten") from None
    except OSError:
        # This call created the file, so a partly written record is its own to remove.
        path.unlink(missing_ok=True)
        raise
    return record


def add_exclusion(
    root: Path,
    *,
    post_id: str,
    reason: str,
    recorded_at: datetime,
    after_labeling: bool = False,
) -> ExcludedPost:
    """Append a post to the record's exclusions: an amendment, recorded with its time.

    Every other field, and every earlier exclusion, is left as it was.

    :param root: Repository root.
    :param post_id: The post's source ID.
    :param reason: Why it is excluded (for example, "post about Afterword").
    :param recorded_at: When the amendment is made (UTC).
    :param after_labeling: Whether test comments on the post were already labeled.
    :returns: The new exclusion.
    :raises PreregistrationError: Without a valid record, or if the post is already
        excluded or the reason is empty.
    """
    data = _read(root)
    if data is None:
        raise PreregistrationError(f"no preregistration record ({RECORD_PATH})")
    record = parse(data)
    if post_id in record.excluded_ids:
        raise PreregistrationError(f"post {post_id} is already excluded")
    if not reason.strip():
        raise PreregistrationError("an exclusion needs a reason")
    entry: dict[str, Any] = {
        "post_id": post_id,
        "reason": reason.strip(),
        "recorded_at": recorded_at.isoformat().replace("+00:00", "Z"),
    }
    if after_labeling:
        entry["after_labeling"] = True
    data["excluded_posts"] = [*data.get("excluded_posts", []), entry]
    parse(data)
    path = root / RECORD_PATH
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return _excluded([entry])[0]


def corpus_set_of(
    *,
    published_at: datetime | None,
    created_at: datetime | None,
    registered_at: datetime | None,
    post_id: str | None = None,
    excluded: frozenset[str] = frozenset(),
) -> str | None:
    """Return the corpus set a comment from others belongs to (ADR-010).

    :param published_at: When the comment's post was published, if known.
    :param created_at: When the comment was created, if known.
    :param registered_at: The preregistration time, or ``None`` before preregistration.
    :param post_id: The post's source ID, checked against ``excluded``.
    :param excluded: Posts excluded from the test set (the record's ``excluded_posts``).
    :returns: ``dev``, ``test``, or ``None`` for a comment in neither set (including
        one on an excluded test-period post, or whose times are unknown once a
        record exists).
    """
    if registered_at is None:
        return DEV
    if published_at is None or created_at is None:
        return None
    if published_at > registered_at:
        return None if post_id is not None and post_id in excluded else TEST
    return DEV if created_at <= registered_at else None
