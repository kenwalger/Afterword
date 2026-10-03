from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from afterword import cli, labeling, taxonomy, timing
from afterword.adapters.dev import records
from afterword.adapters.dev.client import DevClient
from afterword.adapters.dev.probe import Probe
from afterword.observations import ObservedComment, ObservedContent, RunObservations
from tests.conftest import FAKE_KEY, FakeDev, load

REPO = Path(__file__).resolve().parents[1]
NAMES = ("Synthetic Reader One", "synthetic_reader_1", "synthetic_reader_2", "Synthetic Author")
NOW = datetime(2026, 10, 9, 18, 0, tzinfo=UTC)


class Script:
    """A scripted terminal: answers in order, then end of input."""

    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []
        self.out: list[str] = []

    def read(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.answers:
            raise EOFError
        return self.answers.pop(0)

    def write(self, text: str) -> None:
        self.out.append(text)

    @property
    def console(self) -> labeling.Console:
        return labeling.Console(self.read, self.write)

    @property
    def text(self) -> str:
        return "\n".join(self.out + self.prompts)


def ticker(step: float = 1.5) -> Iterator[float]:
    t = 0.0
    while True:
        yield t
        t += step


def make_run(root: Path, *, run_id: str = "r1", finished: datetime | None = None) -> Path:
    client = DevClient(FAKE_KEY, min_interval=0.0, sleep=lambda s: None)
    raw = root / cli.RAW_ROOT / run_id
    probe = Probe(
        client,
        raw,
        root / cli.REPORT_ROOT / "probe" / run_id,
        run_id=run_id,
        page_size=2,
        now=(lambda: finished) if finished else (lambda: datetime.now(UTC)),
    )
    probe.run()
    return raw


def snapshot(root: Path) -> labeling.Snapshot:
    return labeling.Snapshot(records.load_run(make_run(root), include_text=True))


def ids(comments: list[ObservedComment]) -> list[str]:
    return [c.source_object_id for c in comments]


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def label_answers(cls: str = "3", flags: str = "4", pro: str = "2", retro: str = "3") -> list[str]:
    return [cls, flags, pro, retro, "needs an answer", "", ""]


# Thread context -----------------------------------------------------------------


def test_subjects_exclude_author_comments_and_follow_post_then_time(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    assert ids(snap.subjects()) == ["s1a1", "s1b1", "s1a3", "4821"]
    assert snap.excluded_counts()["by_author"] == 1


def test_context_hides_later_replies_including_the_authors(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    first, later = snap.by_id["s1a1"], snap.by_id["s1a3"]
    assert ids(snap.as_of(first)) == ["s1a1"]
    assert snap.hidden_later(first) == 2
    # The author's reply predates s1a3, so it is shown.
    assert ids(snap.as_of(later)) == ["s1a1", "s1a2", "s1a3"]
    assert snap.hidden_later(later) == 0


def test_render_shows_pseudonyms_never_names(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    text = labeling.render(snap, snap.by_id["s1a3"], position="1 of 1", full_thread=False)
    assert "Post: Synthetic article one" in text
    assert text.count("Commenter A") == 2  # same commenter, same pseudonym
    assert "You (author)" in text
    assert "Synthetic follow-up with `inline code`." in text
    assert "<-- THIS COMMENT" in text
    for name in NAMES:
        assert name not in text
    early = labeling.render(snap, snap.by_id["s1a1"], position="1 of 1", full_thread=True)
    assert "Synthetic reply from the author" not in early
    assert "2 later hidden" in early


def test_reply_to_author_is_structural(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    assert snap.reply_to_author(snap.by_id["s1a3"])
    assert not snap.reply_to_author(snap.by_id["s1a1"])


def test_placeholders_are_skipped_and_mark_context_incomplete(tmp_path, fake_dev: FakeDev):
    fake_dev.comments[9000003] = load("comments-with-deletion-placeholder.json")
    snap = snapshot(tmp_path)
    assert "s9p1" not in ids(snap.subjects())
    reply = snap.by_id["s9p2"]
    assert reply in snap.subjects()
    assert snap.excluded_counts()["deletion_placeholders"] == 1
    assert not snap.context_reconstructed(reply)
    assert not snap.reply_to_author(reply)  # authorship unknown from a placeholder
    text = labeling.render(snap, reply, position="1 of 1", full_thread=False)
    assert "[deleted comment]" in text
    assert "[deleted]" not in text  # the placeholder body is never shown
    assert "earlier comment in this thread was deleted" in text


def at(day: str) -> datetime:
    return datetime.fromisoformat(f"{day}T12:00:00+00:00")


def test_post_edited_after_the_comment_marks_context_incomplete():
    def snap_with(edited: datetime | None) -> labeling.Snapshot:
        content = ObservedContent("p", at("2026-08-01"), 1, title="T", edited_at=edited)
        comment = ObservedComment("p", "c1", None, 0, at("2026-08-03"), False, author_ref="9")
        return labeling.Snapshot(RunObservations("r", "all", None, [content], [comment]))

    for edited, expected in ((None, True), (at("2026-08-02"), True), (at("2026-08-04"), False)):
        snap = snap_with(edited)
        assert snap.context_reconstructed(snap.by_id["c1"]) is expected


def test_unexpected_shapes_are_not_labeled():
    content = ObservedContent("p", at("2026-08-01"), 1)
    odd = ObservedComment("p", "c1", None, 0, at("2026-08-03"), False, is_unexpected_shape=True)
    snap = labeling.Snapshot(RunObservations("r", "all", None, [content], [odd]))
    assert snap.subjects() == []
    assert snap.excluded_counts()["unexpected_shapes"] == 1


# Labeling sessions ----------------------------------------------------------------


def run(snap: labeling.Snapshot, root: Path, script: Script, **kwargs: Any) -> int:
    clock = ticker()
    return labeling.run_labeling(
        snap, script.console, root=root, now=lambda: NOW, monotonic=lambda: next(clock), **kwargs
    )


def test_labels_are_recorded_per_schema(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script([*label_answers(), "s", "q"])
    assert run(snap, tmp_path, script) == 1

    out = tmp_path / labeling.LABEL_ROOT / "unfrozen"
    (label,) = lines(out / "initial.jsonl")
    assert label == {
        "label_id": "l_s1a1_initial",
        "comment_id": "s1a1",
        "snapshot_run_id": "r1",
        "corpus_version": "unfrozen",
        "corpus_set": "dev",
        "label_guide_version": "lg-v0.2",
        "taxonomy_version": "tax-v0.1",
        "normalization_version": "display-v0.1",
        "primary_class": "TECHNICAL_QUESTION",
        "flags": ["REFERENCES_SPECIFIC_CLAIM"],
        "consequential_prospective": 2,
        "consequential_retrospective": 3,
        "consequential_retrospective_state": "PRESENT",
        "context_reconstructed": True,
        "replied_before_labeling": True,
        "reason": "needs an answer",
        "pass": "initial",
        "batch_id": "b_20261009T180000Z",
        "duration_seconds": 1.5,
        "labeled_at": "2026-10-09T18:00:00Z",
    }
    start, end = lines(out / "batches.jsonl")
    assert start["event"] == "batch_start"
    assert start["planned"] == 4
    assert start["started_at"] == "2026-10-09T18:00:00Z"
    assert end == {
        "event": "batch_end",
        "batch_id": "b_20261009T180000Z",
        "ended_at": "2026-10-09T18:00:00Z",
        "labeled": 1,
        "skipped": 1,
        "ended_by": "quit",
    }


def test_retrospective_prompt_comes_only_after_the_prospective_grade(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(label_answers())
    run(snap, tmp_path, script)
    prospective = next(i for i, p in enumerate(script.prompts) if p.startswith("Prospective"))
    retrospective = next(i for i, p in enumerate(script.prompts) if p.startswith("Retrospective"))
    assert prospective < retrospective


def test_reason_is_required_for_consequential_grades(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["1", "", "3", "", "", "", "short reason", "", ""])
    run(snap, tmp_path, script)
    reasons = [p for p in script.prompts if p.startswith("Reason")]
    assert len(reasons) == 3
    (label,) = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert label["reason"] == "short reason"
    assert label["consequential_retrospective"] is None
    assert label["consequential_retrospective_state"] == "UNKNOWN"


def test_invalid_answers_are_asked_again(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["11", "x", "8", "9", "", "4", "0", "", "", "", ""])
    run(snap, tmp_path, script)
    (label,) = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert label["primary_class"] == "LIGHTWEIGHT_ACKNOWLEDGMENT"
    assert label["consequential_prospective"] == 0
    assert script.text.count("Not understood") == 4


def test_redo_restarts_the_label(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    answers = ["7", "", "1", "", "", "", "r", *label_answers(cls="1")]
    script = Script(answers)
    run(snap, tmp_path, script)
    (label,) = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert label["primary_class"] == "CORRECTION"


def test_help_lists_every_class_and_flag_with_a_definition(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["h", "1", "h", "4", "2", "3", "needs an answer", "", ""])
    run(snap, tmp_path, script)
    helps = [o for o in script.out if o == taxonomy.help_text()]
    assert len(helps) == 2  # once at the class prompt, once at the flags prompt
    for name in (*taxonomy.CLASSES, *taxonomy.FLAGS):
        assert name in helps[0]
    assert taxonomy.CLASS_DEFINITIONS["CORRECTION"] in helps[0]
    assert "h = help" in script.prompts[0]
    (label,) = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")
    assert label["primary_class"] == "CORRECTION"
    assert label["flags"] == ["REFERENCES_SPECIFIC_CLAIM"]
    assert "Not understood" not in script.text


def test_toggle_shows_the_thread_again(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["t", "q"])
    run(snap, tmp_path, script)
    assert sum("THIS COMMENT" in o for o in script.out) == 2


def test_resume_continues_with_the_next_unlabeled_comment(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    run(snap, tmp_path, Script([*label_answers(), "s", "q"]))  # s1a1 labeled, s1b1 skipped
    run(snap, tmp_path, Script([*label_answers(cls="8", pro="0", retro=""), "q"]))
    out = tmp_path / labeling.LABEL_ROOT / "unfrozen"
    assert [r["comment_id"] for r in lines(out / "initial.jsonl")] == ["s1a1", "s1b1"]
    batch_ids = {e["batch_id"] for e in lines(out / "batches.jsonl")}
    assert len(batch_ids) == 1  # same fixed clock; real batches differ by start time


def test_hard_to_label_notes_go_to_the_batch_record(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    run(snap, tmp_path, Script(["7", "", "1", "", "", "ambiguous", ""]))
    events = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "batches.jsonl")
    assert {"event": "note", "batch_id": "b_20261009T180000Z", "comment_id": "s1a1",
            "note": "ambiguous"} in events  # fmt: skip
    label = lines(tmp_path / labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl")[0]
    assert "note" not in label


def test_batch_size_is_capped_and_ids_restrict_the_queue(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    with pytest.raises(ValueError):
        run(snap, tmp_path, Script([]), batch_size=41)
    script = Script([*label_answers(), "q"])
    run(snap, tmp_path, script, only_ids={"s1a3"}, pass_name="self_agreement")
    out = tmp_path / labeling.LABEL_ROOT / "unfrozen"
    (label,) = lines(out / "self_agreement.jsonl")
    assert label["comment_id"] == "s1a3"
    assert label["flags"] == ["REPLY_TO_AUTHOR", "REFERENCES_SPECIFIC_CLAIM"]
    assert "REPLY_TO_AUTHOR is set automatically" in script.text


def test_unsafe_names_are_refused(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    for name in ("../escape", "a/b", "", ".hidden"):
        with pytest.raises(ValueError):
            run(snap, tmp_path, Script([]), corpus_version=name)


# Chronological timing -------------------------------------------------------------


def test_chronological_mode_times_one_week_in_order(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["", "", "", "y"])
    clock = ticker(2.0)
    out = labeling.run_chronological(
        snap,
        script.console,
        root=tmp_path,
        week=date(2026, 8, 5),  # a Wednesday: the week starts on 2026-08-03
        now=lambda: NOW,
        monotonic=lambda: next(clock),
    )
    assert out is not None
    assert out.parent == tmp_path / labeling.TIMING_ROOT
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["week_start"] == "2026-08-03"
    assert record["week_end"] == "2026-08-09"
    assert record["comments_in_week"] == 2
    assert record["complete"] is True
    assert [c["comment_id"] for c in record["per_comment_seconds"]] == ["s1a1", "s1b1"]
    assert [c["seconds"] for c in record["per_comment_seconds"]] == [2.0, 2.0]
    assert record["total_seconds"] == 10.0  # includes the start prompt
    assert record["seconds_per_comment"] == 5.0
    assert record["valid"] is True
    assert "Record this as a valid timing? (y/n) " in script.prompts
    assert not any("Warning" in line for line in script.out)
    assert not any(p.startswith(("Class", "Prospective")) for p in script.prompts)
    for name in NAMES:
        assert name not in json.dumps(record)


def test_chronological_mode_records_a_stopped_review(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    script = Script(["", "", "q"])
    out = labeling.run_chronological(snap, script.console, root=tmp_path, week=date(2026, 8, 3))
    assert out is not None
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["complete"] is False
    assert record["comments_reviewed"] == 1
    # The validity question is still asked; end of input means practice.
    assert "stopped before the end of the week" in script.text
    assert record["valid"] is False
    assert out.parent == tmp_path / labeling.TIMING_ROOT / timing.PRACTICE_DIR


def chronological(tmp_path: Path, answers: list[str], step: float) -> tuple[Path, Script]:
    snap = snapshot(tmp_path)
    script = Script(answers)
    clock = ticker(step)
    out = labeling.run_chronological(
        snap,
        script.console,
        root=tmp_path,
        week=date(2026, 8, 3),
        now=lambda: NOW,
        monotonic=lambda: next(clock),
    )
    assert out is not None
    return out, script


def test_a_fast_review_warns_before_asking(tmp_path, fake_dev):
    # 0.5 s per clock tick: about 1.25 s per comment, under the 2 s floor.
    seen_at_prompt: list[str] = []
    snap = snapshot(tmp_path)
    script = Script(["", "", "", "y"])
    read = script.read

    def read_and_note(prompt: str) -> str:
        if prompt.startswith("Record this"):
            seen_at_prompt.extend(script.out)
        return read(prompt)

    clock = ticker(0.5)
    out = labeling.run_chronological(
        snap,
        labeling.Console(read_and_note, script.write),
        root=tmp_path,
        week=date(2026, 8, 3),
        now=lambda: NOW,
        monotonic=lambda: next(clock),
    )
    assert out is not None
    assert any(line.startswith("Warning: 1.2 seconds per comment") for line in seen_at_prompt)
    record = json.loads(out.read_text(encoding="utf-8"))
    # A warned run the reviewer still confirms is recorded as valid, with its average.
    assert record["valid"] is True
    assert record["seconds_per_comment"] < timing.MIN_SECONDS_PER_COMMENT


@pytest.mark.parametrize("answers", [["n"], ["maybe", "n"], ["q"], []])
def test_anything_but_yes_is_saved_as_practice(tmp_path, fake_dev, answers):
    out, script = chronological(tmp_path, ["", "", "", *answers], step=3.0)
    assert out.parent == tmp_path / labeling.TIMING_ROOT / timing.PRACTICE_DIR
    assert json.loads(out.read_text(encoding="utf-8"))["valid"] is False
    assert "Practice run, not counted as evidence" in script.text
    if answers[:1] == ["maybe"]:
        assert "Answer y or n." in script.text


def test_a_review_stopped_before_any_comment_is_practice_without_asking(tmp_path, fake_dev):
    out, script = chronological(tmp_path, ["", "q"], step=3.0)
    assert out.parent.name == timing.PRACTICE_DIR
    assert not any("valid timing" in p for p in script.prompts)


def test_chronological_mode_with_an_empty_week_writes_nothing(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    assert (
        labeling.run_chronological(snap, Script([]).console, root=tmp_path, week=date(2026, 9, 1))
        is None
    )
    assert not (tmp_path / labeling.TIMING_ROOT).exists()


# Command line and paths -----------------------------------------------------------


def test_cli_validates_arguments(tmp_path, fake_dev, capsys):
    make_run(tmp_path)
    base = ["--root", str(tmp_path), "label", "--run", "r1"]
    assert cli.main([*base, "--batch-size", "41"]) == 2
    assert cli.main([*base, "--mode", "chronological"]) == 2
    assert cli.main([*base, "--corpus-version", "../x"]) == 2
    assert cli.main([*base[:-1], "missing"]) == 2
    err = capsys.readouterr().err
    assert "--batch-size must be 1 to 40" in err
    assert "needs --week" in err


def test_cli_warns_on_a_stale_run_and_prints_no_names(tmp_path, fake_dev, capsys, monkeypatch):
    make_run(tmp_path, finished=datetime(2026, 1, 1, tzinfo=UTC))

    def no_input(prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)
    assert cli.main(["--root", str(tmp_path), "label", "--run", "r1"]) == 0
    out = capsys.readouterr().out
    assert "warning: run r1 finished" in out
    assert "Run a fresh full probe" in out
    assert "4 comments to label" in out


def test_cli_refuses_scoped_runs(tmp_path, fake_dev, capsys, monkeypatch):
    monkeypatch.setenv("DEV_API_KEY", FAKE_KEY)
    args = ["--root", str(tmp_path), "probe", "--min-interval", "0", "--article", "9000001"]
    assert cli.main(args) == 0
    (run_dir,) = (tmp_path / cli.RAW_ROOT).iterdir()
    assert cli.main(["--root", str(tmp_path), "label", "--run", run_dir.name]) == 2


@pytest.mark.skipif(shutil.which("git") is None, reason="git not available")
def test_every_output_path_is_git_ignored():
    paths = [
        labeling.LABEL_ROOT / "unfrozen" / "initial.jsonl",
        labeling.LABEL_ROOT / "corpus-v1" / "self_agreement.jsonl",
        labeling.LABEL_ROOT / "unfrozen" / "batches.jsonl",
        labeling.TIMING_ROOT / "chronological-2026-09-21-20261009T180000Z.json",
        labeling.TIMING_ROOT / timing.PRACTICE_DIR / "chronological-2026-09-21-x.json",
    ]
    for path in paths:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path.as_posix()], cwd=REPO, check=False
        )
        assert result.returncode == 0, path


def test_replied_before_labeling_means_a_direct_reply_by_the_author(tmp_path, fake_dev):
    snap = snapshot(tmp_path)
    assert snap.author_replied(snap.by_id["s1a1"])  # s1a2 is the author's reply
    assert not snap.author_replied(snap.by_id["s1a3"])
    assert not snap.author_replied(snap.by_id["s1b1"])


def test_full_runs_know_every_posts_edit_time(tmp_path, fake_dev):
    fake_dev.article["edited_at"] = "2026-08-10T00:00:00Z"
    snap = snapshot(tmp_path)
    assert all(c.edited_at is not None for c in snap.obs.contents)
    # Post one was edited on 08-10: after s1a1 (08-03), before s1a3 (08-12).
    assert not snap.context_reconstructed(snap.by_id["s1a1"])
    assert snap.context_reconstructed(snap.by_id["s1a3"])
