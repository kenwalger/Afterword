"""The preregistration record and `--set test` selection (ADR-010; synthetic only)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, label_records, preregistration, service
from afterword.preregistration import PreregistrationError, corpus_set_of
from tests.fake_models import LLAMA
from tests.test_labeling import NOW, make_run

# Synthetic posts: 9000001 published 2026-08-03 (comments s1a1 08-03, s1b1 08-05,
# s1a3 08-12; s1a2 is the author's), 9000002 published 2026-08-17 (4821, 08-18).
# Registered on 2026-08-10: s1a1 and s1b1 are dev, 4821 is test, s1a3 is neither.
REGISTERED = "2026-08-10T00:00:00Z"


def record(**overrides: Any) -> dict[str, Any]:
    return {
        "registered_at": REGISTERED,
        "b1_heuristic": "hb-v0.2",
        "b2_provider": "ollama",
        "b2_model": LLAMA,
        "b2_model_digest": "46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e",
        "policy_version": "pp-v0.2",
        "num_ctx": 4096,
    } | overrides


def write_record(root: Path, **overrides: Any) -> Path:
    path = root / preregistration.RECORD_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record(**overrides)), encoding="utf-8")
    return path


def utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# The record -----------------------------------------------------------------------


def test_no_record_means_no_preregistration(tmp_path):
    assert preregistration.load(tmp_path) is None


def test_a_valid_record_loads(tmp_path):
    write_record(tmp_path)
    loaded = preregistration.load(tmp_path)
    assert loaded is not None
    assert loaded.registered_at == datetime(2026, 8, 10, tzinfo=UTC)
    assert (loaded.b2_model, loaded.policy_version, loaded.num_ctx) == (LLAMA, "pp-v0.2", 4096)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"registered_at": "2026-08-10T00:00:00"}, "UTC"),
        ({"registered_at": "2026-08-10T02:00:00+02:00"}, "UTC"),
        ({"registered_at": "yesterday"}, "RFC 3339"),
        ({"b2_model": ""}, "b2_model"),
        ({"num_ctx": 0}, "num_ctx"),
    ],
)
def test_invalid_records_are_refused(tmp_path, overrides, message):
    write_record(tmp_path, **overrides)
    with pytest.raises(PreregistrationError, match=message):
        preregistration.load(tmp_path)


def test_a_record_missing_a_field_is_refused(tmp_path):
    data = record()
    del data["policy_version"]
    path = tmp_path / preregistration.RECORD_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(PreregistrationError, match="policy_version"):
        preregistration.load(tmp_path)


def test_a_record_that_is_not_json_is_refused(tmp_path):
    path = tmp_path / preregistration.RECORD_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PreregistrationError, match="not valid JSON"):
        preregistration.load(tmp_path)


# Set membership (ADR-010) ---------------------------------------------------------


@pytest.mark.parametrize(
    ("published", "created", "expected"),
    [
        ("2026-08-17T09:00:00Z", "2026-08-18T11:00:00Z", "test"),
        ("2026-08-03T09:00:00Z", "2026-08-05T19:15:00Z", "dev"),
        ("2026-08-03T09:00:00Z", "2026-08-10T00:00:00Z", "dev"),
        ("2026-08-03T09:00:00Z", "2026-08-12T10:00:00Z", None),
        ("2026-08-10T00:00:00Z", "2026-08-12T10:00:00Z", None),
    ],
)
def test_sets_follow_adr_010(published, created, expected):
    assert (
        corpus_set_of(
            published_at=utc(published), created_at=utc(created), registered_at=utc(REGISTERED)
        )
        == expected
    )


def test_before_preregistration_everything_is_dev():
    assert corpus_set_of(published_at=None, created_at=None, registered_at=None) == "dev"


def test_unknown_times_after_preregistration_belong_to_neither_set():
    assert corpus_set_of(published_at=None, created_at=NOW, registered_at=NOW) is None


# The labeling tools ---------------------------------------------------------------


def test_set_test_selects_only_comments_on_posts_published_after_the_record(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    write_record(tmp_path)
    dev = service.open_for_labeling(tmp_path, "r1", now=lambda: NOW)
    test = service.open_for_labeling(tmp_path, "r1", corpus_set="test", now=lambda: NOW)
    assert dev.sets == {"dev": 2, "test": 1, "neither": 1}
    assert sorted(service.labelable_ids(dev)) == ["s1a1", "s1b1"]
    assert sorted(service.labelable_ids(test)) == ["4821"]
    assert (dev.subjects, test.subjects) == (2, 1)


def test_without_a_record_dev_is_every_comment_and_test_is_refused(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    session = service.open_for_labeling(tmp_path, "r1", now=lambda: NOW)
    assert session.subjects == 4 and session.sets == {"dev": 4, "test": 0, "neither": 0}
    with pytest.raises(service.ServiceError, match="preregistration record"):
        service.open_for_labeling(tmp_path, "r1", corpus_set="test", now=lambda: NOW)


def test_an_invalid_record_stops_labeling(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    write_record(tmp_path, registered_at="soon")
    with pytest.raises(service.ServiceError, match="RFC 3339"):
        service.open_for_labeling(tmp_path, "r1", now=lambda: NOW)


def test_a_test_batch_labels_test_comments_and_records_the_set(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    write_record(tmp_path)
    session = service.open_for_labeling(tmp_path, "r1", corpus_set="test", now=lambda: NOW)
    batch = service.start_label_batch(
        session,
        root=tmp_path,
        pass_name="initial",
        corpus_version="unfrozen",
        corpus_set="test",
        batch_size=40,
        only_ids=None,
    )
    assert batch is not None and [c.source_object_id for c in batch.items] == ["4821"]
    saved = service.save_label(
        batch,
        0,
        primary="TECHNICAL_QUESTION",
        flags=[],
        prospective=2,
        retrospective=None,
        reason="synthetic",
        note="",
        duration_seconds=3.0,
    )
    assert saved["corpus_set"] == "test"
    test_counts = service.label_progress(session, root=tmp_path, corpus_version="unfrozen")
    assert (test_counts.eligible, test_counts.labeled, test_counts.not_in_run) == (1, 1, 0)
    dev = service.open_for_labeling(tmp_path, "r1", now=lambda: NOW)
    dev_counts = service.label_progress(dev, root=tmp_path, corpus_version="unfrozen")
    assert (dev_counts.eligible, dev_counts.labeled, dev_counts.not_in_run) == (2, 0, 0)


def test_labels_without_a_set_are_dev_labels():
    assert label_records.set_of({"comment_id": "a"}) == "dev"
    labels = [{"comment_id": "a"}, {"comment_id": "b", "corpus_set": "test"}]
    assert [r["comment_id"] for r in label_records.of_set(labels, "test")] == ["b"]


def test_label_status_set_test_before_preregistration_exits_2(tmp_path, fake_dev, capsys):
    make_run(tmp_path, finished=NOW)
    code = cli.main(["--root", str(tmp_path), "label", "status", "--run", "r1", "--set", "test"])
    assert code == 2
    assert "preregistration record" in capsys.readouterr().err


def test_label_status_prints_set_counts_after_preregistration(tmp_path, fake_dev, capsys):
    make_run(tmp_path, finished=NOW)
    write_record(tmp_path)
    code = cli.main(["--root", str(tmp_path), "label", "status", "--run", "r1", "--set", "test"])
    out = capsys.readouterr().out
    assert code == 0
    assert "dev 2, test 1, neither 1" in out
    assert "1 eligible comments" in out


def test_the_cli_refuses_an_unknown_set(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    with pytest.raises(SystemExit):
        cli.main(["--root", str(tmp_path), "label", "status", "--run", "r1", "--set", "train"])


def test_dev_scoring_never_reads_test_labels(tmp_path, fake_dev):
    from tests.test_evaluation import LABELS, write_labels
    from tests.test_store import Runs

    Runs(tmp_path, fake_dev).ingest()
    marked = [dict(r) for r in LABELS]
    marked[3]["corpus_set"] = "test"
    write_labels(tmp_path, marked)
    service.classify_comments(tmp_path, condition="b1")
    result = service.evaluate_condition(tmp_path, condition="b1")
    assert result.labels == 3 and result.scored == 3


# Exclusions: posts about Afterword (ADR-010, amended 2026-10-18) --------------------

EXCLUSION = {"post_id": "9000002", "reason": "post about Afterword", "recorded_at": REGISTERED}


def test_an_excluded_test_period_post_belongs_to_neither_set():
    args = {"registered_at": utc(REGISTERED), "excluded": frozenset({"9000002"})}
    on_test_post = {"published_at": utc("2026-08-17T09:00:00Z"), "created_at": NOW}
    assert corpus_set_of(**on_test_post, post_id="9000002", **args) is None
    assert corpus_set_of(**on_test_post, post_id="9000004", **args) == "test"
    before = {
        "published_at": utc("2026-08-03T09:00:00Z"),
        "created_at": utc("2026-08-05T00:00:00Z"),
    }
    assert corpus_set_of(**before, post_id="9000002", **args) == "dev"


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ([EXCLUSION, EXCLUSION], "listed twice"),
        ([EXCLUSION | {"reason": " "}], "reason"),
        ([EXCLUSION | {"recorded_at": "2026-08-10"}], "UTC"),
        ([EXCLUSION | {"post_id": 9000002}], "post_id"),
        ([EXCLUSION | {"after_labeling": "yes"}], "after_labeling"),
        ("9000002", "must be a list"),
    ],
)
def test_invalid_exclusions_are_refused(tmp_path, entries, message):
    write_record(tmp_path, excluded_posts=entries)
    with pytest.raises(PreregistrationError, match=message):
        preregistration.load(tmp_path)


def test_the_labeling_tools_honor_the_exclusions(tmp_path, fake_dev):
    make_run(tmp_path, finished=NOW)
    write_record(tmp_path, excluded_posts=[EXCLUSION])
    session = service.open_for_labeling(tmp_path, "r1", corpus_set="test", now=lambda: NOW)
    assert session.subjects == 0 and session.sets == {"dev": 2, "test": 0, "neither": 2}


def ingested(tmp_path, fake_dev):
    from tests.test_store import Runs

    Runs(tmp_path, fake_dev).ingest()
    write_record(tmp_path)


def test_posts_lists_test_period_posts_with_their_ids(tmp_path, fake_dev, capsys):
    ingested(tmp_path, fake_dev)
    rows = service.list_test_period_posts(tmp_path)
    assert [(r.post_id, r.comments_from_others, r.excluded) for r in rows] == [
        ("9000003", 0, False),
        ("9000002", 1, False),
    ]
    assert cli.main(["--root", str(tmp_path), "preregistration", "posts"]) == 0
    assert "9000002  2026-08-17  test" in capsys.readouterr().out


def test_exclude_post_records_an_amendment_and_the_tools_follow_it(tmp_path, fake_dev, capsys):
    ingested(tmp_path, fake_dev)
    when = datetime(2026, 8, 20, 9, 0, tzinfo=UTC)
    made = service.exclude_post(
        tmp_path, post_id="9000002", reason="post about Afterword", now=lambda: when
    )
    assert (made.after_labeling, made.test_labels_on_post, made.sealed_on_post) == (False, 0, 0)
    saved = json.loads((tmp_path / preregistration.RECORD_PATH).read_text(encoding="utf-8"))
    assert saved["excluded_posts"] == [
        {
            "post_id": "9000002",
            "reason": "post about Afterword",
            "recorded_at": "2026-08-20T09:00:00Z",
        }
    ]
    assert saved["registered_at"] == REGISTERED and saved["b2_model"] == LLAMA
    assert [r.excluded for r in service.list_test_period_posts(tmp_path)] == [False, True]
    assert service.classify_comments(tmp_path, condition="b1", corpus_set="test").subjects == 0
    with pytest.raises(service.ServiceError, match="already excluded"):
        service.exclude_post(tmp_path, post_id="9000002", reason="again")


@pytest.mark.parametrize(
    ("post_id", "message"),
    [("9000001", "published before preregistration"), ("123", "not in the store")],
)
def test_exclude_post_refuses_posts_that_are_not_test_posts(tmp_path, fake_dev, post_id, message):
    ingested(tmp_path, fake_dev)
    with pytest.raises(service.ServiceError, match=message):
        service.exclude_post(tmp_path, post_id=post_id, reason="post about Afterword")


def test_a_late_exclusion_needs_acknowledging_and_is_recorded_as_late(tmp_path, fake_dev, capsys):
    ingested(tmp_path, fake_dev)
    out = label_records.label_dir(tmp_path, "unfrozen")
    out.mkdir(parents=True)
    test_label = {
        "comment_id": "4821",
        "pass": "initial",
        "corpus_set": "test",
        "labeled_at": "2026-08-19T10:00:00Z",
        "primary_class": "CONVERSATIONAL",
        "consequential_prospective": 1,
    }
    (out / "initial.jsonl").write_text(json.dumps(test_label) + "\n", encoding="utf-8")
    code = cli.main(
        ["--root", str(tmp_path), "preregistration", "exclude-post", "--post", "9000002"]
    )
    assert code == 2 and "--after-labeling" in capsys.readouterr().err
    code = cli.main(
        [
            "--root",
            str(tmp_path),
            "preregistration",
            "exclude-post",
            "--post",
            "9000002",
            "--after-labeling",
        ]
    )
    assert code == 0 and "deviation, recorded" in capsys.readouterr().out
    record = preregistration.load(tmp_path)
    assert record is not None and record.excluded_posts[0].after_labeling is True
    status = service.shadow_status(tmp_path, now=lambda: NOW)
    assert status.test_labels == 0  # the label on the excluded post no longer counts


def test_nothing_is_sealed_or_frozen_for_an_excluded_post(tmp_path, fake_dev, no_live_api):
    from tests.fake_models import FakeOllama

    FakeOllama(no_live_api)
    ingested(tmp_path, fake_dev)
    write_record(tmp_path, excluded_posts=[EXCLUSION])
    result = service.shadow_run(tmp_path, now=lambda: datetime(2026, 8, 20, tzinfo=UTC))
    assert result.test_comments == 0 and result.sealed_file is None
    with pytest.raises(service.ServiceError, match="no test comments"):
        service.export_corpus(tmp_path, version="v1", corpus_set="test")


def test_a_sealed_comment_on_a_post_excluded_later_drops_out_of_the_counts(
    tmp_path, fake_dev, no_live_api
):
    from tests.fake_models import FakeOllama

    FakeOllama(no_live_api)
    ingested(tmp_path, fake_dev)
    assert (
        service.shadow_run(tmp_path, now=lambda: datetime(2026, 8, 20, tzinfo=UTC)).comments_sealed
        == 1
    )
    service.exclude_post(tmp_path, post_id="9000002", reason="post about Afterword")
    status = service.shadow_status(tmp_path, now=lambda: NOW)
    assert status.sealed_comments == 0 and status.verified
    reveal = service.shadow_reveal(tmp_path, now=lambda: datetime(2026, 12, 31, tzinfo=UTC))
    assert reveal["sealed_comments"] == 0 and reveal["sealed_no_longer_in_test_set"] == 1
    assert reveal["excluded_posts"] == 1
