"""Label records on disk: reading them, progress counts, and which label analysis uses.

Labels and batch records live under ``fixtures/labels/<corpus_version>/``, one
JSONL file per pass plus ``batches.jsonl`` (``fixtures/README.md``). This module
is the one place that counts them, so ``afterword label status``, the terminal
tool's closing line, and the label UI's progress badge agree.

Everything returned here is a count. No comment text, reason, note, or ID
leaves this module, so its results are safe to print. Progress counts carry
no class or grade distribution, so they can be shown while labeling;
:func:`summarize` and :func:`calibration_differences` do carry distributions
and are for analysis, never for a labeling screen.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from afterword import policy, taxonomy

LABEL_ROOT: Path = Path("fixtures/labels")
# Passes, in file order. `calibration` re-labels comments that already have an
# initial label, from scratch with the prior label hidden (LABELING-GUIDE.md).
PASSES: tuple[str, ...] = ("initial", "calibration", "self_agreement")
# Passes whose labels can be the one analysis uses. A self-agreement label is a
# consistency measurement only and never replaces the label it is compared with.
ANALYSIS_PASSES: tuple[str, ...] = ("initial", "calibration")
BATCHES_FILE: str = "batches.jsonl"
# Transports recorded on `batch_start` from session 7 on; earlier batches have none.
TOOLS: tuple[str, ...] = ("terminal", "browser")
UNRECORDED_TOOL: str = "not recorded"
# Post orders a batch can use (`afterword.labeling.POST_ORDERS`), and the key
# for a label whose batch start record is missing.
POST_ORDERS: tuple[str, ...] = ("published", "random")
UNKNOWN_ORDER: str = "unknown"
GRADES: tuple[int, ...] = (0, 1, 2, 3)
# For recall, consequential means grade 2 or 3 (LABELING-GUIDE.md).
CONSEQUENTIAL_FROM: int = 2


def label_dir(root: Path, corpus_version: str) -> Path:
    """Return the directory holding one corpus version's labels.

    :param root: Repository root.
    :param corpus_version: A corpus version already checked as a safe name.
    :returns: ``fixtures/labels/<corpus_version>`` under ``root``.
    """
    return root / LABEL_ROOT / corpus_version


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def read_labels(root: Path, corpus_version: str) -> list[dict[str, Any]]:
    """Read every label of one corpus version, all passes, in pass then file order.

    :param root: Repository root.
    :param corpus_version: A corpus version already checked as a safe name.
    :returns: Label records as written; an empty list when none exist.
    """
    out = label_dir(root, corpus_version)
    return [record for p in PASSES for record in _read_jsonl(out / f"{p}.jsonl")]


def read_batches(root: Path, corpus_version: str) -> list[dict[str, Any]]:
    """Read the batch records of one corpus version.

    :param root: Repository root.
    :param corpus_version: A corpus version already checked as a safe name.
    :returns: Batch start, note, and end records, in file order.
    """
    return _read_jsonl(label_dir(root, corpus_version) / BATCHES_FILE)


def _pass_of(record: dict[str, Any]) -> str:
    return str(record.get("pass", "initial"))


def analysis_labels(labels: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Choose the label analysis uses for each comment.

    The rule (``docs/LABELING-GUIDE.md``): the latest label from a pass other
    than ``self_agreement``, by ``labeled_at``. A calibration label made after
    the initial one therefore replaces it in analysis, while both stay on disk.
    On a tie in time, the later pass in :data:`PASSES` wins, then the later
    record in file order.

    :param labels: Label records from :func:`read_labels`.
    :returns: One record per comment ID.
    """
    chosen: dict[str, tuple[tuple[str, int, int], dict[str, Any]]] = {}
    for position, record in enumerate(labels):
        name = _pass_of(record)
        if name not in ANALYSIS_PASSES:
            continue
        key = (str(record.get("labeled_at", "")), PASSES.index(name), position)
        comment_id = str(record["comment_id"])
        if comment_id not in chosen or key > chosen[comment_id][0]:
            chosen[comment_id] = (key, record)
    return {comment_id: record for comment_id, (_, record) in chosen.items()}


def batch_tools(batches: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Map each batch ID to the transport that wrote it.

    :param batches: Batch records from :func:`read_batches`.
    :returns: ``terminal``, ``browser``, or :data:`UNRECORDED_TOOL` by batch ID.
    """
    tools: dict[str, str] = {}
    for record in batches:
        if record.get("event") == "batch_start":
            tool = record.get("tool")
            tools[str(record.get("batch_id"))] = tool if tool in TOOLS else UNRECORDED_TOOL
    return tools


def batch_post_orders(batches: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Map each batch ID to the post order it labeled in.

    A ``batch_start`` without ``post_order`` predates the option and was
    ``published`` (``fixtures/README.md``).

    :param batches: Batch records from :func:`read_batches`.
    :returns: ``published`` or ``random`` by batch ID.
    """
    return {
        str(record.get("batch_id")): str(record.get("post_order") or "published")
        for record in batches
        if record.get("event") == "batch_start"
    }


def split_by_post_order(
    labels: Iterable[dict[str, Any]], batches: Iterable[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Separate labels made in publication order from labels made in shuffled order.

    Labels in publication order come from the earliest posts first, so they are
    not a random sample of the corpus; shuffled ones come closer to one. Results
    that depend on the sample report the two apart.

    :param labels: Label records.
    :param batches: Batch records from :func:`read_batches`.
    :returns: Labels under :data:`POST_ORDERS` keys, plus :data:`UNKNOWN_ORDER`
        for a label whose batch has no start record.
    """
    orders = batch_post_orders(batches)
    out: dict[str, list[dict[str, Any]]] = {k: [] for k in (*POST_ORDERS, UNKNOWN_ORDER)}
    for record in labels:
        out[orders.get(str(record.get("batch_id")), UNKNOWN_ORDER)].append(record)
    return out


@dataclass(frozen=True)
class LabelProgress:
    """Progress counts for one run: no classes, grades, IDs, or text.

    Only comments eligible in the run count, under the labeling tools' own
    rules (:meth:`afterword.labeling.Snapshot.subjects`).
    """

    eligible: int
    labeled: int
    remaining: int
    relabeled: int
    by_pass: dict[str, int] = field(default_factory=dict)
    by_tool: dict[str, int] = field(default_factory=dict)
    by_post_order: dict[str, int] = field(default_factory=dict)
    not_in_run: int = 0


def progress(
    eligible_ids: set[str],
    labels: Iterable[dict[str, Any]],
    batches: Iterable[dict[str, Any]],
) -> LabelProgress:
    """Count labeling progress the way the labeling tools choose their batches.

    :param eligible_ids: IDs of the comments the tools would label from this run.
    :param labels: Label records from :func:`read_labels`.
    :param batches: Batch records from :func:`read_batches`.
    :returns: ``labeled``: eligible comments with an initial label; ``remaining``:
        eligible comments without one; ``relabeled``: eligible comments with a
        calibration label; label counts by pass, by tool, and by post order
        (``published`` or ``random``); and how many
        labeled comments are not eligible in this run (deleted upstream since,
        for example).
    """
    batch_list = list(batches)
    tools = batch_tools(batch_list)
    orders = batch_post_orders(batch_list)
    by_order: Counter[str] = Counter()
    done: dict[str, set[str]] = {p: set() for p in PASSES}
    by_tool: Counter[str] = Counter()
    outside: set[str] = set()
    for record in labels:
        comment_id = str(record["comment_id"])
        if comment_id not in eligible_ids:
            outside.add(comment_id)
            continue
        name = _pass_of(record)
        if name in done:
            done[name].add(comment_id)
        by_tool[tools.get(str(record.get("batch_id")), UNRECORDED_TOOL)] += 1
        by_order[orders.get(str(record.get("batch_id")), UNKNOWN_ORDER)] += 1
    labeled = len(done["initial"])
    return LabelProgress(
        eligible=len(eligible_ids),
        labeled=labeled,
        remaining=len(eligible_ids) - labeled,
        relabeled=len(done["calibration"]),
        by_pass={p: len(done[p]) for p in PASSES},
        by_tool={t: by_tool[t] for t in (*TOOLS, UNRECORDED_TOOL)},
        by_post_order={o: by_order[o] for o in (*POST_ORDERS, UNKNOWN_ORDER)},
        not_in_run=len(outside),
    )


def _is_consequential(grade: Any) -> bool:
    return isinstance(grade, int) and grade >= CONSEQUENTIAL_FROM


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Return the Wilson score interval for a proportion.

    Reported beside small-sample shares (``EVALUATION.md``: counts first, then a
    percentage with a Wilson interval).

    :param successes: Count of successes.
    :param n: Sample size.
    :param z: Normal quantile; 1.96 gives a 95% interval.
    :returns: Lower and upper bounds as fractions; ``(0.0, 0.0)`` when ``n`` is 0.
    """
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))


def summarize(labels: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Count labels by class and grade, for analysis (never while labeling).

    :param labels: The labels to count, usually :func:`analysis_labels` values.
    :returns: Counts only: totals, classes in precedence order, prospective
        grades, consequential labels, prospective against retrospective
        agreement where both grades exist, and ``replied_before_labeling``.
    """
    records = list(labels)
    classes = Counter(str(r.get("primary_class")) for r in records)
    prospective = Counter(r.get("consequential_prospective") for r in records)
    both = [r for r in records if isinstance(r.get("consequential_retrospective"), int)]
    exact = sum(
        1 for r in both if r["consequential_retrospective"] == r["consequential_prospective"]
    )
    binary = sum(
        1
        for r in both
        if _is_consequential(r["consequential_prospective"])
        == _is_consequential(r["consequential_retrospective"])
    )
    raised = sum(
        1
        for r in both
        if not _is_consequential(r["consequential_prospective"])
        and _is_consequential(r["consequential_retrospective"])
    )
    replied = sum(1 for r in records if r.get("replied_before_labeling") is True)
    return {
        "total": len(records),
        "by_class": {name: classes[name] for name in taxonomy.CLASSES},
        "prospective": {g: prospective[g] for g in GRADES},
        "consequential": sum(
            1 for r in records if _is_consequential(r.get("consequential_prospective"))
        ),
        "with_retrospective": len(both),
        "retrospective_same_grade": exact,
        "retrospective_same_binary": binary,
        "consequential_only_in_hindsight": raised,
        "consequential_only_prospectively": len(both) - binary - raised,
        "replied_before_labeling": replied,
    }


def _labeler_flags(record: dict[str, Any]) -> frozenset[str]:
    return frozenset(f for f in record.get("flags", []) if f not in taxonomy.STRUCTURAL_FLAGS)


def calibration_differences(labels: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Compare each calibration label with the initial label of the same comment.

    :param labels: Label records from :func:`read_labels`.
    :returns: Counts only: comments with both labels, and how many agree on
        class, on prospective grade, on the consequential binary (with the
        direction of each change), and on labeler-chosen flags.
    """
    initial: dict[str, dict[str, Any]] = {}
    calibration: dict[str, dict[str, Any]] = {}
    for record in labels:
        target = {"initial": initial, "calibration": calibration}.get(_pass_of(record))
        if target is not None:
            target[str(record["comment_id"])] = record
    pairs = [(initial[c], calibration[c]) for c in calibration if c in initial]
    became = sum(
        1
        for a, b in pairs
        if not _is_consequential(a.get("consequential_prospective"))
        and _is_consequential(b.get("consequential_prospective"))
    )
    stopped = sum(
        1
        for a, b in pairs
        if _is_consequential(a.get("consequential_prospective"))
        and not _is_consequential(b.get("consequential_prospective"))
    )
    return {
        "compared": len(pairs),
        "same_class": sum(1 for a, b in pairs if a.get("primary_class") == b.get("primary_class")),
        "same_prospective": sum(
            1
            for a, b in pairs
            if a.get("consequential_prospective") == b.get("consequential_prospective")
        ),
        "same_consequential": len(pairs) - became - stopped,
        "became_consequential": became,
        "stopped_being_consequential": stopped,
        "same_labeler_flags": sum(1 for a, b in pairs if _labeler_flags(a) == _labeler_flags(b)),
    }


def class_crosstab(labels: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Cross-tabulate primary class by prospective grade and by class-default tier.

    :param labels: The labels to count, usually :func:`analysis_labels` values.
    :returns: Per class in precedence order: the count at each prospective grade
        (keys ``"0"`` to ``"3"``), the total, and the class's default tier under
        the current policy (``tier``, as a name).
    """
    records = list(labels)
    table: dict[str, dict[str, Any]] = {}
    for name in taxonomy.CLASSES:
        rows = [r for r in records if r.get("primary_class") == name]
        grades = Counter(r.get("consequential_prospective") for r in rows)
        table[name] = {str(g): grades[g] for g in GRADES} | {
            "total": len(rows),
            "tier": policy.CLASS_DEFAULTS[name].name,
        }
    return table


# Taxonomy versions whose REFERENCES_SPECIFIC_CLAIM is not comparable with tax-v0.2's
# stricter test (TAXONOMY.md): tax-v0.1 labels applied it more broadly.
BROAD_RSC_VERSIONS: frozenset[str] = frozenset({"tax-v0.1"})
RSC: str = "REFERENCES_SPECIFIC_CLAIM"
# Which labeled REFERENCES_SPECIFIC_CLAIM flags an oracle ceiling ignores.
RSC_KEEP: str = "keep"
RSC_DROP_BROAD: str = "broad"
RSC_DROP_ALL: str = "all"
# The oracle ceilings, in report order: (name, use labeled flags, RSC handling).
ORACLE_VARIANTS: tuple[tuple[str, bool, str], ...] = (
    ("class_only", False, RSC_KEEP),
    ("class_and_flags", True, RSC_KEEP),
    ("class_and_flags_without_broad_rsc", True, RSC_DROP_BROAD),
    ("class_and_flags_without_rsc", True, RSC_DROP_ALL),
)


def with_content_flags(record: dict[str, Any], content_flags: Iterable[str]) -> dict[str, Any]:
    """Replace a label's code and link flags with the deterministic ones.

    From `tax-v0.2`, analysis uses the code and link flags computed from
    normalization for every label, whatever taxonomy version it was made under
    (``TAXONOMY.md``). The label on disk is not changed.

    :param record: A label record.
    :param content_flags: The comment's flags from
        :func:`afterword.normalize.content_flags`.
    :returns: A copy of the record with ``flags`` updated, in the record's order
        with any added content flag after the structural ``REPLY_TO_AUTHOR``.
    """
    computed = set(content_flags) & taxonomy.CONTENT_FLAGS
    kept = [f for f in record.get("flags", []) if f not in taxonomy.CONTENT_FLAGS]
    head = [f for f in kept if f == taxonomy.REPLY_TO_AUTHOR]
    rest = [f for f in kept if f != taxonomy.REPLY_TO_AUTHOR]
    added = [f for f in taxonomy.FLAGS if f in computed]
    return record | {"flags": head + added + rest}


def _oracle_tier(
    record: dict[str, Any], *, with_flags: bool, rsc: str, policy_version: str
) -> policy.Tier:
    flags = set(record.get("flags", [])) if with_flags else set()
    broad = record.get("taxonomy_version") in BROAD_RSC_VERSIONS
    if rsc == RSC_DROP_ALL or (rsc == RSC_DROP_BROAD and broad):
        flags.discard(RSC)
    decision = policy.assign(
        policy.PolicyInput(
            outcome="OK",
            primary_class=str(record.get("primary_class")),
            flags=frozenset(flags) & frozenset(taxonomy.FLAGS),
            confidence=None,
            edited_since_review=False,
        ),
        policy_version=policy_version,
    )
    return decision.tier


def oracle_ceiling(
    labels: Iterable[dict[str, Any]], *, policy_version: str = policy.POLICY_VERSION
) -> dict[str, dict[str, Any]]:
    """Apply the policy to the labels themselves: what perfect classification would give.

    Four ceilings (:data:`ORACLE_VARIANTS`): ``class_only`` uses the labeled
    class alone (class defaults); ``class_and_flags`` adds the labeled flags, so
    structural and judgment flags raise tiers as policy says;
    ``class_and_flags_without_broad_rsc`` does the same but ignores
    ``REFERENCES_SPECIFIC_CLAIM`` on labels from :data:`BROAD_RSC_VERSIONS`,
    whose use of the flag is not comparable with `tax-v0.2`; and
    ``class_and_flags_without_rsc`` ignores it on every label, so no tier is
    raised by ``REFERENCES_SPECIFIC_CLAIM`` at all.

    :param labels: The labels to score, usually :func:`analysis_labels` values.
    :param policy_version: The policy to apply (:data:`afterword.policy.POLICY_VERSIONS`).
    :returns: Per ceiling: comments by tier, consequential (prospective 2 or 3)
        comments by tier, the collapsed count (review reduction), the
        consequential comments surfaced (``SURFACE`` or ``QUEUE``), and
        ``surface_precision`` as [consequential at ``SURFACE``, all at
        ``SURFACE``]. Counts only.
    """
    records = list(labels)
    out: dict[str, dict[str, Any]] = {}
    for name, with_flags, rsc in ORACLE_VARIANTS:
        tiers: Counter[str] = Counter()
        consequential: Counter[str] = Counter()
        for record in records:
            tier = _oracle_tier(
                record, with_flags=with_flags, rsc=rsc, policy_version=policy_version
            )
            tiers[tier.name] += 1
            if _is_consequential(record.get("consequential_prospective")):
                consequential[tier.name] += 1
        names = [t.name for t in sorted(policy.Tier, reverse=True)]
        out[name] = {
            "total": len(records),
            "by_tier": {t: tiers[t] for t in names},
            "consequential_by_tier": {t: consequential[t] for t in names},
            "collapsed": tiers[policy.Tier.COLLAPSED.name],
            "consequential": sum(consequential.values()),
            "consequential_surfaced": sum(consequential.values())
            - consequential[policy.Tier.COLLAPSED.name],
            "surface_precision": [
                consequential[policy.Tier.SURFACE.name],
                tiers[policy.Tier.SURFACE.name],
            ],
        }
    return out


def summarize_by_post_order(
    labels: Iterable[dict[str, Any]], batches: Iterable[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Summarize labels in publication order and in shuffled order separately, and together.

    :param labels: The labels to count, usually :func:`analysis_labels` values.
    :param batches: Batch records from :func:`read_batches`.
    :returns: :func:`summarize` output under ``published``, ``random``, and
        ``all`` (plus ``unknown`` when some label's batch has no start record).
    """
    records = list(labels)
    split = split_by_post_order(records, batches)
    out = {order: summarize(split[order]) for order in POST_ORDERS}
    if split[UNKNOWN_ORDER]:
        out[UNKNOWN_ORDER] = summarize(split[UNKNOWN_ORDER])
    out["all"] = summarize(records)
    return out
