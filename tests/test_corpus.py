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


# Findings of the pre-seal deep audit (aud_R4f7isAJvl, session 16) ----------------------
# covers: R1, R2, R3, R4, R5, R6


def synthetic_records(text: str = "synthetic") -> list[dict]:
    base = {
        "source_object_id": "",
        "content_id": "p1",
        "corpus_set": "dev",
        "parent_comment_id": None,
        "context_as_of": "2026-08-03T14:00:00+00:00",
        "provenance": corpus.PROVENANCE,
        "normalization_version": "norm-v0.1",
    }
    return [
        base | {"comment_id": "a", "source_object_id": "a", "body_text": f"{text} one"},
        base | {"comment_id": "b", "source_object_id": "b", "body_text": f"{text} two"},
    ]


def frozen(tmp_path, records):
    made = corpus.manifest(
        records,
        version="v1",
        corpus_set="dev",
        created_at="x",
        store_as_of=None,
        registered_at=None,
    )
    path = tmp_path / "dev.jsonl"
    path.write_bytes(corpus.file_bytes(records))
    return made, path


def checked(made, path):
    return corpus.check(made["comments"], made["file_sha256"], path)


def test_verify_refuses_a_duplicated_record(tmp_path):
    records = synthetic_records()
    made, path = frozen(tmp_path, records)
    path.write_bytes(corpus.file_bytes(records) + corpus.file_bytes(records[:1]))
    result = checked(made, path)
    assert result.duplicates == 1 and not result.ok


def test_verify_refuses_a_file_whose_hash_differs_without_a_withdrawal(tmp_path):
    records = synthetic_records()
    made, path = frozen(tmp_path, records)
    path.write_bytes(b"".join(reversed(corpus.file_bytes(records).splitlines(keepends=True))))
    result = checked(made, path)
    assert result.matched == 2 and not result.file_matches and not result.ok


@pytest.mark.parametrize(
    "tamper",
    [
        {"body_text": "other synthetic text"},
        {"content_id": "p2"},
        {"corpus_set": "test"},
        {"withdrawn_on": None},
    ],
)
def test_a_record_marked_withdrawn_must_be_a_real_withdrawal(tmp_path, tamper):
    records = synthetic_records()
    made, path = frozen(tmp_path, records)
    corpus.withdraw(path, {"a"}, on=NOW.date())
    assert checked(made, path).ok
    edited = [r | tamper if r["comment_id"] == "a" else r for r in corpus.read_records(path)]
    path.write_bytes(corpus.file_bytes(edited))
    result = checked(made, path)
    assert (result.withdrawn, result.changed) == (0, 1) and not result.ok


def test_line_separators_in_text_stay_inside_their_record(tmp_path):
    records = synthetic_records(text=f"code a{chr(0x2028)}b{chr(0x2029)}c")
    made, path = frozen(tmp_path, records)
    assert [r["comment_id"] for r in corpus.read_records(path)] == ["a", "b"]
    assert checked(made, path).ok
    assert corpus.withdraw(path, {"b"}, on=NOW.date()) == ["b"]
    assert checked(made, path).ok


def test_a_withdrawal_that_fails_leaves_the_corpus_file_as_it_was(tmp_path, monkeypatch):
    _made, path = frozen(tmp_path, synthetic_records())
    before = path.read_bytes()

    def fail(*args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(corpus.os, "replace", fail)
    with pytest.raises(OSError, match="disk full"):
        corpus.withdraw(path, {"a"}, on=NOW.date())
    assert path.read_bytes() == before
    assert [p.name for p in tmp_path.iterdir()] == ["dev.jsonl"]


def test_an_export_that_fails_partway_leaves_nothing_and_can_be_rerun(runs, tmp_path, monkeypatch):
    real = corpus.write_once

    def fail_on_manifest(path, data):
        if path.suffix == ".json":
            raise OSError("disk full")
        real(path, data)

    monkeypatch.setattr(corpus, "write_once", fail_on_manifest)
    with pytest.raises(OSError, match="disk full"):
        export(tmp_path)
    assert not (tmp_path / corpus.data_path("v1", "dev")).exists()
    monkeypatch.undo()
    assert export(tmp_path).records == 4


def test_export_never_replaces_a_file_that_appears_after_its_check(runs, tmp_path, monkeypatch):
    data = tmp_path / corpus.data_path("v1", "dev")
    real = corpus.file_bytes

    def racing(records):
        data.parent.mkdir(parents=True, exist_ok=True)
        data.write_bytes(b"first export\n")
        return real(records)

    monkeypatch.setattr(corpus, "file_bytes", racing)
    with pytest.raises(service.ServiceError, match="frozen"):
        export(tmp_path)
    assert data.read_bytes() == b"first export\n"
    assert not (tmp_path / corpus.manifest_path("v1", "dev")).exists()


def test_the_manifest_is_written_with_lf_line_endings(runs, tmp_path):
    made = export(tmp_path)
    raw = (tmp_path / made.manifest_file).read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"}\n")


# Session 16b: the manifest's registered_at must equal the record's ---------------------
# covers: R11


def test_verify_refuses_a_manifest_whose_registered_at_differs_from_the_record(
    runs, tmp_path, capsys
):
    path = write_record(tmp_path)
    export(tmp_path)
    assert service.verify_corpus(tmp_path, version="v1").ok
    record = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(
        json.dumps(record | {"registered_at": "2026-08-11T00:00:00Z"}), encoding="utf-8"
    )
    result = service.verify_corpus(tmp_path, version="v1")
    assert result.matched == 2 and not result.registered_at_matches and not result.ok
    assert cli.main(["--root", str(tmp_path), "corpus", "verify", "--version", "v1"]) == 1
    assert "registered_at differs" in capsys.readouterr().out


def test_verify_refuses_a_corpus_exported_before_the_record(runs, tmp_path):
    export(tmp_path)
    assert service.verify_corpus(tmp_path, version="v1").ok
    write_record(tmp_path)
    result = service.verify_corpus(tmp_path, version="v1")
    assert not result.registered_at_matches and not result.ok
