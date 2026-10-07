"""Label records: the analysis rule, progress counts, and counts-only summaries."""

from __future__ import annotations

from typing import Any

from afterword import label_records as lr
from afterword import taxonomy


def label(
    comment_id: str,
    pass_name: str = "initial",
    *,
    at: str = "2026-10-01T10:00:00Z",
    cls: str = "CONVERSATIONAL",
    pro: int = 0,
    retro: int | None = 0,
    flags: list[str] | None = None,
    batch: str = "b1",
    replied: bool = False,
) -> dict[str, Any]:
    return {
        "comment_id": comment_id,
        "pass": pass_name,
        "labeled_at": at,
        "primary_class": cls,
        "flags": flags or [],
        "consequential_prospective": pro,
        "consequential_retrospective": retro,
        "replied_before_labeling": replied,
        "batch_id": batch,
    }


def test_analysis_uses_the_latest_label_outside_self_agreement():
    labels = [
        label("a", at="2026-10-01T10:00:00Z", cls="CORRECTION"),
        label("a", "calibration", at="2026-10-20T10:00:00Z", cls="CONVERSATIONAL"),
        label("a", "self_agreement", at="2026-11-01T10:00:00Z", cls="UNCERTAIN"),
        label("b", at="2026-10-02T10:00:00Z", cls="TECHNICAL_QUESTION"),
        label("b", "self_agreement", at="2026-11-01T10:00:00Z", cls="UNCERTAIN"),
        label("c", "self_agreement", at="2026-11-01T10:00:00Z"),
    ]
    chosen = lr.analysis_labels(labels)
    assert {k: v["primary_class"] for k, v in chosen.items()} == {
        "a": "CONVERSATIONAL",
        "b": "TECHNICAL_QUESTION",
    }


def test_a_tie_in_time_goes_to_the_calibration_label():
    same = "2026-10-01T10:00:00Z"
    labels = [label("a", "calibration", at=same, cls="CORRECTION"), label("a", at=same)]
    assert lr.analysis_labels(labels)["a"]["primary_class"] == "CORRECTION"


def test_progress_counts_eligible_comments_by_pass_and_tool():
    batches = [
        {"event": "batch_start", "batch_id": "old"},
        {"event": "batch_start", "batch_id": "t", "tool": "terminal"},
        {"event": "batch_start", "batch_id": "w", "tool": "browser"},
        {"event": "batch_end", "batch_id": "w"},
    ]
    labels = [
        label("a", batch="old"),
        label("b", batch="t"),
        label("c", batch="w"),
        label("a", "calibration", batch="w"),
        label("gone", batch="w"),  # deleted upstream since: not in the run
    ]
    counts = lr.progress({"a", "b", "c", "d", "e"}, labels, batches)
    assert counts == lr.LabelProgress(
        eligible=5,
        labeled=3,
        remaining=2,
        relabeled=1,
        by_pass={"initial": 3, "calibration": 1, "self_agreement": 0},
        by_tool={"terminal": 1, "browser": 2, "not recorded": 1},
        by_post_order={"published": 4, "random": 0, "unknown": 0},
        not_in_run=1,
    )


def test_labels_split_by_the_post_order_of_their_batch():
    batches = [
        {"event": "batch_start", "batch_id": "old"},  # predates post_order: published
        {"event": "batch_start", "batch_id": "p", "post_order": "published"},
        {"event": "batch_start", "batch_id": "r", "post_order": "random", "seed": 7},
    ]
    labels = [label("a", batch="old"), label("b", batch="p"), label("c", batch="r")]
    labels.append(label("d", batch="missing"))
    split = lr.split_by_post_order(labels, batches)
    assert {k: [r["comment_id"] for r in v] for k, v in split.items()} == {
        "published": ["a", "b"],
        "random": ["c"],
        "unknown": ["d"],
    }


def test_oracle_ceiling_applies_the_policy_to_the_labels():
    labels = [
        label("a", cls="CORRECTION", pro=3),
        label("b", cls="LIGHTWEIGHT_ACKNOWLEDGMENT", pro=0, flags=["REPLY_TO_AUTHOR"]),
        label("c", cls="LIKELY_SPAM_OR_NOISE", pro=2),
        label("d", cls="TECHNICAL_EXTENSION", pro=1),
    ]
    ceiling = lr.oracle_ceiling(labels)
    assert ceiling["class_only"]["by_tier"] == {"SURFACE": 1, "QUEUE": 1, "COLLAPSED": 2}
    assert ceiling["class_only"]["consequential_by_tier"] == {
        "SURFACE": 1,
        "QUEUE": 0,
        "COLLAPSED": 1,
    }
    assert ceiling["class_only"]["consequential_surfaced"] == 1
    assert ceiling["class_and_flags"]["collapsed"] == 1
    table = lr.class_crosstab(labels)
    assert table["CORRECTION"] == {"0": 0, "1": 0, "2": 0, "3": 1, "total": 1, "tier": "SURFACE"}
    assert list(table) == list(taxonomy.CLASSES)


def test_summary_counts_classes_grades_agreement_and_replies():
    labels = [
        label("a", cls="CORRECTION", pro=3, retro=3, replied=True),
        label("b", cls="TECHNICAL_QUESTION", pro=2, retro=1, replied=True),
        label("c", pro=1, retro=2),
        label("d", pro=0, retro=None),
        label("e", pro=1, retro=1),
    ]
    summary = lr.summarize(labels)
    assert summary["total"] == 5
    assert list(summary["by_class"]) == list(taxonomy.CLASSES)
    assert summary["by_class"]["CONVERSATIONAL"] == 3
    assert summary["prospective"] == {0: 1, 1: 2, 2: 1, 3: 1}
    assert summary["consequential"] == 2
    assert summary["with_retrospective"] == 4
    assert summary["retrospective_same_grade"] == 2
    assert summary["retrospective_same_binary"] == 2
    assert summary["consequential_only_in_hindsight"] == 1
    assert summary["consequential_only_prospectively"] == 1
    assert summary["replied_before_labeling"] == 2


def test_calibration_differences_are_counts_against_the_initial_label():
    labels = [
        label("a", cls="CORRECTION", pro=3, flags=["REPLY_TO_AUTHOR", "CONTAINS_CODE"]),
        label("a", "calibration", cls="CORRECTION", pro=1, flags=["CONTAINS_CODE"]),
        label("b", pro=0),
        label("b", "calibration", cls="TECHNICAL_QUESTION", pro=2),
        label("c", pro=1),
        label("c", "calibration", pro=1),
        label("d", "calibration", pro=1),  # no initial label: not compared
    ]
    assert lr.calibration_differences(labels) == {
        "compared": 3,
        "same_class": 2,
        "same_prospective": 1,
        "same_consequential": 1,
        "became_consequential": 1,
        "stopped_being_consequential": 1,
        "same_labeler_flags": 3,
    }


def test_progress_carries_no_class_or_grade():
    fields = set(lr.LabelProgress.__dataclass_fields__)
    assert fields == {
        "eligible",
        "labeled",
        "remaining",
        "relabeled",
        "by_pass",
        "by_tool",
        "by_post_order",
        "not_in_run",
    }


def test_summaries_report_each_post_order_and_the_whole():
    batches = [
        {"event": "batch_start", "batch_id": "p", "post_order": "published"},
        {"event": "batch_start", "batch_id": "r", "post_order": "random"},
    ]
    labels = [label("a", batch="p", pro=3), label("b", batch="r"), label("c", batch="r")]
    out = lr.summarize_by_post_order(labels, batches)
    assert set(out) == {"published", "random", "all"}
    assert (out["published"]["total"], out["random"]["total"], out["all"]["total"]) == (1, 2, 3)
    assert out["published"]["consequential"] == 1


def test_analysis_uses_deterministic_code_and_link_flags_for_every_label():
    old = label("a", flags=["REPLY_TO_AUTHOR", "CONTAINS_LINK", "HOSTILE_TONE"])
    updated = lr.with_content_flags(old, {"CONTAINS_CODE"})
    assert updated["flags"] == ["REPLY_TO_AUTHOR", "CONTAINS_CODE", "HOSTILE_TONE"]
    assert old["flags"] == ["REPLY_TO_AUTHOR", "CONTAINS_LINK", "HOSTILE_TONE"]  # unchanged
    assert lr.with_content_flags(label("b"), set())["flags"] == []


def test_the_broad_rsc_ceiling_ignores_rsc_on_tax_v0_1_labels_only():
    old = label("a", cls="LIGHTWEIGHT_ACKNOWLEDGMENT", flags=["REFERENCES_SPECIFIC_CLAIM"])
    old["taxonomy_version"] = "tax-v0.1"
    new = old | {"comment_id": "b", "taxonomy_version": "tax-v0.2"}
    ceiling = lr.oracle_ceiling([old, new])
    assert ceiling["class_and_flags"]["collapsed"] == 0
    assert ceiling["class_and_flags_without_broad_rsc"]["collapsed"] == 1
    assert ceiling["class_and_flags_without_rsc"]["collapsed"] == 2
    assert list(ceiling) == [name for name, _, _ in lr.ORACLE_VARIANTS]


def test_wilson_interval_brackets_the_share():
    low, high = lr.wilson(39, 150)
    assert round(low, 3) == 0.196 and round(high, 3) == 0.336
    assert lr.wilson(0, 0) == (0.0, 0.0)
    assert lr.wilson(0, 10)[0] == 0.0
