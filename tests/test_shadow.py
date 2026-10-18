"""Shadow mode: sealing, the ledger, verification, the reveal, and scoring (synthetic only)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, label_records, service, shadow, taxonomy
from tests.fake_models import FakeOllama, answer
from tests.test_preregistration import write_record
from tests.test_store import Runs

# Registered 2026-08-10: only 4821 (post 9000002, published 2026-08-17) is a test comment.
REGISTERED = datetime(2026, 8, 10, tzinfo=UTC)
WEEK_LATER = REGISTERED + timedelta(days=9)
AFTER_CAP = REGISTERED + timedelta(weeks=16, days=1)
EXPLANATION = "Synthetic explanation that must never be sealed"


@pytest.fixture
def store(tmp_path, fake_dev):
    Runs(tmp_path, fake_dev).ingest()
    write_record(tmp_path)
    return tmp_path


@pytest.fixture
def ollama(no_live_api):
    return FakeOllama(no_live_api, reply=lambda body: answer(explanation=EXPLANATION))


def seal(root: Path, when: datetime = WEEK_LATER, **kwargs: Any) -> service.ShadowRun:
    return service.shadow_run(root, now=lambda: when, **kwargs)


def write_test_labels(root: Path, records: list[dict[str, Any]]) -> None:
    out = label_records.label_dir(root, "unfrozen")
    out.mkdir(parents=True, exist_ok=True)
    (out / "initial.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
    )


def make_test_label(comment_id: str, grade: int, at: datetime) -> dict[str, Any]:
    return {
        "comment_id": comment_id,
        "pass": "initial",
        "corpus_set": "test",
        "labeled_at": at.isoformat().replace("+00:00", "Z"),
        "primary_class": "TECHNICAL_QUESTION",
        "flags": [],
        "consequential_prospective": grade,
        "taxonomy_version": "tax-v0.2",
        "batch_id": "b1",
    }


# Pure parts ------------------------------------------------------------------------


def test_canonical_bytes_do_not_depend_on_order_or_key_order():
    a = [
        {"condition": "b2", "comment_id": "x", "tier": "QUEUE"},
        {"comment_id": "x", "condition": "b1"},
    ]
    b = list(reversed(a))
    assert shadow.canonical_bytes(a) == shadow.canonical_bytes(b)
    assert (
        shadow.canonical_bytes(a)
        .decode()
        .splitlines()[0]
        .startswith('{"comment_id":"x","condition":"b1"')
    )


@pytest.mark.parametrize(
    ("labels", "consequential", "now", "reason"),
    [
        (100, 20, WEEK_LATER, "targets_met"),
        (99, 40, WEEK_LATER, "not_met"),
        (300, 19, WEEK_LATER, "not_met"),
        (10, 2, AFTER_CAP, "sixteen_week_cap"),
    ],
)
def test_the_stopping_rule(labels, consequential, now, reason):
    decision = shadow.stopping_rule(
        test_labels=labels, consequential=consequential, registered_at=REGISTERED, now=now
    )
    assert decision.reason == reason and decision.met == (reason != "not_met")


# Sealing ---------------------------------------------------------------------------


def test_shadow_mode_needs_the_preregistration_record(tmp_path, fake_dev, ollama):
    Runs(tmp_path, fake_dev).ingest()
    with pytest.raises(service.ServiceError, match="preregistration record"):
        seal(tmp_path)


def test_a_run_seals_only_new_test_comments_and_records_the_hash(store, ollama):
    result = seal(store)
    assert (result.test_comments, result.comments_sealed, result.records) == (1, 1, 2)
    assert len(ollama.chats) == 1  # B2 classified the one test comment, nothing else
    assert (
        result.sealed_file is not None and result.sealed_file.parent == store / shadow.SEALED_ROOT
    )
    data = result.sealed_file.read_bytes()
    assert shadow.sha256(data) == result.sha256
    [entry] = shadow.read_ledger(store)
    assert entry["sha256"] == result.sha256 and entry["file"] == result.sealed_file.name
    assert entry["week_start"] == "2026-08-17" and entry["comments"] == 1
    records = shadow.read_sealed(result.sealed_file)
    assert {r["condition"] for r in records} == {"b1", "b2"}
    assert {r["comment_id"] for r in records} == {"4821"}
    assert all(r["policy_version"] == "pp-v0.2" for r in records)
    text = data.decode("utf-8")
    assert EXPLANATION not in text and "explanation" not in text and "raw_output" not in text
    again = seal(store, WEEK_LATER + timedelta(days=7))
    assert again.sealed_file is None and again.already_sealed == 1
    assert len(shadow.read_ledger(store)) == 1


def test_ordinary_classification_never_touches_test_comments(store, ollama):
    b1 = service.classify_comments(store, condition="b1")
    assert b1.subjects == 2  # s1a1 and s1b1; 4821 is test, s1a3 is in neither set
    with pytest.raises(service.ServiceError, match="unknown corpus set"):
        service.classify_comments(store, condition="b1", corpus_set="train")


def test_the_run_command_prints_no_output_of_any_classifier(store, ollama, capsys, monkeypatch):
    monkeypatch.setattr(service, "datetime", _FixedDatetime)
    code = cli.main(["--root", str(store), "shadow", "run"])
    out = capsys.readouterr().out
    assert code == 0 and "sealed 1 comments" in out and "sha256: " in out
    for word in (*taxonomy.CLASSES, "SURFACE", "QUEUE", "COLLAPSED", EXPLANATION):
        assert word not in out


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz: Any = None) -> datetime:
        return WEEK_LATER


def test_failed_b2_outputs_are_held_back_and_retried(store, ollama):
    ollama.fail_with = 500
    first = seal(store)
    assert first.sealed_file is None and first.held_back_failed == 1
    assert shadow.read_ledger(store) == []
    ollama.fail_with = None
    second = seal(store, WEEK_LATER + timedelta(days=7))
    assert second.comments_sealed == 1 and second.held_back_failed == 0


def test_failed_outputs_can_be_sealed_on_request(store, ollama):
    ollama.fail_with = 500
    result = seal(store, seal_failed=True)
    assert result.comments_sealed == 1
    [b2] = [r for r in shadow.read_sealed(result.sealed_file) if r["condition"] == "b2"]
    assert b2["outcome"] == "FAILED" and b2["tier"] == "SURFACE"


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"b2_model_digest": "0" * 64}, "differs from the application's pin"),
        ({"num_ctx": 2048}, "context size"),
        ({"policy_version": "pp-v9"}, "registered policy"),
        ({"b1_heuristic": "hb-v9"}, "registered heuristic"),
    ],
)
def test_a_record_that_does_not_match_the_application_is_refused(store, ollama, overrides, message):
    write_record(store, **overrides)
    with pytest.raises(service.ServiceError, match=message):
        seal(store)
    assert ollama.chats == []


# Verification ----------------------------------------------------------------------


def test_verify_detects_a_changed_a_missing_and_an_unlisted_file(store, ollama):
    result = seal(store)
    assert service.shadow_verify(store).ok
    result.sealed_file.write_bytes(result.sealed_file.read_bytes() + b"\n")
    check = service.shadow_verify(store)
    assert not check.ok and check.mismatched == (result.sealed_file.name,)
    with pytest.raises(service.ServiceError, match="do not match the committed ledger"):
        seal(store, WEEK_LATER + timedelta(days=7))
    result.sealed_file.unlink()
    assert service.shadow_verify(store).missing == (result.sealed_file.name,)
    (store / shadow.SEALED_ROOT / "shadow-20260901T000000Z.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    assert service.shadow_verify(store).unlisted == ("shadow-20260901T000000Z.jsonl",)


def test_the_verify_command_exits_1_when_a_file_differs(store, ollama, capsys):
    result = seal(store)
    assert cli.main(["--root", str(store), "shadow", "verify"]) == 0
    result.sealed_file.write_text("tampered\n", encoding="utf-8")
    assert cli.main(["--root", str(store), "shadow", "verify"]) == 1
    assert "hash differs" in capsys.readouterr().out


# Reveal and score ------------------------------------------------------------------


def test_nothing_is_revealed_or_scored_before_the_stopping_rule(store, ollama):
    seal(store)
    write_test_labels(store, [make_test_label("4821", 2, WEEK_LATER)])
    with pytest.raises(service.ServiceError, match="not revealed"):
        service.shadow_score(store)
    with pytest.raises(service.ServiceError, match="stopping rule is not met"):
        service.shadow_reveal(store, now=lambda: WEEK_LATER + timedelta(days=1))
    assert shadow.read_reveal(store) is None


def test_reveal_at_the_cap_then_score_once_with_blind_labels_only(store, ollama):
    seal(store)
    write_test_labels(
        store,
        [
            make_test_label("4821", 2, WEEK_LATER),
            # A dev comment mislabeled as test is not a test comment: never counted.
            make_test_label("s1a1", 3, WEEK_LATER),
        ],
    )
    reveal = service.shadow_reveal(store, now=lambda: AFTER_CAP)
    assert reveal["reason"] == "sixteen_week_cap" and reveal["sealed_comments"] == 1
    assert (store / shadow.REVEAL_PATH).exists()
    with pytest.raises(service.ServiceError, match="already revealed"):
        service.shadow_reveal(store, now=lambda: AFTER_CAP)
    with pytest.raises(service.ServiceError, match="accrual has stopped"):
        seal(store, AFTER_CAP)
    result = service.shadow_score(store)
    assert result["labels_before_reveal"] == 1 and result["labels_after_reveal_excluded"] == 0
    for condition in ("b1", "b2"):
        counts = result["conditions"][condition]["scores"]["all"]
        assert counts["total"] == 1 and counts["consequential"] == 1
    assert result["oracle"]["class_and_flags"]["consequential"] == 1


def test_a_label_made_after_the_reveal_is_excluded_from_the_score(store, ollama):
    seal(store)
    write_test_labels(store, [make_test_label("4821", 2, AFTER_CAP + timedelta(days=1))])
    service.shadow_reveal(store, now=lambda: AFTER_CAP)
    result = service.shadow_score(store)
    assert result["labels_before_reveal"] == 0 and result["labels_after_reveal_excluded"] == 1
    assert result["conditions"]["b2"]["scores"]["all"]["total"] == 0


def test_scoring_refuses_tampered_outputs_even_after_the_reveal(store, ollama):
    sealed = seal(store)
    write_test_labels(store, [make_test_label("4821", 2, WEEK_LATER)])
    service.shadow_reveal(store, now=lambda: AFTER_CAP)
    sealed.sealed_file.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(service.ServiceError, match="do not match the committed ledger"):
        service.shadow_score(store)


def test_status_reports_targets_as_met_or_not_never_the_grade_count(store, ollama, capsys):
    seal(store)
    write_test_labels(store, [make_test_label("4821", 3, WEEK_LATER)])
    st = service.shadow_status(store, now=lambda: WEEK_LATER + timedelta(days=5))
    assert (st.test_labels, st.total_target_met, st.consequential_target_met) == (1, False, False)
    assert st.sealed_comments == 1 and st.verified and not st.revealed and not st.stopping_rule_met
    assert cli.main(["--root", str(store), "shadow", "status"]) == 0
    out = capsys.readouterr().out
    assert "graded 2 or 3: not yet" in out and "stopping rule: not yet" in out
    assert shadow.read_reveal(store) is None
