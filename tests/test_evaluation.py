"""Offline evaluation on dev labels: scoring, pp-v0.2, heuristic versions (synthetic only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, heuristic, label_records, policy, scoring, service
from afterword.normalize import normalize
from afterword.sqlite_store import SqliteRepository
from tests.fake_models import QWEN, FakeOllama, answer
from tests.test_store import Runs

REASON = "Synthetic reason that must never be printed"


def label(comment_id: str, cls: str, pro: int, batch: str, flags: list[str] | None = None):
    return {
        "comment_id": comment_id,
        "pass": "initial",
        "labeled_at": "2026-10-05T10:00:00Z",
        "primary_class": cls,
        "flags": flags or [],
        "consequential_prospective": pro,
        "consequential_retrospective": pro,
        "replied_before_labeling": False,
        "taxonomy_version": "tax-v0.2",
        "reason": REASON,
        "batch_id": batch,
    }


def write_labels(root: Path, records: list[dict[str, Any]]) -> None:
    out = root / label_records.label_dir(Path("."), "unfrozen")
    out.mkdir(parents=True, exist_ok=True)
    (out / "initial.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in records), encoding="utf-8"
    )
    batches = [
        {"event": "batch_start", "batch_id": "b1", "post_order": "published"},
        {"event": "batch_start", "batch_id": "b2", "post_order": "random", "seed": 1},
    ]
    (out / "batches.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in batches), encoding="utf-8"
    )


LABELS = [
    label("s1a1", "TECHNICAL_QUESTION", 3, "b1"),
    label("s1b1", "TECHNICAL_EXTENSION", 2, "b1", ["REFERENCES_SPECIFIC_CLAIM"]),
    label("s1a3", "TECHNICAL_QUESTION", 2, "b2"),
    label("4821", "LIGHTWEIGHT_ACKNOWLEDGMENT", 0, "b2"),
]


@pytest.fixture
def labeled(tmp_path, fake_dev):
    runs = Runs(tmp_path, fake_dev)
    runs.ingest()
    write_labels(tmp_path, LABELS)
    return runs


def stored_tiers(root: Path) -> dict[str, str]:
    repo = SqliteRepository(root / service.STORE_PATH)
    try:
        cid = repo.list_connections()[0].connection_id
        return {
            c: repo.priority_assignments(cid, c)[-1].tier for c in ("s1a1", "s1a3", "s1b1", "4821")
        }
    finally:
        repo.close()


# Policy ------------------------------------------------------------------------------


def decision(flags: set[str], version: str, cls: str = "LIGHTWEIGHT_ACKNOWLEDGMENT"):
    return policy.assign(
        policy.PolicyInput("OK", cls, frozenset(flags), None, False), policy_version=version
    )


def test_pp_v0_2_makes_judgment_flags_informational_only():
    for flag in ("REFERENCES_SPECIFIC_CLAIM", "NEEDS_THREAD_CONTEXT"):
        assert decision({flag}, "pp-v0.1").tier is policy.Tier.QUEUE
        later = decision({flag}, "pp-v0.2")
        assert later.tier is policy.Tier.COLLAPSED
        assert later.rules_fired == ("class_default:LIGHTWEIGHT_ACKNOWLEDGMENT",)
        assert later.policy_version == "pp-v0.2"
    assert decision({"REPLY_TO_AUTHOR"}, "pp-v0.2").tier is policy.Tier.QUEUE
    assert decision({"POSSIBLE_INSTRUCTION_TEXT"}, "pp-v0.2").tier is policy.Tier.SURFACE
    assert decision(set(), "pp-v0.2", "TECHNICAL_QUESTION").tier is policy.Tier.SURFACE
    with pytest.raises(ValueError):
        decision(set(), "pp-v9")


# Heuristic versions ------------------------------------------------------------------


def test_heuristic_versions_differ_only_in_the_length_threshold():
    assert heuristic.HEURISTIC_VERSIONS == {"hb-v0.1": 280, "hb-v0.2": 281}
    text = normalize("<p>" + "x" * 280 + "</p>", "HTML")
    assert heuristic.classify(text, "hb-v0.1").primary_class == "CONVERSATIONAL"
    second = heuristic.classify(text, "hb-v0.2")
    assert (second.primary_class, second.version) == ("LIGHTWEIGHT_ACKNOWLEDGMENT", "hb-v0.2")
    assert second.explanation.startswith("hb-v0.2 ")
    with pytest.raises(ValueError):
        heuristic.classify(text, "hb-v9")


# Scoring -----------------------------------------------------------------------------


def scored(cid: str, grade: int, tier: str, base: str | None = None, **kw: Any) -> scoring.Scored:
    return scoring.Scored(
        comment_id=cid,
        label={"consequential_prospective": grade, "primary_class": "CONVERSATIONAL"}
        | kw.pop("label", {}),
        post_order=kw.pop("order", "published"),
        outcome="OK",
        primary_class=kw.pop("cls", "CONVERSATIONAL"),
        classifier_flags=frozenset(kw.pop("flags", ())),
        tier=tier,
        base_tier=base or tier,
    )


def test_score_counts_recall_reduction_classes_flags_and_raises():
    items = [
        scored("a", 3, "SURFACE"),
        scored("b", 2, "COLLAPSED"),
        scored("c", 0, "QUEUE", "COLLAPSED", flags={"REFERENCES_SPECIFIC_CLAIM"}),
        scored("d", 1, "COLLAPSED", order="random", cls="LIGHTWEIGHT_ACKNOWLEDGMENT"),
    ]
    out = scoring.score(items)
    c = out.counts
    assert c["consequential_recall"]["count"] == 1 and c["consequential_recall"]["of"] == 2
    assert c["review_reduction"]["count"] == 2 and c["surface_size"] == 1
    assert out.missed_ids == ["b"]
    assert c["per_class"]["CONVERSATIONAL"] == {"predicted": 3, "labeled": 4, "agree": 3}
    assert c["flag_precision"]["REFERENCES_SPECIFIC_CLAIM"] == {"set": 1, "agree": 0, "labeled": 0}
    assert c["flag_caused_raises"] == {"raised": 1, "graded_0_or_1": 1}
    split = scoring.score_by_post_order(items)
    assert (split["published"].counts["total"], split["random"].counts["total"]) == (3, 1)


# Service: offline evaluation -----------------------------------------------------------


def test_b1_evaluation_matches_the_stored_tiers_and_needs_no_model(labeled, tmp_path):
    before = service.evaluate_condition(tmp_path, condition="b1")
    assert before.scored == 0 and before.not_scored == {"not_classified": 4}
    service.classify_comments(tmp_path, condition="b1")
    result = service.evaluate_condition(tmp_path, condition="b1")
    tiers = stored_tiers(tmp_path)
    s = result.scores["all"]
    assert result.scored == 4 and s["total"] == 4
    assert s["by_tier"] == {t: list(tiers.values()).count(t) for t in scoring.TIERS}
    expected = sorted(
        c for c, grade in (("s1a1", 3), ("s1b1", 2), ("s1a3", 2)) if tiers[c] == "COLLAPSED"
    )
    assert result.missed_ids == expected
    assert result.scores["published"]["total"] == 2 and result.scores["random"]["total"] == 2
    assert result.oracle["class_and_flags"]["consequential"] == 3


def test_policies_are_compared_on_cached_model_output_without_calling_the_model(
    labeled, tmp_path, no_live_api
):
    fake = FakeOllama(
        no_live_api,
        reply=lambda body: answer("LIGHTWEIGHT_ACKNOWLEDGMENT", ["REFERENCES_SPECIFIC_CLAIM"]),
    )
    service.classify_comments(tmp_path, condition="b2", model=QWEN)
    calls = len(fake.chats)
    first = service.evaluate_condition(tmp_path, condition="b2", model=QWEN)
    second = service.evaluate_condition(
        tmp_path, condition="b2", model=QWEN, policy_version="pp-v0.2"
    )
    assert len(fake.chats) == calls  # no model call to score or to re-apply a policy
    assert first.model_digests and first.prompt_version == "pr-v0.2"
    a, b = first.scores["all"], second.scores["all"]
    assert a["by_tier"]["COLLAPSED"] == 0
    # Under pp-v0.2 the model's RSC no longer raises; s1a3 still replies to the author.
    assert b["by_tier"]["COLLAPSED"] == 3 and b["by_tier"]["QUEUE"] == 1
    assert a["flag_caused_raises"]["raised"] == 3 and b["flag_caused_raises"]["raised"] == 0
    assert a["flag_precision"]["REFERENCES_SPECIFIC_CLAIM"] == {"set": 4, "agree": 1, "labeled": 1}
    assert second.missed_ids == ["s1a1", "s1b1"]


def test_only_ids_restricts_classification_and_scoring(labeled, tmp_path):
    result = service.classify_comments(tmp_path, condition="b1", only_ids={"s1a1", "4821"})
    assert result.subjects == 2
    scored_ = service.evaluate_condition(tmp_path, condition="b1", only_ids={"s1a1"})
    assert (scored_.labels, scored_.scored) == (1, 1)


def test_threshold_sweep_scores_in_memory_and_stores_nothing(labeled, tmp_path):
    sweep = service.tune_b1_threshold(tmp_path, [0, 10_000])
    assert sweep[0]["all"]["by_tier"]["COLLAPSED"] <= sweep[10_000]["all"]["by_tier"]["COLLAPSED"]
    repo = SqliteRepository(tmp_path / service.STORE_PATH)
    try:
        cid = repo.list_connections()[0].connection_id
        assert repo.count_connection(cid)["classifications"] == 0
    finally:
        repo.close()


def test_reports_hold_counts_and_the_miss_list_holds_ids_only(labeled, tmp_path, capsys):
    service.classify_comments(tmp_path, condition="b1")
    args = ["--root", str(tmp_path), "evaluate", "--condition", "b1", "--misses"]
    assert cli.main(args) == 0
    out = capsys.readouterr().out
    assert "consequential surfaced" in out and REASON not in out and "Synthetic" not in out
    reports = sorted((tmp_path / service.EVAL_ROOT).iterdir())
    report = next(p for p in reports if p.suffix == ".json")
    text = report.read_text(encoding="utf-8")
    assert REASON not in text and "missed_ids" not in text
    misses = next(p for p in reports if p.name.endswith("-misses.txt"))
    for line in misses.read_text(encoding="utf-8").splitlines():
        assert line in {"s1a1", "s1b1", "s1a3"}


def test_evaluation_refuses_unknown_versions_and_b2_without_a_model(labeled, tmp_path):
    with pytest.raises(service.ServiceError):
        service.evaluate_condition(tmp_path, condition="b1", policy_version="pp-v9")
    with pytest.raises(service.ServiceError):
        service.evaluate_condition(tmp_path, condition="b1", heuristic_version="hb-v9")
    with pytest.raises(service.ServiceError):
        service.evaluate_condition(tmp_path, condition="b2")
