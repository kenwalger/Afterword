"""Self-agreement draw and report (LABELING-GUIDE.md; synthetic labels only)."""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, label_records, service

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=UTC)
REASON = "Synthetic reason that must never be printed"


def label(
    comment_id: str,
    *,
    grade: int = 0,
    cls: str = "CONVERSATIONAL",
    days_ago: float = 20,
    pass_name: str = "initial",
    corpus_set: str | None = None,
) -> dict[str, Any]:
    at = (NOW - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")
    record: dict[str, Any] = {
        "comment_id": comment_id,
        "pass": pass_name,
        "labeled_at": at,
        "primary_class": cls,
        "consequential_prospective": grade,
        "reason": REASON,
    }
    if corpus_set is not None:
        record["corpus_set"] = corpus_set
    return record


def write(root: Path, records: list[dict[str, Any]]) -> None:
    out = label_records.label_dir(root, "unfrozen")
    out.mkdir(parents=True, exist_ok=True)
    by_pass: dict[str, list[dict[str, Any]]] = {}
    for r in records:
        by_pass.setdefault(r["pass"], []).append(r)
    for name, rows in by_pass.items():
        (out / f"{name}.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )


POOL = [label(f"c{i:02d}", grade=2 if i < 6 else (i % 2)) for i in range(40)] + [
    label("young", grade=3, days_ago=3),
    label("t1", grade=3, corpus_set="test"),
]


# The draw ------------------------------------------------------------------------------


def test_the_draw_follows_the_guide_rule():
    draw = label_records.draw_self_agreement(POOL, now=NOW, seed=20261018)
    pooled = sorted(f"c{i:02d}" for i in range(40))
    expected_random = random.Random(20261018).sample(pooled, 25)
    graded = {f"c{i:02d}" for i in range(6)}
    assert draw.pool == 40 and draw.graded == 6 and draw.random_drawn == 25
    assert draw.ids == sorted(graded | set(expected_random))
    assert draw.random_also_graded == len(graded & set(expected_random))
    assert "young" not in draw.ids and "t1" not in draw.ids
    assert draw.cutoff == NOW - timedelta(days=14)


def test_the_draw_is_reproducible_and_depends_on_the_seed():
    a = label_records.draw_self_agreement(POOL, now=NOW, seed=1)
    b = label_records.draw_self_agreement(POOL, now=NOW, seed=1)
    c = label_records.draw_self_agreement(POOL, now=NOW, seed=2)
    assert a.ids == b.ids and a.ids != c.ids


def test_a_calibration_label_restarts_the_clock():
    records = [label("a", grade=2), label("a", grade=2, days_ago=2, pass_name="calibration")]
    draw = label_records.draw_self_agreement(records, now=NOW, seed=1)
    assert draw.pool == 0 and draw.ids == []


def test_the_random_part_never_exceeds_the_pool():
    draw = label_records.draw_self_agreement(POOL[:3], now=NOW, seed=1)
    assert draw.random_drawn == 3 and len(draw.ids) == 3


def test_test_labels_are_drawn_only_for_the_test_set():
    draw = label_records.draw_self_agreement(POOL, now=NOW, seed=1, corpus_set="test")
    assert draw.ids == ["t1"] and draw.graded == 1


def test_the_draw_command_writes_ids_and_a_record_and_prints_counts_only(tmp_path, capsys):
    write(tmp_path, POOL)
    draw, path = service.draw_self_agreement(tmp_path, seed=7, now=lambda: NOW)
    assert path.name == "self-agreement-20261022-s7.txt"
    assert path.read_text(encoding="utf-8").split() == draw.ids
    sidecar = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    assert sidecar["seed"] == 7 and sidecar["pool"] == 40 and sidecar["sample"] == len(draw.ids)
    assert "ids" not in sidecar
    with pytest.raises(service.ServiceError, match="one draw per day"):
        service.draw_self_agreement(tmp_path, seed=7, now=lambda: NOW)
    code = cli.main(["--root", str(tmp_path), "self-agreement", "draw", "--seed", "8"])
    out = capsys.readouterr().out
    assert code == 0 and "pool 40" in out and "seed 8" in out
    assert not any(f"c{i:02d}" in out for i in range(40))


def test_the_draw_refuses_an_empty_pool(tmp_path):
    write(tmp_path, [label("a", days_ago=1)])
    with pytest.raises(service.ServiceError, match="14 days old"):
        service.draw_self_agreement(tmp_path, seed=1, now=lambda: NOW)


# Cohen's kappa -----------------------------------------------------------------------


def test_kappa_matches_a_hand_computed_example():
    # 10 items: 7 agree. First rater A 6, B 4; second A 5, B 5.
    pairs = [("A", "A")] * 4 + [("A", "B")] * 2 + [("B", "A")] * 1 + [("B", "B")] * 3
    # Observed 0.7; expected 0.6*0.5 + 0.4*0.5 = 0.5; kappa 0.4.
    assert label_records.cohen_kappa(pairs) == pytest.approx(0.4)


def test_kappa_edge_cases():
    assert label_records.cohen_kappa([]) is None
    assert label_records.cohen_kappa([("A", "A"), ("A", "A")]) == 1.0
    assert label_records.cohen_kappa([("A", "A"), ("B", "B")]) == 1.0


# The report --------------------------------------------------------------------------


REPORTED = [
    label("a", grade=2, cls="TECHNICAL_QUESTION", days_ago=30),
    label("b", grade=1, days_ago=30),
    label("c", grade=3, cls="CORRECTION", days_ago=30),
    label("d", grade=0, days_ago=30),
    # Relabels: a keeps everything; b becomes consequential; c changes class and stops
    # being consequential; d is relabeled twice, and the latest is used.
    label("a", grade=2, cls="TECHNICAL_QUESTION", days_ago=1, pass_name="self_agreement"),
    label("b", grade=2, days_ago=1, pass_name="self_agreement"),
    label("c", grade=1, cls="CHALLENGE_OR_COUNTEREXAMPLE", days_ago=1, pass_name="self_agreement"),
    label("d", grade=3, days_ago=2, pass_name="self_agreement"),
    label("d", grade=0, days_ago=1, pass_name="self_agreement"),
    label("orphan", grade=0, days_ago=1, pass_name="self_agreement"),
]


def test_the_report_compares_with_the_analysis_label():
    report = label_records.self_agreement_report(REPORTED)
    assert (report.compared, report.without_original, report.relabeled_too_soon) == (4, 1, 0)
    assert (report.same_class, report.same_grade) == (3, 2)
    assert (report.same_consequential, report.became_consequential) == (2, 1)
    assert report.stopped_being_consequential == 1
    assert report.disagreements == [
        ("b", "consequential: no to yes"),
        ("c", "class"),
        ("c", "consequential: yes to no"),
    ]
    assert report.class_kappa is not None and 0 < report.class_kappa < 1
    counts = report.counts()
    assert "disagreements" not in counts and counts["comments_with_a_disagreement"] == 2


def test_relabels_made_too_soon_are_counted():
    records = [label("a", days_ago=10), label("a", days_ago=1, pass_name="self_agreement")]
    assert label_records.self_agreement_report(records).relabeled_too_soon == 1


def test_the_report_command_prints_counts_and_writes_ids_only(tmp_path, capsys):
    write(tmp_path, REPORTED)
    code = cli.main(["--root", str(tmp_path), "self-agreement", "report"])
    out = capsys.readouterr().out
    assert code == 0
    assert "4 comments compared" in out and "same 2 of 4" in out and "kappa" in out
    assert REASON not in out
    assert not any(f" {c} " in f" {out} " or f"\t{c}" in out for c in ("a", "b", "c", "d"))
    lists = list((tmp_path / service.EVAL_ROOT).glob("self-agreement-report-*-disagreements.txt"))
    assert len(lists) == 1
    text = lists[0].read_text(encoding="utf-8")
    assert text.splitlines() == [
        "b\tconsequential: no to yes",
        "c\tclass",
        "c\tconsequential: yes to no",
    ]
    assert REASON not in text


def test_the_report_refuses_when_nothing_was_relabeled(tmp_path):
    write(tmp_path, POOL)
    with pytest.raises(service.ServiceError, match="no dev self-agreement label"):
        service.report_self_agreement(tmp_path)
