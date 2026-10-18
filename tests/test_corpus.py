"""Corpus export, the committed manifest, verification, and ADR-009 withdrawal (synthetic only)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from afterword import cli, corpus, service
from tests.test_preregistration import write_record
from tests.test_redact import make_placeholder
from tests.test_store import Runs

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
QUESTION = "Synthetic question about step two"


@pytest.fixture
def runs(tmp_path, fake_dev):
    r = Runs(tmp_path, fake_dev)
    r.ingest()
    return r


def export(root, **kwargs):
    return service.export_corpus(root, version="v1", now=lambda: NOW, **kwargs)


def test_export_writes_records_and_a_manifest_with_ids_and_hashes_only(runs, tmp_path):
    made = export(tmp_path)
    assert made.records == 4 and made.store_as_of == "r1"
    records = corpus.read_records(tmp_path / made.data_file)
    assert [r["comment_id"] for r in records] == ["4821", "s1a1", "s1a3", "s1b1"]
    assert set(records[0]) == set(corpus.RECORD_FIELDS)
    by_id = {r["comment_id"]: r for r in records}
    assert by_id["s1a3"]["parent_comment_id"] == "s1a2"
    assert by_id["s1a1"]["parent_comment_id"] is None
    assert by_id["4821"]["content_id"] == "9000002" and by_id["s1a1"]["corpus_set"] == "dev"
    assert by_id["s1a1"]["context_as_of"] == "2026-08-03T14:00:00+00:00"
    assert all(r["provenance"] == "public-real" for r in records)
    manifest_text = (tmp_path / made.manifest_file).read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert manifest["file_sha256"] == made.file_sha256 and manifest["records"] == 4
    assert manifest["file"] == "fixtures/corpus/v1/dev.jsonl"
    assert {e["comment_id"] for e in manifest["comments"]} == set(by_id)
    for r in records:
        if r["body_text"]:
            assert r["body_text"] not in manifest_text
    assert "body_text" not in manifest_text


def test_a_version_is_written_once(runs, tmp_path):
    export(tmp_path)
    with pytest.raises(service.ServiceError, match="frozen"):
        export(tmp_path)


@pytest.mark.parametrize("version", ["1", "v0", "dev", "v1/../x", "V1"])
def test_bad_versions_are_refused(runs, tmp_path, version):
    with pytest.raises(service.ServiceError, match="corpus version"):
        service.export_corpus(tmp_path, version=version)


def test_after_preregistration_each_set_is_frozen_apart(runs, tmp_path):
    write_record(tmp_path)
    dev = export(tmp_path)
    test = export(tmp_path, corpus_set="test")
    assert (dev.records, test.records) == (2, 1)
    manifest = json.loads((tmp_path / test.manifest_file).read_text(encoding="utf-8"))
    assert manifest["registered_at"] == "2026-08-10T00:00:00+00:00"
    assert [e["comment_id"] for e in manifest["comments"]] == ["4821"]


def test_verify_finds_changed_missing_and_extra_records(runs, tmp_path):
    made = export(tmp_path)
    assert service.verify_corpus(tmp_path, version="v1").ok
    path = tmp_path / made.data_file
    records = corpus.read_records(path)
    records[0]["body_text"] = "edited"
    records.pop()
    records.append(records[0] | {"comment_id": "zzz"})
    path.write_bytes(corpus.file_bytes(records))
    result = service.verify_corpus(tmp_path, version="v1")
    assert (result.changed, result.missing, result.extra) == (1, 1, 1)
    assert not result.ok and not result.file_matches


def test_a_deleted_comment_is_withdrawn_from_the_corpus_at_the_next_ingest(runs, tmp_path):
    made = export(tmp_path)
    make_placeholder(runs, "s1b1")
    result = runs.ingest()
    assert result.corpus_withdrawn == 1
    records = {r["comment_id"]: r for r in corpus.read_records(tmp_path / made.data_file)}
    assert records["s1b1"]["body_text"] is None and records["s1b1"]["withdrawn"] is True
    check = service.verify_corpus(tmp_path, version="v1")
    assert (check.withdrawn, check.changed, check.missing) == (1, 0, 0) and check.ok
    log = (tmp_path / service.REDACTION_LOG).read_text(encoding="utf-8")
    assert '"reason": "deleted_upstream_corpus"' in log
    assert runs.ingest().corpus_withdrawn == 0  # already withdrawn


def test_the_commands_print_counts_and_paths_only(runs, tmp_path, capsys):
    assert cli.main(["--root", str(tmp_path), "corpus", "export", "--version", "v1"]) == 0
    out = capsys.readouterr().out
    assert "4 records" in out and "registry/corpus-v1-dev.json" in out
    assert QUESTION not in out
    assert cli.main(["--root", str(tmp_path), "corpus", "verify", "--version", "v1"]) == 0
    assert "verified" in capsys.readouterr().out
    code = cli.main(["--root", str(tmp_path), "corpus", "verify", "--version", "v2"])
    assert code == 2
