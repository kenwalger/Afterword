"""The store and ingest: lifecycle rules, ADR-009 purge, ADR-013 identity rules (synthetic only)."""

from __future__ import annotations

import copy
import getpass
import json
import re
import socket
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, domain, service
from afterword.sqlite_store import SqliteRepository
from tests.conftest import FakeDev, load
from tests.test_labeling import NAMES, make_run

T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


class Runs:
    """Probe runs against the fake DEV API, one hour apart, ingested in order."""

    def __init__(self, root: Path, fake: FakeDev) -> None:
        self.root, self.fake, self.n = root, fake, 0

    def ingest(self) -> service.IngestResult:
        self.n += 1
        run_id = f"r{self.n}"
        make_run(self.root, run_id=run_id, finished=T0 + timedelta(hours=self.n))
        return service.ingest_run(self.root, run_id, now=lambda: T0 + timedelta(hours=self.n))

    @property
    def thread(self) -> list[dict[str, Any]]:
        return self.fake.comments[9000001]

    def node(self, id_code: str) -> dict[str, Any]:
        stack = list(self.thread)
        while stack:
            n = stack.pop()
            if n["id_code"] == id_code:
                return n
            stack.extend(n.get("children", []))
        raise KeyError(id_code)


@pytest.fixture
def runs(tmp_path, fake_dev):
    return Runs(tmp_path, fake_dev)


def store(root: Path) -> SqliteRepository:
    return SqliteRepository(root / service.STORE_PATH)


def comment(root: Path, comment_id: str) -> domain.Comment:
    repo = store(root)
    try:
        cid = repo.list_connections()[0].connection_id
        return repo.comments(cid)[comment_id]
    finally:
        repo.close()


def history(root: Path, comment_id: str) -> tuple[list[str], list[domain.SourceRecord]]:
    repo = store(root)
    try:
        cid = repo.list_connections()[0].connection_id
        events = [e.to_state for e in repo.lifecycle_events(cid, comment_id)]
        return events, repo.source_records(cid, comment_id)
    finally:
        repo.close()


# First ingest -----------------------------------------------------------------------


def test_first_ingest_creates_a_connection_and_stores_every_comment(runs, tmp_path):
    result = runs.ingest()
    assert result.created_connection
    assert result.counts == {"new": 5}
    assert result.limitations == ()

    question = comment(tmp_path, "s1a1")
    assert question.lifecycle_state == domain.ACTIVE
    assert question.body_text == "Synthetic question about step two?"
    assert question.normalization_version == "norm-v0.1"
    assert question.parent_comment_id is None
    assert question.parent_comment_id_state == domain.SOURCE_EMPTY
    assert question.is_content_author is False

    reply = comment(tmp_path, "s1a2")
    assert reply.is_content_author is True
    follow_up = comment(tmp_path, "s1a3")
    assert follow_up.parent_comment_id == "s1a2"
    assert follow_up.thread_root_comment_id == "s1a1"
    assert comment(tmp_path, "4821").source_object_id == "4821"  # digits stay a string


def test_payloads_are_reduced_before_storage(runs, tmp_path):
    runs.ingest()
    _, records = history(tmp_path, "s1a1")
    (rec,) = records
    payload = json.loads(rec.raw_payload or "")
    assert set(payload["user"]) == {"user_id", "username", "name"}
    assert "children" not in payload
    assert rec.source_updated_at_state == domain.NOT_EXPOSED
    raw = (tmp_path / service.STORE_PATH).read_bytes()
    for dropped in (b"profile_image", b"twitter_username", b"github_username", b"body_markdown"):
        assert dropped not in raw


def test_runs_are_ingested_once_and_oldest_first(runs, tmp_path):
    runs.ingest()
    with pytest.raises(service.ServiceError, match="already ingested"):
        service.ingest_run(tmp_path, "r1")
    make_run(tmp_path, run_id="older", finished=T0)
    with pytest.raises(service.ServiceError, match="oldest first"):
        service.ingest_run(tmp_path, "older")
    with pytest.raises(service.ServiceError, match="no probe run"):
        service.ingest_run(tmp_path, "missing")


# Lifecycle --------------------------------------------------------------------------


def test_an_unchanged_run_only_moves_last_observed(runs, tmp_path):
    runs.ingest()
    result = runs.ingest()
    assert result.counts == {"unchanged": 5}
    c = comment(tmp_path, "s1b1")
    assert c.last_observed_at > c.first_observed_at
    assert len(history(tmp_path, "s1b1")[1]) == 1


def test_an_edit_is_detected_by_normalized_text(runs, tmp_path):
    runs.ingest()
    runs.node("s1b1")["body_html"] = "<p>Synthetic acknowledgment, edited.</p>\n"
    result = runs.ingest()
    assert result.counts["edited"] == 1
    c = comment(tmp_path, "s1b1")
    assert c.lifecycle_state == domain.EDITED
    assert c.body_text == "Synthetic acknowledgment, edited."
    events, records = history(tmp_path, "s1b1")
    assert events == [domain.ACTIVE, domain.EDITED]
    assert len(records) == 2


def test_a_rendering_change_is_not_an_edit(runs, tmp_path):
    runs.ingest()
    runs.node("s1b1")["body_html"] = "<div><p>Synthetic   acknowledgment.</p></div>"
    result = runs.ingest()
    assert result.counts["payload_changed"] == 1
    c = comment(tmp_path, "s1b1")
    assert c.lifecycle_state == domain.ACTIVE
    events, records = history(tmp_path, "s1b1")
    assert events == [domain.ACTIVE]
    assert len(records) == 2  # stored for provenance


def test_absence_twice_deletes_and_purges(runs, tmp_path):
    # Unique text: comment 4821 is a fixture copy of s1b1 and stays live.
    runs.node("s1b1")["body_html"] = "<p>Synthetic leaf, soon withdrawn.</p>"
    runs.ingest()
    removed = runs.thread.pop(1)  # s1b1, a leaf: deleted leaves disappear
    assert removed["id_code"] == "s1b1"

    first = runs.ingest()
    assert first.counts["missing"] == 1
    assert comment(tmp_path, "s1b1").lifecycle_state == domain.MISSING_FROM_SOURCE
    assert comment(tmp_path, "s1b1").body_text is not None  # one absence is not proof
    assert any("source reports 4 comments, 3 live" in x for x in first.limitations)

    second = runs.ingest()
    assert second.counts["deleted_absent"] == 1
    c = comment(tmp_path, "s1b1")
    assert c.lifecycle_state == domain.PURGED
    assert c.deletion_evidence == domain.ABSENT_TWICE
    assert (c.body_source, c.body_text, c.body_text_hash) == (None, None, None)
    events, records = history(tmp_path, "s1b1")
    assert events == [
        domain.ACTIVE,
        domain.MISSING_FROM_SOURCE,
        domain.DELETED_UPSTREAM,
        domain.PURGED,
    ]
    assert all(r.raw_payload is None and r.purged_at is not None for r in records)
    assert b"soon withdrawn" not in (tmp_path / service.STORE_PATH).read_bytes()


def test_a_comment_back_after_one_absence_is_active_again(runs, tmp_path):
    runs.ingest()
    saved = runs.thread.pop(1)
    runs.ingest()
    runs.thread.append(saved)
    result = runs.ingest()
    assert result.counts["reappeared"] == 1
    c = comment(tmp_path, "s1b1")
    assert (c.lifecycle_state, c.consecutive_absences) == (domain.ACTIVE, 0)


def test_a_placeholder_deletes_at_once_keeping_structure_and_authorship(runs, tmp_path):
    runs.ingest()
    with_text = {"type_of", "id_code", "created_at", "body_html", "user", "children"}
    node = runs.node("s1a1")
    for key in set(node) - with_text:
        del node[key]
    node.update(body_html="<p>[deleted]</p>", user={})

    result = runs.ingest()
    assert result.counts["deleted_placeholder"] == 1
    c = comment(tmp_path, "s1a1")
    assert c.lifecycle_state == domain.PURGED
    assert c.deletion_evidence == domain.SOURCE_PLACEHOLDER
    assert c.body_text is None
    # Non-content facts survive from the last observation (ADR-009).
    assert (c.author_platform_identity_id, c.is_content_author) == ("2001", False)
    assert comment(tmp_path, "s1a2").parent_comment_id == "s1a1"

    _, records = history(tmp_path, "s1a1")
    original, placeholder = records
    assert original.raw_payload is None
    assert json.loads(placeholder.raw_payload or "")["user"] == {}
    assert b"Synthetic question about step two" not in (tmp_path / service.STORE_PATH).read_bytes()


def test_a_placeholder_first_seen_has_unknown_authorship(runs, tmp_path):
    runs.fake.comments[9000003] = load("comments-with-deletion-placeholder.json")
    result = runs.ingest()
    assert result.counts["placeholder_first_seen"] == 1
    c = comment(tmp_path, "s9p1")
    assert c.lifecycle_state == domain.DELETED_UPSTREAM
    assert c.deletion_evidence == domain.SOURCE_PLACEHOLDER
    assert (c.author_state, c.is_content_author, c.is_content_author_state) == (
        domain.UNKNOWN,
        None,
        domain.UNKNOWN,
    )
    assert c.body_source is None
    assert comment(tmp_path, "s9p2").parent_comment_id == "s9p1"


def test_an_unexpected_shape_is_not_stored_and_is_reported(runs, tmp_path):
    odd = copy.deepcopy(runs.node("s1b1"))
    odd.update(id_code="s1zz", user=None)
    runs.thread.append(odd)
    result = runs.ingest()
    assert result.counts["unexpected_shapes"] == 1
    assert any("unexpected node shape: comment s1zz" in x for x in result.limitations)
    repo = store(tmp_path)
    try:
        cid = repo.list_connections()[0].connection_id
        assert "s1zz" not in repo.comments(cid)
        assert repo.source_records(cid, "s1zz") == []
    finally:
        repo.close()


def test_a_purge_removes_model_text_derived_from_the_comment(runs, tmp_path):
    runs.ingest()
    repo = store(tmp_path)
    cid = repo.list_connections()[0].connection_id
    key = domain.CacheKey("h", "ollama", "m", "d", "pr-v0.1", "tax-v0.1")
    repo.add_classification(
        domain.Classification(
            classification_id="k1",
            connection_id=cid,
            comment_id="s1b1",
            comment_source_record_id=None,
            key=key,
            primary_class="LIGHTWEIGHT_ACKNOWLEDGMENT",
            flags=(),
            flags_by_source={},
            confidence="HIGH",
            confidence_state=domain.PRESENT,
            explanation="Synthetic explanation quoting the comment.",
            classifier_kind=domain.MODEL,
            model_digest_state=domain.PRESENT,
            normalization_version="norm-v0.1",
            precheck_version="pc-v0.1",
            input_fields_sent=("comment",),
            raw_output='{"explanation": "Synthetic explanation quoting the comment."}',
            latency_ms=1,
            classified_at=T0,
            outcome=domain.OK,
        )
    )
    repo.close()
    runs.thread.pop(1)
    runs.ingest()
    runs.ingest()
    repo = store(tmp_path)
    (k,) = repo.classifications(cid, "s1b1")
    repo.close()
    assert (k.raw_output, k.explanation) == (None, None)
    assert k.primary_class == "LIGHTWEIGHT_ACKNOWLEDGMENT"  # a non-content judgment remains


# ADR-013 and forget -------------------------------------------------------------------


def all_text(db_path: Path) -> list[str]:
    db = sqlite3.connect(db_path)
    out = []
    for (table,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'"):
        for row in db.execute(f"SELECT * FROM {table}"):
            out += [v for v in row if isinstance(v, str)]
    db.close()
    return out


def test_records_follow_the_one_way_door_rules(runs, tmp_path):
    runs.ingest()
    runs.thread.pop(1)
    runs.ingest()
    db_path = tmp_path / service.STORE_PATH
    values = all_text(db_path)
    forbidden = [str(tmp_path), tmp_path.name, socket.gethostname(), getpass.getuser()]
    for value in values:
        for term in forbidden:
            assert term not in value
    db = sqlite3.connect(db_path)
    for table, column in [
        ("connections", "created_at"),
        ("comments", "first_observed_at"),
        ("source_records", "observed_at"),
        ("lifecycle_events", "occurred_at"),
        ("sync_runs", "ingested_at"),
    ]:
        for (value,) in db.execute(f"SELECT {column} FROM {table}"):
            assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?\+00:00", value)
    for table in ("connections", "source_records", "lifecycle_events"):
        types = {r[0] for r in db.execute(f"SELECT DISTINCT typeof({table}.rowid) FROM {table}")}
        ids = db.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        assert isinstance(ids[0], str) and types == {"integer"}
    (uuid_like,) = db.execute("SELECT connection_id FROM connections").fetchone()
    assert re.fullmatch(r"[0-9a-f-]{36}", uuid_like)
    db.close()


def test_forget_counts_first_then_deletes_only_that_connection(runs, tmp_path):
    first = runs.ingest()
    runs.fake.me = {**runs.fake.me, "id": 1002}
    second = runs.ingest()
    assert second.created_connection and second.connection_id != first.connection_id

    counts = service.forget_connection(tmp_path, first.connection_id, confirm=False)
    assert counts["comments"] == 5 and counts["connections"] == 1
    assert service.forget_connection(tmp_path, first.connection_id, confirm=True) == counts
    remaining = service.list_connections(tmp_path)
    assert [s.connection.connection_id for s in remaining] == [second.connection_id]
    assert remaining[0].counts["comments"] == 5
    with pytest.raises(service.ServiceError):
        service.forget_connection(tmp_path, first.connection_id, confirm=True)


# CLI -----------------------------------------------------------------------------------


def test_cli_ingest_and_forget_print_counts_and_ids_only(runs, tmp_path, capsys):
    make_run(tmp_path, run_id="r1", finished=T0)
    assert cli.main(["--root", str(tmp_path), "ingest", "--run", "r1"]) == 0
    out = capsys.readouterr().out
    assert "comments: new 5" in out
    connection_id = re.search(r"connection (\S+)", out).group(1)
    assert cli.main(["--root", str(tmp_path), "connections"]) == 0
    assert connection_id in capsys.readouterr().out

    forget = ["--root", str(tmp_path), "forget", "--connection", connection_id]
    assert cli.main(forget) == 1
    assert "nothing deleted" in capsys.readouterr().out
    assert cli.main([*forget, "--yes"]) == 0
    out = capsys.readouterr().out
    assert "deleted:" in out
    for name in NAMES:
        assert name not in out
    assert cli.main(["--root", str(tmp_path), "ingest", "--run", "nope"]) == 2


def test_the_store_is_git_ignored():
    ignored = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert "data/" in ignored.splitlines()
