"""Volume baseline for C-009, computed from source-neutral observations.

Outputs aggregates only: counts, distributions, and week start dates. No
comment text, commenter identity, or titles are read or written here.
Comments by the content author are counted separately and excluded from the
triage-relevant figures (ADR-011).
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Any

from afterword.observations import RunObservations

HISTOGRAM_BUCKETS: tuple[tuple[int, int | None], ...] = (
    (0, 0),
    (1, 1),
    (2, 5),
    (6, 10),
    (11, 20),
    (21, 50),
    (51, None),
)
TRAILING_WEEKS: int = 52
RECENT_WEEKS: int = 13
POST_AGE_BUCKETS: tuple[tuple[int, int | None], ...] = (
    (0, 7),
    (8, 30),
    (31, 90),
    (91, 365),
    (366, None),
)


def describe(values: list[int]) -> dict[str, Any]:
    """Summarize a list of counts.

    :param values: Counts, in any order.
    :returns: ``n``, min, median, mean, nearest-rank p90, max, and total; only ``n`` when empty.
    """
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "min": ordered[0],
        "median": statistics.median(ordered),
        "mean": round(statistics.fmean(ordered), 2),
        "p90": nearest_rank(ordered, 0.9),
        "max": ordered[-1],
        "total": sum(ordered),
    }


def nearest_rank(ordered: list[int], q: float) -> int:
    """Return the nearest-rank percentile.

    :param ordered: Values sorted ascending, not empty.
    :param q: Quantile between 0 and 1.
    :returns: The value at that rank.
    """
    return ordered[max(math.ceil(q * len(ordered)) - 1, 0)]


def week_start(moment: datetime | date) -> date:
    """Return the Monday that starts the ISO week containing ``moment`` (UTC).

    :param moment: A timezone-aware datetime, or a date.
    :returns: The week's Monday.
    """
    day = moment.astimezone(UTC).date() if isinstance(moment, datetime) else moment
    return day - timedelta(days=day.weekday())


def _bucket_label(lo: int, hi: int | None) -> str:
    if hi is None:
        return f"{lo}+"
    return str(lo) if lo == hi else f"{lo}-{hi}"


def histogram(values: list[int]) -> dict[str, int]:
    """Count values into the fixed per-article buckets.

    :param values: Counts per article.
    :returns: Number of articles per bucket label.
    """
    out = {}
    for lo, hi in HISTOGRAM_BUCKETS:
        out[_bucket_label(lo, hi)] = sum(1 for v in values if v >= lo and (hi is None or v <= hi))
    return out


def pick_week(weeks: list[tuple[date, int]], target: float) -> dict[str, Any] | None:
    """Find the week whose count is closest to ``target``; ties go to the most recent.

    :param weeks: Week starts with their counts, oldest first.
    :param target: Count to approach, such as the median.
    :returns: The chosen week's start, end, and count, or ``None`` if there are no weeks.
    """
    if not weeks:
        return None
    start, count = min(reversed(weeks), key=lambda w: abs(w[1] - target))
    return {
        "week_start": start.isoformat(),
        "week_end": (start + timedelta(days=6)).isoformat(),
        "comments_from_others": count,
    }


def calendar_months(
    others: list[datetime], mine: list[datetime], as_of: date
) -> list[dict[str, Any]]:
    """Count comments per calendar month (UTC), from the first comment's month to ``as_of``.

    :param others: Creation times of comments from others.
    :param mine: Creation times of the author's comments.
    :param as_of: Date the run finished; its month is marked partial.
    :returns: One row per month, including empty months.
    """
    if not others and not mine:
        return []
    by_others = Counter(t.astimezone(UTC).strftime("%Y-%m") for t in others)
    by_mine = Counter(t.astimezone(UTC).strftime("%Y-%m") for t in mine)
    first = min(others + mine).astimezone(UTC).date().replace(day=1)
    last = as_of.replace(day=1)
    months = []
    current = first
    while current <= last:
        key = current.strftime("%Y-%m")
        months.append(
            {
                "month": key,
                "others": by_others.get(key, 0),
                "mine": by_mine.get(key, 0),
                "complete": (current.replace(day=28) + timedelta(days=4)).replace(day=1) <= as_of,
            }
        )
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months


def post_age_at_comment(ages_days: list[int]) -> dict[str, int]:
    """Bucket how old the post was when each comment arrived, in whole days.

    :param ages_days: Post age at each comment.
    :returns: Number of comments per age bucket.
    """
    return {
        _bucket_label(lo, hi): sum(1 for a in ages_days if a >= lo and (hi is None or a <= hi))
        for lo, hi in POST_AGE_BUCKETS
    }


def concentration(per_article_counts: list[int]) -> dict[str, Any]:
    """Describe how comments from others are spread across articles. Counts only, no IDs.

    :param per_article_counts: Comments from others per article, zeros included.
    :returns: Top-k shares, articles needed for 50% and 80%, and threshold counts.
    """
    ordered = sorted(per_article_counts, reverse=True)
    total = sum(ordered)

    def articles_to_reach(fraction: float) -> int | None:
        running = 0
        for i, n in enumerate(ordered, start=1):
            running += n
            if total and running >= fraction * total:
                return i
        return None

    return {
        "top_articles": [
            {
                "top": k,
                "comments": sum(ordered[:k]),
                "share": round(sum(ordered[:k]) / total, 3) if total else 0.0,
            }
            for k in (1, 3, 5, 10, 20)
        ],
        "articles_to_reach_50pct": articles_to_reach(0.5),
        "articles_to_reach_80pct": articles_to_reach(0.8),
        "articles_with_zero": sum(1 for n in ordered if n == 0),
        "articles_with_at_least": {
            str(k): sum(1 for n in ordered if n >= k) for k in (1, 5, 10, 20)
        },
        "nonzero_counts_desc": [n for n in ordered if n > 0],
    }


def build(obs: RunObservations, *, as_of: date) -> dict[str, Any]:
    """Compute the C-009 volume baseline.

    :param obs: Observations from one full-scope run.
    :param as_of: Date the run finished. Weeks and months that contain it are partial.
    :returns: The report as JSON-ready data. Aggregates only.
    """
    # Deletion placeholders hold a thread position but are no one's comment.
    placeholders = [c for c in obs.comments if c.is_deletion_placeholder]
    live = [c for c in obs.comments if not c.is_deletion_placeholder]
    others = [c for c in live if not c.is_content_author]
    mine = [c for c in live if c.is_content_author]

    per_article = Counter(c.content_ref for c in others)
    per_article_counts = [per_article.get(c.content_ref, 0) for c in obs.contents]
    reported_total = sum(c.reported_comment_count or 0 for c in obs.contents)

    published = {c.content_ref: c.published_at for c in obs.contents}
    recent_start = week_start(as_of) - timedelta(weeks=RECENT_WEEKS)

    def ages(comments: list[Any]) -> list[int]:
        return [
            max((c.created_at - published[c.content_ref]).days, 0)
            for c in comments
            if c.created_at and published.get(c.content_ref)
        ]

    recent_others = [
        c
        for c in others
        if c.created_at and recent_start <= week_start(c.created_at) < week_start(as_of)
    ]
    dated_others = [c.created_at for c in others if c.created_at]
    dated_mine = [c.created_at for c in mine if c.created_at]
    anchors = [c.published_at for c in obs.contents if c.published_at] + dated_others + dated_mine
    weekly: list[dict[str, Any]] = []
    if anchors:
        first = week_start(min(anchors))
        last = week_start(as_of)
        by_week_others = Counter(week_start(t) for t in dated_others)
        by_week_mine = Counter(week_start(t) for t in dated_mine)
        current = first
        while current <= last:
            weekly.append(
                {
                    "week_start": current,
                    "others": by_week_others.get(current, 0),
                    "mine": by_week_mine.get(current, 0),
                }
            )
            current += timedelta(days=7)

    # A week counts toward statistics only once it has ended; the week containing
    # `as_of` is still listed in the table but would bias every statistic low.
    for w in weekly:
        w["complete"] = w["week_start"] + timedelta(days=7) <= as_of
    all_weeks = [(w["week_start"], w["others"]) for w in weekly if w["complete"]]
    trailing = all_weeks[-TRAILING_WEEKS:]
    trailing_counts = [n for _, n in trailing]
    trailing_desc = describe(trailing_counts)
    non_empty = [n for n in trailing_counts if n > 0]
    recent = all_weeks[-RECENT_WEEKS:]
    recent_desc = describe([n for _, n in recent])

    return {
        "run_id": obs.run_id,
        "scope": obs.scope,
        "as_of": as_of.isoformat(),
        "totals": {
            "articles": len(obs.contents),
            "articles_with_comments_from_others": sum(1 for n in per_article_counts if n > 0),
            "comments": len(obs.comments),
            "comments_from_others": len(others),
            "comments_by_author": len(mine),
            "deletion_placeholders": len(placeholders),
            "reported_comment_count_sum": reported_total,
            "undated_comments": len(live) - len(dated_others) - len(dated_mine),
        },
        "per_article_from_others": {
            **describe(per_article_counts),
            "histogram": histogram(per_article_counts),
            "concentration": concentration(per_article_counts),
        },
        "per_week_from_others": {
            "all_weeks": describe([n for _, n in all_weeks]),
            "trailing_52_weeks": trailing_desc,
            "trailing_13_weeks": recent_desc,
            "trailing_non_empty_weeks": len(non_empty),
            "trailing_median_of_non_empty_weeks": statistics.median(non_empty) if non_empty else 0,
        },
        "weeks_to_time": [
            {
                "basis": f"trailing {len(window)} complete weeks before {as_of.isoformat()}",
                "median_week": pick_week(window, desc.get("median", 0)),
                "p90_week": pick_week(window, desc.get("p90", 0)),
            }
            for window, desc in ((trailing, trailing_desc), (recent, recent_desc))
        ],
        "weekly": [{**w, "week_start": w["week_start"].isoformat()} for w in weekly],
        "monthly": calendar_months(dated_others, dated_mine, as_of),
        "post_age_at_comment_from_others": {
            "all": post_age_at_comment(ages(others)),
            f"trailing_{RECENT_WEEKS}_weeks": post_age_at_comment(ages(recent_others)),
        },
    }


def _stats_row(label: str, d: dict[str, Any]) -> str:
    if not d.get("n"):
        return f"| {label} | 0 | | | | | | |"
    return (
        f"| {label} | {d['n']} | {d['total']} | {d['min']} | {d['median']} | "
        f"{d['mean']} | {d['p90']} | {d['max']} |"
    )


def render_markdown(report: dict[str, Any]) -> str:
    """Render the baseline report as Markdown.

    :param report: Output of :func:`build`.
    :returns: Markdown text, aggregates only.
    """
    t = report["totals"]
    pa = report["per_article_from_others"]
    pw = report["per_week_from_others"]
    wt = report["weeks_to_time"]
    age_recent = report["post_age_at_comment_from_others"][f"trailing_{RECENT_WEEKS}_weeks"]
    lines = [
        "# Volume baseline (C-009)",
        "",
        f"Run: `{report['run_id']}` (scope `{report['scope']}`), as of {report['as_of']}.",
        "Aggregates only. Weeks are ISO weeks (Monday start, UTC), bucketed by comment",
        '`created_at`. "From others" excludes comments by the content author (ADR-011).',
        "",
        "## Totals",
        "",
        "| Measure | Count |",
        "| --- | --- |",
        f"| Articles | {t['articles']} |",
        f"| Articles with comments from others | {t['articles_with_comments_from_others']} |",
        f"| Comment nodes returned (all) | {t['comments']} |",
        f"| Comments from others | {t['comments_from_others']} |",
        f"| Comments by the author | {t['comments_by_author']} |",
        f"| Deletion placeholders (excluded above) | {t['deletion_placeholders']} |",
        f"| Sum of reported `comments_count` | {t['reported_comment_count_sum']} |",
        f"| Comments without a usable timestamp | {t['undated_comments']} |",
        "",
        "## Distributions (comments from others)",
        "",
        "| Unit | n | total | min | median | mean | p90 | max |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        _stats_row("Per article", pa),
        _stats_row("Per week, all history", pw["all_weeks"]),
        _stats_row("Per week, trailing 52", pw["trailing_52_weeks"]),
        _stats_row("Per week, trailing 13", pw["trailing_13_weeks"]),
        "",
        "Weekly statistics use complete weeks only; the week containing the as-of date is",
        "listed in the tables but marked partial.",
        "",
        f"Trailing weeks with at least one comment from others: {pw['trailing_non_empty_weeks']}."
        f" Median among those weeks: {pw['trailing_median_of_non_empty_weeks']}.",
        "",
        "### Comments from others per article",
        "",
        "| Comments | Articles |",
        "| --- | --- |",
        *[f"| {k} | {v} |" for k, v in pa["histogram"].items()],
        "",
        "### Concentration across articles",
        "",
        "| Top articles | Comments from others | Share |",
        "| --- | --- | --- |",
        *[
            f"| {row['top']} | {row['comments']} | {row['share']:.1%} |"
            for row in pa["concentration"]["top_articles"]
        ],
        "",
        f"Articles needed to reach 50% of comments from others: "
        f"{pa['concentration']['articles_to_reach_50pct']}; 80%: "
        f"{pa['concentration']['articles_to_reach_80pct']}. "
        f"Articles with none: {pa['concentration']['articles_with_zero']}.",
        "",
        "Non-zero per-article counts, descending: "
        + ", ".join(str(n) for n in pa["concentration"]["nonzero_counts_desc"])
        + ".",
        "",
        "## Weeks to time (C-009, manual)",
        "",
        "The p90 value uses nearest rank. Ties go to the most recent week.",
    ]
    for basis in wt:
        lines += ["", f"Basis: {basis['basis']}.", ""]
        for label in ("median_week", "p90_week"):
            week = basis[label]
            name = "Median week" if label == "median_week" else "p90 week"
            if week:
                lines.append(
                    f"- **{name}:** {week['week_start']} to {week['week_end']}, "
                    f"{week['comments_from_others']} comments from others."
                )
            else:
                lines.append(f"- **{name}:** none (no complete weeks).")
    lines += [
        "",
        "## Per calendar month",
        "",
        "Bucketed by each comment's own `created_at` month (UTC).",
        "",
        "| Month | From others | By author |",
        "| --- | --- | --- |",
        *[
            f"| {m['month']}{'' if m['complete'] else ' (partial)'} | {m['others']} | {m['mine']} |"
            for m in report["monthly"]
        ],
        "",
        "## Post age when comments from others arrived (days)",
        "",
        "| Post age | All history | Trailing 13 complete weeks |",
        "| --- | --- | --- |",
        *[
            f"| {k} | {v} | {age_recent[k]} |"
            for k, v in report["post_age_at_comment_from_others"]["all"].items()
        ],
        "",
        "## Per week",
        "",
        "| Week start | From others | By author |",
        "| --- | --- | --- |",
        *[
            f"| {w['week_start']}{'' if w['complete'] else ' (partial)'} | {w['others']} "
            f"| {w['mine']} |"
            for w in report["weekly"]
        ],
        "",
    ]
    return "\n".join(lines)
