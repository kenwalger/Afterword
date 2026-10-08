"""Scoring classifier conditions against labels on `dev` (`docs/EVALUATION.md`).

Pure functions over already-joined records: one :class:`Scored` item per
labeled comment, holding the analysis label, what the condition predicted, and
the tier a policy gave it. Nothing here reads storage or calls a model, so the
same scoring applies to any cached classification under any policy version.

Every result is counts. The one exception, :attr:`Score.missed_ids`, holds the
IDs of consequential comments a condition collapsed: it is for a git-ignored
local report only and is never printed (``EVALUATION.md``, miss review).
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from afterword import label_records, taxonomy

TIERS: tuple[str, ...] = ("SURFACE", "QUEUE", "COLLAPSED")
COLLAPSED: str = "COLLAPSED"
# Flags a classifier judges (never structural). Their precision is scored
# against the labels, which carry the same flags by the labeler's judgment.
JUDGMENT_FLAGS: tuple[str, ...] = tuple(
    f for f in taxonomy.FLAGS if f not in taxonomy.STRUCTURAL_FLAGS
)
RSC: str = label_records.RSC


@dataclass(frozen=True)
class Scored:
    """One labeled comment as a condition and a policy saw it.

    ``tier`` is the policy's tier with every flag; ``base_tier`` is the tier the
    class default, structural flags, and pre-check give without the flags the
    classifier set itself, so ``tier > base_tier`` is a flag-caused raise.
    """

    comment_id: str
    label: dict[str, Any]
    post_order: str
    outcome: str
    primary_class: str | None
    classifier_flags: frozenset[str]
    tier: str
    base_tier: str


@dataclass(frozen=True)
class Score:
    """Counts for one condition under one policy, on one set of labels."""

    counts: dict[str, Any]
    missed_ids: list[str] = field(default_factory=list)
    failed_ids: list[str] = field(default_factory=list)


def _consequential(item: Scored) -> bool:
    grade = item.label.get("consequential_prospective")
    return isinstance(grade, int) and grade >= label_records.CONSEQUENTIAL_FROM


def _share(k: int, n: int) -> dict[str, Any]:
    low, high = label_records.wilson(k, n)
    return {
        "count": k,
        "of": n,
        "share": round(k / n, 4) if n else None,
        "wilson95": [round(low, 4), round(high, 4)],
    }


def _rank(tier: str) -> int:
    return len(TIERS) - TIERS.index(tier)


def score(items: Iterable[Scored]) -> Score:
    """Score one condition's predictions against the labels.

    :param items: The joined records.
    :returns: Consequential recall (``SURFACE`` or ``QUEUE``), review reduction
        (share ``COLLAPSED``), tier sizes, ``SURFACE`` precision (the share of
        ``SURFACE`` comments graded 2 or 3), ``SURFACE`` capture (the share of
        consequential comments at ``SURFACE``), outcomes, per-class precision and
        recall, judgment-flag precision (``REFERENCES_SPECIFIC_CLAIM`` also by
        the label's taxonomy version), flag-caused raises, and the IDs of
        consequential comments collapsed.
    """
    rows = list(items)
    n = len(rows)
    tiers = Counter(r.tier for r in rows)
    consequential = [r for r in rows if _consequential(r)]
    missed = sorted(r.comment_id for r in consequential if r.tier == COLLAPSED)
    by_tier = {t: tiers[t] for t in TIERS}
    cons_tier = Counter(r.tier for r in consequential)

    per_class: dict[str, dict[str, int]] = {}
    for name in taxonomy.CLASSES:
        predicted = [r for r in rows if r.outcome == "OK" and r.primary_class == name]
        labeled = [r for r in rows if r.label.get("primary_class") == name]
        agree = sum(1 for r in predicted if r.label.get("primary_class") == name)
        per_class[name] = {"predicted": len(predicted), "labeled": len(labeled), "agree": agree}

    flags: dict[str, dict[str, int]] = {}
    for name in JUDGMENT_FLAGS:
        setting = [r for r in rows if name in r.classifier_flags]
        labeled_with = [r for r in rows if name in r.label.get("flags", [])]
        flags[name] = {
            "set": len(setting),
            "agree": sum(1 for r in setting if name in r.label.get("flags", [])),
            "labeled": len(labeled_with),
        }
    rsc_by_version: dict[str, dict[str, int]] = {}
    for version in sorted({str(r.label.get("taxonomy_version")) for r in rows}):
        sub = [r for r in rows if str(r.label.get("taxonomy_version")) == version]
        setting = [r for r in sub if RSC in r.classifier_flags]
        rsc_by_version[version] = {
            "labels": len(sub),
            "set": len(setting),
            "agree": sum(1 for r in setting if RSC in r.label.get("flags", [])),
            "labeled": sum(1 for r in sub if RSC in r.label.get("flags", [])),
        }

    raised = [r for r in rows if _rank(r.tier) > _rank(r.base_tier)]
    counts: dict[str, Any] = {
        "total": n,
        "outcomes": dict(sorted(Counter(r.outcome for r in rows).items())),
        "by_tier": by_tier,
        "surface_size": by_tier["SURFACE"],
        # Of the comments at SURFACE, how many are graded 2 or 3 (proposed co-primary).
        "surface_precision": _share(cons_tier["SURFACE"], by_tier["SURFACE"]),
        # Of the consequential comments, how many reach SURFACE.
        "surface_capture": _share(cons_tier["SURFACE"], len(consequential)),
        "review_reduction": _share(by_tier[COLLAPSED], n),
        "consequential": len(consequential),
        "consequential_by_tier": {t: cons_tier[t] for t in TIERS},
        "consequential_recall": _share(len(consequential) - len(missed), len(consequential)),
        "consequential_missed": len(missed),
        "per_class": per_class,
        "flag_precision": flags,
        "rsc_by_label_taxonomy": rsc_by_version,
        "flag_caused_raises": {
            "raised": len(raised),
            "graded_0_or_1": sum(1 for r in raised if not _consequential(r)),
        },
    }
    failed = sorted(r.comment_id for r in rows if r.outcome != "OK")
    return Score(counts=counts, missed_ids=missed, failed_ids=failed)


def score_by_post_order(items: Iterable[Scored]) -> dict[str, Score]:
    """Score all items, and the publication-order and shuffled labels apart.

    :param items: The joined records.
    :returns: :func:`score` results under ``all``, ``published``, and ``random``.
    """
    rows = list(items)
    out = {"all": score(rows)}
    for order in label_records.POST_ORDERS:
        out[order] = score(r for r in rows if r.post_order == order)
    return out
