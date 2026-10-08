"""Redact saved DEV probe runs in place (ADR-009, amended 2026-10-08).

Two operations, both on the raw files under ``fixtures/dev-api/source/real/``,
and neither ever deletes a run or a file:

- :func:`redact_withdrawn` removes the text and the author of comments that
  were deleted upstream, from every saved run that holds them.
- :func:`reduce_run` cuts one run down to IDs, timestamps, counts, and thread
  structure (the retention rule).

Each redacted comment node carries :data:`REDACTION_KEY`, so a later reader
knows what happened to it; :func:`afterword.adapters.dev.records.redaction_reason`
reads that marker. Only the adapter knows the DEV field names involved.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from afterword.adapters.dev import records
from afterword.adapters.dev.records import (
    REASON_DELETED,
    REASON_RETENTION,
    REDACTION_KEY,
    redaction_reason,
)

# Added to a run's run.json once the run is reduced by the retention rule.
RUN_RETENTION_KEY: str = "afterword_retention"

# What a reduced comment keeps: its ID, time, and place in the thread, plus the
# author's numeric ID, so authorship stays countable (the baseline separates the
# author's own comments). Text, names, handles, and profile links go.
_COMMENT_STRUCTURE: tuple[str, ...] = ("type_of", "id_code", "created_at", "children")
# What a reduced post keeps: IDs, timestamps, and the reported comment count.
_ARTICLE_STRUCTURE: tuple[str, ...] = (
    "type_of",
    "id",
    "published",
    "published_at",
    "published_timestamp",
    "created_at",
    "edited_at",
    "comments_count",
)
_USER_STRUCTURE: tuple[str, ...] = ("user_id",)
_ACCOUNT_STRUCTURE: tuple[str, ...] = ("type_of", "id")


@dataclass(frozen=True)
class Redaction:
    """One comment redacted in one saved run. IDs only."""

    run_id: str
    source_object_id: str


def _is_comment(value: Any) -> bool:
    return isinstance(value, dict) and "id_code" in value and "children" in value


def _comment_nodes(value: Any) -> Iterator[dict[str, Any]]:
    stack = [value]
    while stack:
        v = stack.pop()
        if _is_comment(v):
            yield v
            stack.extend(v.get("children") or [])
        elif isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)


def run_dirs(raw_root: Path) -> list[Path]:
    """List saved run directories, oldest first (run IDs are UTC start times).

    :param raw_root: Directory holding one subdirectory per saved run.
    :returns: Run directories that hold a run file.
    """
    if not raw_root.exists():
        return []
    return sorted(p for p in raw_root.iterdir() if p.is_dir() and (p / records.RUN_FILE).exists())


def _payload_files(run_dir: Path) -> list[Path]:
    return sorted(p for p in run_dir.glob("*.json") if p.name != records.RUN_FILE)


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: Any) -> None:
    # Same format as the probe; written beside the file, then swapped in, so an
    # interrupted write never leaves a half-written payload.
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _body(record: Any) -> Any:
    if isinstance(record, dict) and isinstance(record.get("response"), dict):
        return record["response"].get("body")
    return None


def redact_withdrawn(
    raw_root: Path, source_object_ids: Iterable[str], *, on: date
) -> list[Redaction]:
    """Remove the text and author of deleted comments from every saved run.

    A matching comment node keeps its ID, time, and children (replies keep their
    parent); its body becomes ``None``, its ``user`` an empty object, and it gets
    a :data:`REDACTION_KEY` marker. Nodes already redacted for deletion, and
    DEV's own deletion placeholders (which hold no commenter content), are left
    as they are. Runs and files are never deleted.

    :param raw_root: Directory holding one subdirectory per saved run.
    :param source_object_ids: Source IDs of comments deleted upstream.
    :param on: Date recorded in each marker.
    :returns: One entry per comment newly redacted in each run.
    """
    targets = {str(i) for i in source_object_ids}
    done: list[Redaction] = []
    if not targets:
        return done
    marker = {"reason": REASON_DELETED, "on": on.isoformat()}
    for run_dir in run_dirs(raw_root):
        redacted: set[str] = set()
        for path in _payload_files(run_dir):
            record = _read(path)
            changed = False
            for node in _comment_nodes(_body(record)):
                if str(node.get("id_code")) not in targets:
                    continue
                if redaction_reason(node) == REASON_DELETED:
                    continue
                if records.is_deletion_placeholder(node):
                    continue
                node["body_html"] = None
                node["user"] = {}
                node[REDACTION_KEY] = dict(marker)
                redacted.add(str(node["id_code"]))
                changed = True
            if changed:
                _write(path, record)
        done += [Redaction(run_dir.name, i) for i in sorted(redacted)]
    return done


def is_reduced(run_dir: Path) -> bool:
    """Report whether a run was already reduced by the retention rule.

    :param run_dir: Saved run directory.
    :returns: ``True`` once :func:`reduce_run` has marked the run.
    """
    return RUN_RETENTION_KEY in _read(run_dir / records.RUN_FILE)


def _reduce_user(user: Any) -> Any:
    if not isinstance(user, dict):
        return user
    return {k: user[k] for k in _USER_STRUCTURE if k in user}


def _reduce(value: Any, marker: dict[str, str], counted: list[int]) -> Any:
    if _is_comment(value):
        if redaction_reason(value) == REASON_DELETED or records.is_deletion_placeholder(value):
            kept = dict(value)
        else:
            kept = {k: value[k] for k in _COMMENT_STRUCTURE if k in value}
            kept["body_html"] = None
            kept["user"] = _reduce_user(value.get("user"))
            kept[REDACTION_KEY] = dict(marker)
            counted[0] += 1
        kept["children"] = [_reduce(c, marker, counted) for c in value.get("children") or []]
        return kept
    if isinstance(value, dict) and value.get("type_of") == "article":
        kept = {k: value[k] for k in _ARTICLE_STRUCTURE if k in value}
        if "user" in value:
            kept["user"] = _reduce_user(value["user"])
        return kept
    if isinstance(value, dict) and value.get("type_of") == "user":
        return {k: value[k] for k in _ACCOUNT_STRUCTURE if k in value}
    if isinstance(value, list):
        return [_reduce(v, marker, counted) for v in value]
    return value


def reduce_run(run_dir: Path, *, on: date) -> int:
    """Reduce a saved run to IDs, timestamps, counts, and thread structure.

    Comments lose their text and every author field except the numeric user ID;
    posts lose their titles, bodies, links, and tags. What remains still loads
    (no text) and still gives the same volume counts. The run directory and its
    files stay; ``run.json`` is marked. A run already reduced is left as it is.

    :param run_dir: Saved run directory.
    :param on: Date recorded in the markers.
    :returns: Comment nodes reduced (``0`` for a run already reduced).
    """
    if is_reduced(run_dir):
        return 0
    marker = {"reason": REASON_RETENTION, "on": on.isoformat()}
    counted = [0]
    for path in _payload_files(run_dir):
        record = _read(path)
        body = _body(record)
        if body is None:
            continue
        record["response"]["body"] = _reduce(body, marker, counted)
        _write(path, record)
    run = _read(run_dir / records.RUN_FILE)
    run[RUN_RETENTION_KEY] = {"reduced_on": on.isoformat()}
    _write(run_dir / records.RUN_FILE, run)
    return counted[0]
