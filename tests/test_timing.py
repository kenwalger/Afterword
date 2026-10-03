from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from afterword import baseline, cli, timing
from tests.conftest import FAKE_KEY
from tests.test_baseline import observations


def write_record(path: Path, **fields: Any) -> None:
    record = {
        "week_start": "2026-09-07",
        "week_end": "2026-09-13",
        "snapshot_run_id": "r1",
        "comments_in_week": 44,
        "comments_reviewed": 44,
        "complete": True,
        "total_seconds": 900.0,
        "seconds_per_comment": 20.5,
        "started_at": "2026-10-03T10:00:00Z",
        "per_comment_seconds": [{"comment_id": "abc1", "seconds": 20.0}],
    } | fields
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")


def seed(root: Path) -> None:
    base = root / timing.TIMING_ROOT
    write_record(base / "chronological-2026-09-07-a.json", valid=True)
    # Saved before the confirmation step existed: no `valid` field.
    write_record(base / "chronological-2026-09-21-b.json", week_start="2026-09-21")
    write_record(base / "chronological-2026-09-14-c.json", valid=False)
    write_record(base / timing.PRACTICE_DIR / "chronological-2026-09-21-d.json", valid=True)
    (base / "broken.json").write_text("{", encoding="utf-8")


def test_only_confirmed_top_level_records_count(tmp_path):
    seed(tmp_path)
    loaded = timing.load_valid(tmp_path)
    assert [r["week_start"] for r in loaded["valid"]] == ["2026-09-07"]
    # Unconfirmed, explicitly invalid, practice (even if marked valid), and unreadable.
    assert loaded["ignored"] == 4
    # Per-comment IDs never leave the records.
    assert "per_comment_seconds" not in loaded["valid"][0]


def test_no_timing_directory_means_nothing_counted(tmp_path):
    assert timing.load_valid(tmp_path) == {"valid": [], "ignored": 0}


def test_record_dir_separates_practice(tmp_path):
    assert timing.record_dir(tmp_path, valid=True) == tmp_path / timing.TIMING_ROOT
    assert timing.record_dir(tmp_path, valid=False).name == timing.PRACTICE_DIR
    assert timing.seconds_per_comment(10.0, 4) == 2.5
    assert timing.seconds_per_comment(10.0, 0) is None


def test_baseline_report_shows_valid_timings_only():
    loaded = {
        "valid": [
            {
                "week_start": "2026-09-07",
                "week_end": "2026-09-13",
                "snapshot_run_id": "r1",
                "comments_in_week": 44,
                "comments_reviewed": 44,
                "complete": True,
                "total_seconds": 900.0,
                "seconds_per_comment": 20.5,
                "started_at": "x",
            }
        ],
        "ignored": 2,
    }
    report = baseline.build(
        observations(), as_of=observations().finished_at.date(), review_timing=loaded
    )
    text = baseline.render_markdown(report)
    assert "## Chronological review time (C-009)" in text
    assert "| 2026-09-07 to 2026-09-13 | 44 of 44 | yes | 900.0 | 20.5 | `r1` |" in text
    assert "Practice or unconfirmed records ignored: 2." in text


def test_baseline_without_timings_says_so():
    report = baseline.build(observations(), as_of=observations().finished_at.date())
    assert "No valid timings recorded yet." in baseline.render_markdown(report)


def test_baseline_command_ignores_practice_records(tmp_path, fake_dev, monkeypatch, capsys):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    assert cli.main(["--root", str(tmp_path), "probe", "--min-interval", "0"]) == 0
    (run_dir,) = (tmp_path / cli.RAW_ROOT).iterdir()
    seed(tmp_path)
    assert cli.main(["--root", str(tmp_path), "baseline", "--run", run_dir.name]) == 0
    assert "valid review timings: 1, practice or unconfirmed ignored: 4" in capsys.readouterr().out
    report = json.loads(
        (tmp_path / cli.REPORT_ROOT / f"baseline-{run_dir.name}.json").read_text(encoding="utf-8")
    )
    assert [r["week_start"] for r in report["review_timing"]["valid"]] == ["2026-09-07"]
    assert "abc1" not in json.dumps(report)


def test_baseline_command_names_a_replacement_week(tmp_path, fake_dev, monkeypatch, capsys):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    assert cli.main(["--root", str(tmp_path), "probe", "--min-interval", "0"]) == 0
    (run_dir,) = (tmp_path / cli.RAW_ROOT).iterdir()
    base = ["--root", str(tmp_path), "baseline", "--run", run_dir.name]
    assert cli.main([*base, "--exclude-week", "not-a-date"]) == 2
    assert cli.main([*base, "--exclude-week", "2026-09-21", "--exclude-week", "2026-09-07"]) == 0
    assert "replacement typical week: " in capsys.readouterr().out
