from __future__ import annotations

from datetime import UTC, date, datetime

from afterword import baseline
from afterword.observations import ObservedComment, ObservedContent, RunObservations


def ts(day: str) -> datetime:
    return datetime.fromisoformat(f"{day}T12:00:00+00:00")


def comment(ref: str, cid: str, day: str | None, author: bool = False) -> ObservedComment:
    return ObservedComment(ref, cid, None, 0, ts(day) if day else None, author)


def observations() -> RunObservations:
    contents = [
        ObservedContent("a", ts("2026-08-03"), 4),
        ObservedContent("b", ts("2026-08-17"), 1),
        ObservedContent("c", ts("2026-09-07"), 0),
    ]
    comments = [
        comment("a", "1", "2026-08-03"),  # week of 08-03
        comment("a", "2", "2026-08-04", author=True),
        comment("a", "3", "2026-08-12"),  # week of 08-10
        comment("a", "4", "2026-08-05"),  # week of 08-03
        comment("b", "5", "2026-08-18"),  # week of 08-17
        comment("b", "6", None),
    ]
    return RunObservations("r1", "all", datetime(2026, 9, 10, tzinfo=UTC), contents, comments)


def test_totals_separate_author_comments():
    t = baseline.build(observations(), as_of=date(2026, 9, 10))["totals"]
    assert t["articles"] == 3
    assert t["comments"] == 6
    assert t["comments_from_others"] == 5
    assert t["comments_by_author"] == 1
    assert t["undated_comments"] == 1
    assert t["articles_with_comments_from_others"] == 2


def test_per_article_distribution_includes_zero_comment_articles():
    pa = baseline.build(observations(), as_of=date(2026, 9, 10))["per_article_from_others"]
    assert pa["n"] == 3
    assert pa["min"] == 0
    assert pa["max"] == 3
    assert pa["histogram"]["0"] == 1
    assert pa["histogram"]["2-5"] == 2  # a: 3, b: 2 (one undated still counts per article)


def test_weekly_series_is_contiguous_and_includes_zero_weeks():
    report = baseline.build(observations(), as_of=date(2026, 9, 10))
    weeks = [(w["week_start"], w["others"], w["mine"], w["complete"]) for w in report["weekly"]]
    assert weeks == [
        ("2026-08-03", 2, 1, True),
        ("2026-08-10", 1, 0, True),
        ("2026-08-17", 1, 0, True),
        ("2026-08-24", 0, 0, True),
        ("2026-08-31", 0, 0, True),
        ("2026-09-07", 0, 0, False),  # contains as_of (a Thursday)
    ]


def test_partial_week_is_excluded_from_statistics():
    pw = baseline.build(observations(), as_of=date(2026, 9, 10))["per_week_from_others"]
    assert pw["all_weeks"]["n"] == 5
    # A Monday as_of completes the previous week and starts a new partial one.
    pw = baseline.build(observations(), as_of=date(2026, 9, 14))["per_week_from_others"]
    assert pw["all_weeks"]["n"] == 6


def test_median_and_p90_weeks_prefer_most_recent_on_ties():
    wt = baseline.build(observations(), as_of=date(2026, 9, 10))["weeks_to_time"]
    trailing_52, trailing_13 = wt
    assert trailing_52["basis"].startswith("trailing 5 complete weeks")
    # Complete weekly counts [2, 1, 1, 0, 0]: median 1 (two candidates), p90 2.
    assert trailing_52["median_week"]["week_start"] == "2026-08-17"
    assert trailing_52["p90_week"] == {
        "week_start": "2026-08-03",
        "week_end": "2026-08-09",
        "comments_from_others": 2,
    }
    assert trailing_13 == trailing_52 | {"basis": trailing_13["basis"]}


def test_recent_window_is_thirteen_complete_weeks():
    obs = observations()
    obs.contents.insert(0, ObservedContent("old", ts("2025-01-06"), 0))
    pw = baseline.build(obs, as_of=date(2026, 9, 10))["per_week_from_others"]
    assert pw["trailing_13_weeks"]["n"] == 13
    assert pw["trailing_52_weeks"]["n"] == 52


def test_deletion_placeholders_are_excluded_and_reported_separately():
    obs = observations()
    obs.comments.append(
        ObservedComment("a", "p1", None, 0, ts("2026-08-04"), False, is_deletion_placeholder=True)
    )
    report = baseline.build(obs, as_of=date(2026, 9, 10))
    assert report["totals"]["comments_from_others"] == 5
    assert report["totals"]["deletion_placeholders"] == 1
    assert report["weekly"][0]["others"] == 2


def test_concentration_shares_and_thresholds():
    c = baseline.concentration([0, 0, 10, 5, 3, 2, 0])
    assert c["top_articles"][0] == {"top": 1, "comments": 10, "share": 0.5}
    assert c["top_articles"][1] == {"top": 3, "comments": 18, "share": 0.9}
    assert c["articles_to_reach_50pct"] == 1
    assert c["articles_to_reach_80pct"] == 3
    assert c["articles_with_zero"] == 3
    assert c["articles_with_at_least"] == {"1": 4, "5": 2, "10": 1, "20": 0}
    assert c["nonzero_counts_desc"] == [10, 5, 3, 2]


def test_nearest_rank_percentile():
    assert baseline.nearest_rank([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.9) == 9
    assert baseline.nearest_rank([7], 0.9) == 7


def test_markdown_has_no_identifiers_beyond_refs():
    md = baseline.render_markdown(baseline.build(observations(), as_of=date(2026, 9, 10)))
    assert "Median week" in md
    assert "p90 week" in md
    assert chr(0x2014) not in md  # no em-dashes in generated prose


def test_calendar_months_bucket_by_comment_month():
    report = baseline.build(observations(), as_of=date(2026, 9, 10))
    assert report["monthly"] == [
        {"month": "2026-08", "others": 4, "mine": 1, "complete": True},
        {"month": "2026-09", "others": 0, "mine": 0, "complete": False},
    ]


def test_calendar_months_split_a_week_that_crosses_months():
    # The week of 2026-08-31 starts in August but this comment is in September.
    obs = observations()
    obs.comments.append(comment("b", "7", "2026-09-02"))
    months = {
        m["month"]: m["others"] for m in baseline.build(obs, as_of=date(2026, 9, 10))["monthly"]
    }
    assert months == {"2026-08": 4, "2026-09": 1}


def test_post_age_at_comment():
    ages = baseline.build(observations(), as_of=date(2026, 9, 10))[
        "post_age_at_comment_from_others"
    ]
    # a published 08-03: comments on 08-03, 08-12, 08-05 -> 0, 9, 2 days; b published 08-17: 1 day.
    assert ages["all"] == {"0-7": 3, "8-30": 1, "31-90": 0, "91-365": 0, "366+": 0}
