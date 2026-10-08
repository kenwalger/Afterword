"""Saved-run redaction (ADR-009, amended 2026-10-08): withdrawn comments and retention."""

from __future__ import annotations

import json
import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from afterword import baseline, cli, service
from afterword.adapters.dev import records
from afterword.adapters.dev import redact as dev_redact
from tests.test_labeling import NAMES, make_run
from tests.test_store import T0, Runs

QUESTION = "Synthetic question about step two"


@pytest.fixture
def runs(tmp_path, fake_dev):
    return Runs(tmp_path, fake_dev)


def raw(root: Path, run_id: str) -> Path:
    return root / cli.RAW_ROOT / run_id


def run_text(root: Path, run_id: str) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(raw(root, run_id).glob("*")))


def nodes(root: Path, run_id: str, id_code: str) -> list[dict[str, Any]]:
    """Every saved copy of one comment node in a run (tree files and single fetches)."""
    found = []
    for path in raw(root, run_id).glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        stack = [record.get("response", {}).get("body")] if isinstance(record, dict) else []
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                if v.get("id_code") == id_code and "children" in v:
                    found.append(v)
                stack.extend(v.values())
            elif isinstance(v, list):
                stack.extend(v)
    return found


def log(root: Path) -> list[dict[str, Any]]:
    path = root / service.REDACTION_LOG
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def file_counts(root: Path) -> dict[str, int]:
    return {p.name: len(list(p.iterdir())) for p in (root / cli.RAW_ROOT).iterdir()}


def make_placeholder(runs: Runs, id_code: str) -> None:
    node = runs.node(id_code)
    for key in set(node) - {"type_of", "id_code", "created_at", "body_html", "user", "children"}:
        del node[key]
    node.update(body_html="<p>[deleted]</p>", user={})
    # The single-comment endpoint returns the same placeholder.
    single = runs.fake.single.get(id_code)
    if single is not None:
        for key in set(single) - {
            "type_of",
            "id_code",
            "created_at",
            "body_html",
            "user",
            "children",
        }:
            del single[key]
        single.update(body_html="<p>[deleted]</p>", user={})


# Withdrawn comments ------------------------------------------------------------------


def test_a_comment_deleted_by_absence_is_redacted_from_every_saved_run(runs, tmp_path):
    runs.node("s1b1")["body_html"] = "<p>Synthetic leaf, soon withdrawn.</p>"
    runs.ingest()
    runs.thread.pop(1)  # s1b1 disappears: absent twice is a deletion
    runs.ingest()
    assert "soon withdrawn" in run_text(tmp_path, "r1")  # one absence is not proof
    before = file_counts(tmp_path)

    result = runs.ingest()
    assert result.counts["deleted_absent"] == 1
    assert result.saved_runs.withdrawn_redactions == 1
    assert "soon withdrawn" not in run_text(tmp_path, "r1")
    copies = nodes(tmp_path, "r1", "s1b1")  # with and without the key
    assert copies
    for node in copies:
        assert node["body_html"] is None and node["user"] == {}
        assert node[records.REDACTION_KEY] == {"reason": "deleted_upstream", "on": "2026-09-01"}
    assert {r: n for r, n in file_counts(tmp_path).items() if r in before} == before  # none deleted
    assert log(tmp_path) == [
        {"date": "2026-09-01", "reason": "deleted_upstream", "run_id": "r1", "comment_id": "s1b1"}
    ]


def test_a_placeholder_redacts_earlier_runs_and_leaves_the_placeholder(runs, tmp_path):
    runs.ingest()
    make_placeholder(runs, "s1a1")
    result = runs.ingest()
    assert result.counts["deleted_placeholder"] == 1
    assert QUESTION not in run_text(tmp_path, "r1")
    assert nodes(tmp_path, "r1", "s1a1")
    for node in nodes(tmp_path, "r1", "s1a1"):  # the tree and the single fetch
        assert node["body_html"] is None and node["user"] == {}
    # DEV's own placeholder holds no commenter content and is not rewritten.
    assert all(records.REDACTION_KEY not in n for n in nodes(tmp_path, "r2", "s1a1"))
    assert {e["run_id"] for e in log(tmp_path)} == {"r1"}

    # The redacted run still loads: the comment is thread structure, its reply keeps
    # its parent, and nothing is reported as an unexpected shape.
    obs = records.load_run(raw(tmp_path, "r1"), include_text=True)
    by_id = {c.source_object_id: c for c in obs.comments}
    assert by_id["s1a1"].is_deletion_placeholder and by_id["s1a1"].body_source is None
    assert by_id["s1a2"].parent_source_object_id == "s1a1"
    assert not any(c.is_unexpected_shape for c in obs.comments)


def test_redaction_is_idempotent_and_logged_once(runs, tmp_path):
    runs.ingest()
    make_placeholder(runs, "s1a1")
    runs.ingest()
    entries = log(tmp_path)
    again = runs.ingest()
    assert again.saved_runs.withdrawn_redactions == 0
    assert log(tmp_path) == entries


def test_a_redacted_run_ingests_into_a_fresh_store_as_a_deletion(runs, tmp_path):
    runs.ingest()
    make_placeholder(runs, "s1a1")
    runs.ingest()
    (tmp_path / service.STORE_PATH).unlink()
    result = service.ingest_run(tmp_path, "r1", now=lambda: T0)
    assert result.counts.get("unexpected_shapes", 0) == 0
    assert result.counts["placeholder_first_seen"] == 1


# Retention ---------------------------------------------------------------------------


def test_runs_beyond_the_newest_n_are_reduced_to_structure(runs, tmp_path):
    runs.ingest()
    full = records.load_run(raw(tmp_path, "r1"))
    as_of = date(2026, 9, 2)
    before_counts = baseline.build(full, as_of=as_of)["totals"]
    before_files = file_counts(tmp_path)
    for _ in range(3):
        result = runs.ingest()
    assert result.saved_runs.runs_reduced == ("r1",)
    assert dev_redact.is_reduced(raw(tmp_path, "r1"))
    assert not any(dev_redact.is_reduced(raw(tmp_path, r)) for r in ("r2", "r3", "r4"))
    assert file_counts(tmp_path)["r1"] == before_files["r1"]  # no file deleted or left behind

    text = run_text(tmp_path, "r1")
    assert QUESTION not in text
    for name in NAMES:
        assert name not in text
    for key in ("body_markdown", "title", "url", "username", "profile_image"):
        assert f'"{key}":' not in text

    # IDs, timestamps, counts, and structure remain: the volume counts are unchanged.
    reduced = records.load_run(raw(tmp_path, "r1"), include_text=True)
    assert all(c.body_source is None for c in reduced.comments)
    assert baseline.build(reduced, as_of=as_of)["totals"] == before_counts
    assert [c.source_object_id for c in reduced.comments] == [
        c.source_object_id for c in full.comments
    ]
    assert not any(c.is_unexpected_shape for c in reduced.comments)
    assert {"date": "2026-09-01", "reason": "retention", "run_id": "r1"}.items() <= log(tmp_path)[
        -1
    ].items()


def test_retention_keeps_runs_that_labels_were_made_from(runs, tmp_path):
    labels = tmp_path / "fixtures" / "labels" / "unfrozen"
    labels.mkdir(parents=True)
    (labels / "initial.jsonl").write_text(json.dumps({"snapshot_run_id": "r1"}) + "\n")
    for _ in range(4):
        result = runs.ingest()
    assert result.saved_runs.runs_kept_for_labels == ("r1",)
    assert not dev_redact.is_reduced(raw(tmp_path, "r1"))
    assert QUESTION in run_text(tmp_path, "r1")


def test_retention_never_reduces_a_run_newer_than_the_last_ingest(tmp_path, fake_dev):
    for n in range(1, 5):
        make_run(tmp_path, run_id=f"r{n}", finished=T0 + timedelta(hours=n))
    result = service.ingest_run(tmp_path, "r1", keep_runs=1, now=lambda: T0)
    # r1 was just ingested and is older than the newest saved run, so it is reduced;
    # r2 and r3 are not ingested yet, so they stay whole.
    assert result.saved_runs.runs_reduced == ("r1",)
    assert not any(dev_redact.is_reduced(raw(tmp_path, r)) for r in ("r2", "r3", "r4"))
    (tmp_path / service.STORE_PATH).unlink()
    with pytest.raises(service.ServiceError, match="reduced by the retention rule"):
        service.ingest_run(tmp_path, "r1", now=lambda: T0)


def test_a_reduced_comment_deleted_later_is_redacted_as_deleted(runs, tmp_path):
    for _ in range(4):
        runs.ingest()
    assert dev_redact.is_reduced(raw(tmp_path, "r1"))
    make_placeholder(runs, "s1a1")
    runs.ingest()
    for node in nodes(tmp_path, "r1", "s1a1"):
        assert node["user"] == {}
        assert node[records.REDACTION_KEY]["reason"] == "deleted_upstream"


def test_keep_runs_must_be_at_least_one(tmp_path, fake_dev, capsys):
    make_run(tmp_path, run_id="r1", finished=T0)
    with pytest.raises(service.ServiceError):
        service.ingest_run(tmp_path, "r1", keep_runs=0)
    assert cli.main(["--root", str(tmp_path), "ingest", "--run", "r1", "--keep-runs", "0"]) == 2


def test_cli_ingest_reports_saved_run_changes_as_counts_and_run_ids(runs, tmp_path, capsys):
    for n in range(1, 3):
        make_run(tmp_path, run_id=f"r{n}", finished=T0 + timedelta(hours=n))
    root = ["--root", str(tmp_path)]
    assert cli.main([*root, "ingest", "--run", "r1", "--keep-runs", "1"]) == 0
    out = capsys.readouterr().out
    assert "saved runs: deleted comments redacted 0" in out
    assert "saved runs reduced to structure (retention): r1" in out
    for name in NAMES:
        assert name not in out


def test_the_redaction_log_is_git_ignored():
    gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
    assert service.REDACTION_LOG.parts[0] + "/" in gitignore.splitlines()


def test_redaction_touches_only_saved_runs(runs, tmp_path):
    runs.ingest()
    shutil.copytree(raw(tmp_path, "r1"), tmp_path / "elsewhere")
    make_placeholder(runs, "s1a1")
    runs.ingest()
    assert QUESTION in "\n".join(
        p.read_text(encoding="utf-8") for p in (tmp_path / "elsewhere").glob("*.json")
    )


# Read-only store commands -------------------------------------------------------------


@pytest.mark.parametrize(
    "argv",
    [
        ["connections"],
        ["store-status"],
        ["forget", "--connection", "x"],
        ["forget", "--connection", "x", "--yes"],
    ],
)
def test_store_commands_never_create_a_database(tmp_path, capsys, argv):
    assert cli.main(["--root", str(tmp_path), *argv]) == 0
    out = capsys.readouterr().out
    assert "No local database yet" in out
    assert not (tmp_path / service.STORE_PATH).exists()
    assert not (tmp_path / service.STORE_PATH).parent.exists()


def test_store_services_raise_no_store_without_creating_one(tmp_path):
    for call in (
        lambda: service.list_connections(tmp_path),
        lambda: service.store_status(tmp_path),
        lambda: service.forget_connection(tmp_path, "x", confirm=False),
    ):
        with pytest.raises(service.NoStoreError):
            call()
    assert not (tmp_path / "data").exists()
