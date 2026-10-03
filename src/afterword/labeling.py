"""Local labeling tool (``afterword label``) and chronological review timing (C-009).

Runs in the author's own terminal. It reads one saved run through source-neutral
observations (ADR-001) and writes only to git-ignored paths: labels and batch
records under ``fixtures/labels/``, timing records under ``reports/timing/``
(valid) or ``reports/timing/practice/`` (not confirmed).

Comment text is shown with the display rendering in :mod:`afterword.display`,
not a classification normalization. Commenters appear as per-thread pseudonyms
("Commenter A"), never by name or handle, so a label rests on what a comment
says rather than on who wrote it. The author's own comments appear as
"You (author)".

Context follows ``docs/LABELING-GUIDE.md``: the post title and the comment's
thread as of the comment's ``created_at``. Earlier comments, including the
author's, are shown; later ones are hidden.
"""

from __future__ import annotations

import json
import os
import re
import string
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from afterword import timing
from afterword.baseline import week_start
from afterword.display import DISPLAY_VERSION, html_to_display_text, strip_controls
from afterword.observations import ObservedComment, ObservedContent, RunObservations

LABEL_ROOT: Path = Path("fixtures/labels")
TIMING_ROOT: Path = timing.TIMING_ROOT

LABEL_GUIDE_VERSION: str = "lg-v0.2"
TAXONOMY_VERSION: str = "tax-v0.1"
DEFAULT_CORPUS_VERSION: str = "unfrozen"
# Every historical comment is `dev` (ADR-010); prospective test labels pass `--set test`.
DEFAULT_CORPUS_SET: str = "dev"
PASSES: tuple[str, ...] = ("initial", "self_agreement")
MAX_BATCH: int = 40
STALE_AFTER: timedelta = timedelta(days=7)

# Precedence order from TAXONOMY.md, then UNCERTAIN.
CLASSES: tuple[str, ...] = (
    "CORRECTION",
    "CHALLENGE_OR_COUNTEREXAMPLE",
    "TECHNICAL_QUESTION",
    "OPPORTUNITY",
    "DIRECT_QUESTION",
    "TECHNICAL_EXTENSION",
    "CONVERSATIONAL",
    "LIGHTWEIGHT_ACKNOWLEDGMENT",
    "LIKELY_SPAM_OR_NOISE",
    "UNCERTAIN",
)
# REPLY_TO_AUTHOR is structural (TAXONOMY.md) and set by the tool, not chosen.
REPLY_TO_AUTHOR: str = "REPLY_TO_AUTHOR"
LABELER_FLAGS: tuple[str, ...] = (
    "NEEDS_THREAD_CONTEXT",
    "CONTAINS_CODE",
    "CONTAINS_LINK",
    "REFERENCES_SPECIFIC_CLAIM",
    "ADDRESSED_TO_OTHER_COMMENTER",
    "HOSTILE_TONE",
    "POSSIBLE_INSTRUCTION_TEXT",
)

_SAFE_NAME: re.Pattern[str] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MAX_INDENT: int = 8
_RULE: str = "=" * 72
_THIN_RULE: str = "-" * 72


class Quit(Exception):
    """Raised when the labeler asks to stop."""


class Console:
    """Terminal input and output, injectable for tests."""

    def __init__(
        self,
        read: Callable[[str], str] | None = None,
        write: Callable[[str], None] | None = None,
    ) -> None:
        """Create a console.

        :param read: Prompt and return one line; :func:`input` when ``None``.
        :param write: Print one block of text; :func:`print` when ``None``.
        """
        self._read = read if read is not None else input
        self._write = write if write is not None else print

    def say(self, text: str = "") -> None:
        """Print text.

        :param text: Text to print.
        """
        self._write(text)

    def ask(self, prompt: str) -> str:
        """Prompt for one line. ``q`` or end of input stops the session.

        :param prompt: Prompt text.
        :returns: The answer, stripped.
        :raises Quit: If the answer is ``q`` or input has ended.
        """
        try:
            answer = self._read(prompt).strip()
        except EOFError:
            raise Quit from None
        if answer.lower() == "q":
            raise Quit
        return answer


def safe_name(value: str) -> str:
    """Check that a user-supplied name is safe as one path component.

    :param value: Name such as a corpus version.
    :returns: The name unchanged.
    :raises ValueError: If the name could escape its directory or is empty.
    """
    if not _SAFE_NAME.fullmatch(value):
        raise ValueError(f"not a safe name: {value!r}")
    return value


def _utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _shown_time(moment: datetime | None) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC") if moment else "unknown time"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def _labeled_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            ids.add(str(json.loads(line)["comment_id"]))
    return ids


class Snapshot:
    """One run's comments arranged into threads, for display and labeling."""

    def __init__(self, obs: RunObservations) -> None:
        """Index a run's observations.

        :param obs: Observations loaded with text.
        """
        self.obs = obs
        self.contents: dict[str, ObservedContent] = {c.content_ref: c for c in obs.contents}
        self.by_id: dict[str, ObservedComment] = {c.source_object_id: c for c in obs.comments}
        self.root_of: dict[str, str] = {}
        self.threads: dict[str, list[ObservedComment]] = defaultdict(list)
        # Observations are depth first, so a parent is always indexed before its children.
        for c in obs.comments:
            parent = c.parent_source_object_id
            root = self.root_of.get(parent, parent) if parent else c.source_object_id
            self.root_of[c.source_object_id] = root
            self.threads[root].append(c)

    @staticmethod
    def is_subject(c: ObservedComment) -> bool:
        """Report whether a comment is labeled: from others, live, of known shape and time.

        :param c: A comment.
        :returns: ``False`` for the author's comments (ADR-011), deletion placeholders
            (ADR-009), unexpected shapes, and undated comments.
        """
        return not (
            c.is_content_author
            or c.is_deletion_placeholder
            or c.is_unexpected_shape
            or c.created_at is None
        )

    def subjects(self) -> list[ObservedComment]:
        """List the comments to label, in post order and then in time order.

        Time order within a post means a comment is never labeled after a later
        comment from the same post has been seen.

        :returns: Labelable comments.
        """
        floor = datetime.min.replace(tzinfo=UTC)

        def key(c: ObservedComment) -> tuple[datetime, str, datetime, str]:
            content = self.contents.get(c.content_ref)
            published = content.published_at if content and content.published_at else floor
            return (published, c.content_ref, c.created_at or floor, c.source_object_id)

        return sorted((c for c in self.obs.comments if self.is_subject(c)), key=key)

    def excluded_counts(self) -> dict[str, int]:
        """Count comments that are never labeled, by reason.

        :returns: Counts of author comments, placeholders, unexpected shapes, and undated comments.
        """
        comments = self.obs.comments
        return {
            "by_author": sum(1 for c in comments if c.is_content_author),
            "deletion_placeholders": sum(1 for c in comments if c.is_deletion_placeholder),
            "unexpected_shapes": sum(1 for c in comments if c.is_unexpected_shape),
            "undated": sum(1 for c in comments if c.created_at is None),
        }

    def thread(self, c: ObservedComment) -> list[ObservedComment]:
        """Return the whole top-level thread containing a comment, depth first.

        :param c: A comment.
        :returns: Every comment in its thread, including later ones.
        """
        return self.threads[self.root_of[c.source_object_id]]

    def as_of(self, c: ObservedComment) -> list[ObservedComment]:
        """Return the thread as it stood when a comment was posted.

        :param c: The comment being shown.
        :returns: Thread comments created at or before ``c``, depth first, ``c`` included.
        """
        cutoff = c.created_at
        return [
            t
            for t in self.thread(c)
            if t is c or (cutoff and t.created_at is not None and t.created_at <= cutoff)
        ]

    def hidden_later(self, c: ObservedComment) -> int:
        """Count thread comments hidden because they came later or have no time.

        :param c: The comment being shown.
        :returns: Number of hidden comments.
        """
        return len(self.thread(c)) - len(self.as_of(c))

    def ancestors(self, c: ObservedComment) -> list[ObservedComment]:
        """Return the reply chain above a comment, top level first.

        :param c: A comment.
        :returns: Its ancestors, excluding itself.
        """
        chain = []
        parent = c.parent_source_object_id
        while parent and parent in self.by_id:
            chain.append(self.by_id[parent])
            parent = self.by_id[parent].parent_source_object_id
        return list(reversed(chain))

    def context_gaps(self, c: ObservedComment) -> list[str]:
        """List known reasons the shown context may differ from what the commenter saw.

        Parent edits are undetectable on DEV and never appear here
        (``docs/LABELING-GUIDE.md``).

        :param c: The comment being labeled.
        :returns: Human-readable reasons; empty when no gap is known.
        """
        gaps = []
        if any(t.is_deletion_placeholder for t in self.as_of(c) if t is not c):
            gaps.append("an earlier comment in this thread was deleted")
        if any(t.created_at is None for t in self.thread(c)):
            gaps.append("a comment in this thread has no timestamp")
        content = self.contents.get(c.content_ref)
        if content and content.edited_at and c.created_at and content.edited_at > c.created_at:
            gaps.append("the post was edited after this comment")
        return gaps

    def context_reconstructed(self, c: ObservedComment) -> bool:
        """Report whether no gap in the reconstructed context is known.

        :param c: The comment being labeled.
        :returns: ``True`` means "no known gap", not "verified identical".
        """
        return not self.context_gaps(c)

    def reply_to_author(self, c: ObservedComment) -> bool:
        """Report the structural ``REPLY_TO_AUTHOR`` flag.

        A reply to a deletion placeholder is not flagged: its authorship is
        unknown from a single snapshot (ADR-009).

        :param c: A comment.
        :returns: ``True`` if its parent was written by the content author.
        """
        parent = self.by_id.get(c.parent_source_object_id or "")
        return bool(parent and parent.is_content_author and not parent.is_deletion_placeholder)

    def author_replied(self, c: ObservedComment) -> bool:
        """Report whether the author's direct reply to a comment exists in this run.

        Recorded as ``replied_before_labeling``: a prospective grade given after
        replying may carry hindsight the grade is meant to exclude.

        :param c: A comment.
        :returns: ``True`` if a comment by the content author has ``c`` as its parent.
        """
        return any(
            t.is_content_author and t.parent_source_object_id == c.source_object_id
            for t in self.thread(c)
        )

    def pseudonyms(self, c: ObservedComment) -> dict[str, str]:
        """Name the commenters in a comment's thread A, B, C, ... by first appearance.

        :param c: Any comment in the thread.
        :returns: Display name by comment ID.
        """
        letters: dict[str, str] = {}
        names: dict[str, str] = {}
        timed = sorted(
            self.thread(c),
            key=lambda t: (t.created_at or datetime.max.replace(tzinfo=UTC), t.source_object_id),
        )
        for t in timed:
            if t.is_deletion_placeholder:
                names[t.source_object_id] = "[deleted comment]"
            elif t.is_content_author:
                names[t.source_object_id] = "You (author)"
            elif t.author_ref is None:
                names[t.source_object_id] = "Commenter ?"
            else:
                if t.author_ref not in letters:
                    letters[t.author_ref] = _letter(len(letters))
                names[t.source_object_id] = f"Commenter {letters[t.author_ref]}"
        return names


def _letter(i: int) -> str:
    letters = string.ascii_uppercase
    return letters[i] if i < 26 else letters[i // 26 - 1] + letters[i % 26]


def render(snap: Snapshot, c: ObservedComment, *, position: str, full_thread: bool) -> str:
    """Render one comment with its post title and thread context as of its time.

    :param snap: The run being labeled.
    :param c: The comment to show.
    :param position: Progress text, such as ``3 of 40``.
    :param full_thread: Show every earlier comment in the thread, not only the reply chain.
    :returns: Terminal text. Contains no commenter names or handles.
    """
    content = snap.contents.get(c.content_ref)
    title = strip_controls(content.title) if content and content.title else "(untitled post)"
    earlier = snap.as_of(c)
    names = snap.pseudonyms(c)
    shown = earlier if full_thread else [*snap.ancestors(c), c]
    gaps = snap.context_gaps(c)
    lines = [
        _RULE,
        f"Post: {title}",
        f"Comment {position}, posted {_shown_time(c.created_at)}",
        (
            f"Thread as of this comment: {len(earlier) - 1} earlier shown"
            f"{'' if full_thread else ' (reply chain only; t shows all)'}, "
            f"{snap.hidden_later(c)} later hidden"
        ),
        "Context: " + ("no known gaps" if not gaps else "incomplete, " + "; ".join(gaps)),
        _THIN_RULE,
    ]
    for t in shown:
        depth = t.depth
        indent = "  " * min(depth, _MAX_INDENT)
        deep = f" (depth {depth})" if depth > _MAX_INDENT else ""
        marker = ">>> " if t is c else ""
        suffix = "   <-- THIS COMMENT" if t is c else ""
        who = names[t.source_object_id]
        lines.append(f"{indent}{marker}[{_shown_time(t.created_at)}] {who}{deep}{suffix}")
        if not t.is_deletion_placeholder:
            body = html_to_display_text(t.body_source) or "(empty)"
            lines.extend(f"{indent}    {line}" if line else "" for line in body.split("\n"))
        lines.append("")
    lines.append(_THIN_RULE)
    return "\n".join(lines)


def _menu(options: tuple[str, ...]) -> str:
    return "\n".join(f"  {i:>2}. {name}" for i, name in enumerate(options, start=1))


def _grade(answer: str, *, optional: bool) -> int | None:
    if optional and answer == "":
        return None
    if answer in ("0", "1", "2", "3"):
        return int(answer)
    raise ValueError


def _flags(answer: str) -> list[str]:
    if not answer:
        return []
    picked = []
    for part in answer.replace(" ", ",").split(","):
        if not part:
            continue
        number = int(part)
        if not 1 <= number <= len(LABELER_FLAGS):
            raise ValueError
        picked.append(LABELER_FLAGS[number - 1])
    return [f for f in LABELER_FLAGS if f in picked]


def _ask_valid[T](console: Console, prompt: str, parse: Callable[[str], T]) -> T:
    while True:
        answer = console.ask(prompt)
        try:
            return parse(answer)
        except ValueError:
            console.say("  Not understood, try again.")


@dataclass(frozen=True)
class LabelContext:
    """Fixed fields shared by every label in a batch."""

    snapshot_run_id: str
    corpus_version: str
    corpus_set: str
    pass_name: str
    batch_id: str


def label_one(
    console: Console,
    snap: Snapshot,
    c: ObservedComment,
    ctx: LabelContext,
    *,
    position: str,
    now: Callable[[], datetime],
    monotonic: Callable[[], float],
) -> tuple[dict[str, Any] | None, str]:
    """Show one comment and collect its label.

    The retrospective prompt appears only after the prospective grade is entered.

    :param console: Terminal.
    :param snap: The run being labeled.
    :param c: The comment to label.
    :param ctx: Batch-wide label fields.
    :param position: Progress text, such as ``3 of 40``.
    :param now: Wall clock for ``labeled_at``.
    :param monotonic: Clock for ``duration_seconds``.
    :returns: The label record, or ``None`` if skipped; and an optional hard-to-label note.
    """
    started = monotonic()
    full = False
    console.say(render(snap, c, position=position, full_thread=full))
    reply_to_author = snap.reply_to_author(c)
    while True:
        console.say("Primary class (TAXONOMY.md precedence order):\n" + _menu(CLASSES))
        while True:
            answer = console.ask(f"Class [1-{len(CLASSES)}], t = toggle full thread, s = skip: ")
            if answer.lower() == "t":
                full = not full
                console.say(render(snap, c, position=position, full_thread=full))
                continue
            if answer.lower() == "s":
                return None, ""
            if answer.isdigit() and 1 <= int(answer) <= len(CLASSES):
                primary = CLASSES[int(answer) - 1]
                break
            console.say("  Not understood, try again.")

        auto = f"  ({REPLY_TO_AUTHOR} is set automatically: this replies to you.)"
        console.say("Flags:\n" + _menu(LABELER_FLAGS) + ("\n" + auto if reply_to_author else ""))
        flags = _ask_valid(console, "Flags [numbers, comma-separated; Enter for none]: ", _flags)
        prospective = _ask_valid(
            console,
            "Prospective grade, as of when it was posted [0-3]: ",
            lambda a: _grade(a, optional=False),
        )
        retrospective = _ask_valid(
            console,
            "Retrospective grade, with hindsight [0-3; Enter to skip]: ",
            lambda a: _grade(a, optional=True),
        )
        needs_reason = prospective is not None and prospective >= 2
        reason_prompt = "Reason (one line, required for grade 2 or 3): "
        reason = console.ask(reason_prompt if needs_reason else "Reason (optional): ")
        while needs_reason and not reason:
            reason = console.ask(reason_prompt)
        note = console.ask(
            "Hard to label? Note for the session notes (optional, not stored in the label): "
        )

        all_flags = ([REPLY_TO_AUTHOR] if reply_to_author else []) + flags
        retro = "skipped" if retrospective is None else str(retrospective)
        console.say(
            f"\n  {primary} | flags: {', '.join(all_flags) or 'none'} | "
            f"prospective {prospective} | retrospective {retro}"
        )
        decision = console.ask("Save? [Enter = yes, r = redo, s = skip]: ").lower()
        if decision == "r":
            continue
        if decision == "s":
            return None, note
        break

    record = {
        "label_id": f"l_{c.source_object_id}_{ctx.pass_name}",
        "comment_id": c.source_object_id,
        "snapshot_run_id": ctx.snapshot_run_id,
        "corpus_version": ctx.corpus_version,
        "corpus_set": ctx.corpus_set,
        "label_guide_version": LABEL_GUIDE_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "normalization_version": DISPLAY_VERSION,
        "primary_class": primary,
        "flags": all_flags,
        "consequential_prospective": prospective,
        "consequential_retrospective": retrospective,
        "consequential_retrospective_state": "UNKNOWN" if retrospective is None else "PRESENT",
        "context_reconstructed": snap.context_reconstructed(c),
        "replied_before_labeling": snap.author_replied(c),
        "reason": reason,
        "pass": ctx.pass_name,
        "batch_id": ctx.batch_id,
        "duration_seconds": round(monotonic() - started, 1),
        "labeled_at": _utc(now()),
    }
    return record, note


def run_labeling(
    snap: Snapshot,
    console: Console,
    *,
    root: Path,
    pass_name: str = "initial",
    corpus_version: str = DEFAULT_CORPUS_VERSION,
    corpus_set: str = DEFAULT_CORPUS_SET,
    batch_size: int = MAX_BATCH,
    only_ids: set[str] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    monotonic: Callable[[], float] = time.monotonic,
) -> int:
    """Label one batch of comments not yet labeled in this pass, then stop.

    Labels are appended as they are saved, so stopping at any point loses at
    most the comment on screen. Running again resumes with the next unlabeled
    comment.

    :param snap: The run to label from.
    :param console: Terminal.
    :param root: Repository root; outputs go under ``fixtures/labels/``.
    :param pass_name: ``initial`` or ``self_agreement``.
    :param corpus_version: Output directory name and label field.
    :param corpus_set: Label field: ``dev`` for historical comments, ``test`` for prospective ones.
    :param batch_size: At most :data:`MAX_BATCH`.
    :param only_ids: Restrict to these comment IDs, such as a self-agreement sample.
    :param now: Wall clock.
    :param monotonic: Clock for durations.
    :returns: Number of labels saved in this batch.
    :raises ValueError: For an unknown pass, an unsafe name, or a batch size out of range.
    """
    if pass_name not in PASSES:
        raise ValueError(f"unknown pass: {pass_name}")
    if not 1 <= batch_size <= MAX_BATCH:
        raise ValueError(f"batch size must be 1 to {MAX_BATCH}")
    out_dir = root / LABEL_ROOT / safe_name(corpus_version)
    labels_path = out_dir / f"{pass_name}.jsonl"
    batches_path = out_dir / "batches.jsonl"

    done = _labeled_ids(labels_path)
    queue = [
        c
        for c in snap.subjects()
        if c.source_object_id not in done and (only_ids is None or c.source_object_id in only_ids)
    ]
    if not queue:
        console.say(f"Nothing left to label in pass {pass_name} ({len(done)} already labeled).")
        return 0
    batch = queue[:batch_size]
    started = now()
    ctx = LabelContext(
        snapshot_run_id=snap.obs.run_id,
        corpus_version=corpus_version,
        corpus_set=safe_name(corpus_set),
        pass_name=pass_name,
        batch_id=f"b_{_stamp(started)}",
    )
    _append_jsonl(
        batches_path,
        {
            "event": "batch_start",
            "batch_id": ctx.batch_id,
            "pass": pass_name,
            "snapshot_run_id": ctx.snapshot_run_id,
            "mode": "label",
            "planned": len(batch),
            "started_at": _utc(started),
        },
    )
    console.say(
        f"Batch {ctx.batch_id}: {len(batch)} comments ({len(queue)} unlabeled, "
        f"{len(done)} done). q at any prompt stops; saved labels are kept."
    )
    saved = skipped = 0
    ended_by = "complete"
    try:
        for i, c in enumerate(batch, start=1):
            record, note = label_one(
                console,
                snap,
                c,
                ctx,
                position=f"{i} of {len(batch)}",
                now=now,
                monotonic=monotonic,
            )
            if note:
                _append_jsonl(
                    batches_path,
                    {
                        "event": "note",
                        "batch_id": ctx.batch_id,
                        "comment_id": c.source_object_id,
                        "note": note,
                    },
                )
            if record is None:
                skipped += 1
                continue
            _append_jsonl(labels_path, record)
            saved += 1
    except (Quit, KeyboardInterrupt):
        ended_by = "quit"
    _append_jsonl(
        batches_path,
        {
            "event": "batch_end",
            "batch_id": ctx.batch_id,
            "ended_at": _utc(now()),
            "labeled": saved,
            "skipped": skipped,
            "ended_by": ended_by,
        },
    )
    console.say(
        f"\nBatch {ctx.batch_id} ended ({ended_by}): {saved} labeled, {skipped} skipped, "
        f"{len(queue) - saved} still unlabeled in pass {pass_name}."
    )
    return saved


def run_chronological(
    snap: Snapshot,
    console: Console,
    *,
    root: Path,
    week: date,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    monotonic: Callable[[], float] = time.monotonic,
) -> Path | None:
    """Time a chronological review of one week's comments from others (C-009, B0).

    Comments are shown oldest first with the same context view as labeling.
    There are no labeling prompts: Enter moves to the next comment.

    :param snap: The run to review from.
    :param console: Terminal.
    At the end the reviewer is asked whether to record the run as a valid timing,
    with a warning first when the average is under
    :data:`afterword.timing.MIN_SECONDS_PER_COMMENT`. Only a ``y`` makes it
    evidence; any other ending saves it under ``reports/timing/practice/``.

    :param root: Repository root; the record goes under ``reports/timing/``.
    :param week: Any date in the week; the week starts on its Monday (UTC).
    :param now: Wall clock.
    :param monotonic: Clock for durations.
    :returns: Path of the timing record, or ``None`` if the week has no comments.
    """
    start = week_start(week)
    end = start + timedelta(days=7)
    items = sorted(
        (
            c
            for c in snap.subjects()
            if c.created_at and start <= c.created_at.astimezone(UTC).date() < end
        ),
        key=lambda c: (c.created_at, c.source_object_id),
    )
    console.say(
        f"Week {start.isoformat()} to {(end - timedelta(days=1)).isoformat()}: "
        f"{len(items)} comments from others, oldest first."
    )
    if not items:
        return None
    try:
        console.ask("Enter starts the clock. Enter after each comment moves on; q stops: ")
    except (Quit, KeyboardInterrupt):
        console.say("Not started; nothing recorded.")
        return None

    started_at = now()
    t0 = monotonic()
    per_comment: list[dict[str, Any]] = []
    complete = True
    try:
        for i, c in enumerate(items, start=1):
            shown = monotonic()
            console.say(render(snap, c, position=f"{i} of {len(items)}", full_thread=False))
            console.ask("Enter for next, q to stop: ")
            per_comment.append(
                {"comment_id": c.source_object_id, "seconds": round(monotonic() - shown, 1)}
            )
    except (Quit, KeyboardInterrupt):
        complete = False
    total = round(monotonic() - t0, 1)
    ended_at = now()
    average = timing.seconds_per_comment(total, len(per_comment))
    console.say(
        f"\n{'Complete' if complete else 'Stopped early'}: {len(per_comment)} of {len(items)} "
        f"comments in {total} seconds"
        + ("." if average is None else f" ({average} seconds per comment).")
    )
    valid = _confirm_valid(console, average=average, complete=complete)

    record = {
        "mode": "chronological",
        "condition": "B0",
        "snapshot_run_id": snap.obs.run_id,
        "week_start": start.isoformat(),
        "week_end": (end - timedelta(days=1)).isoformat(),
        "display_version": DISPLAY_VERSION,
        "context_view": "reply chain as of each comment",
        "comments_in_week": len(items),
        "comments_reviewed": len(per_comment),
        "complete": complete,
        "started_at": _utc(started_at),
        "ended_at": _utc(ended_at),
        "total_seconds": total,
        "seconds_per_comment": average,
        "valid": valid,
        "per_comment_seconds": per_comment,
    }
    out_dir = timing.record_dir(root, valid=valid)
    out = out_dir / f"chronological-{start.isoformat()}-{_stamp(started_at)}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    kind = "Valid timing" if valid else "Practice run, not counted as evidence"
    console.say(f"{kind}. Record: {out}")
    return out


def _confirm_valid(console: Console, *, average: float | None, complete: bool) -> bool:
    """Ask whether a finished review counts as a valid timing.

    :param console: Terminal.
    :param average: Seconds per comment, or ``None`` when nothing was reviewed.
    :param complete: Whether every comment in the week was reviewed.
    :returns: ``True`` only for an explicit ``y``. ``n``, ``q``, end of input, and
        an interrupt all mean practice.
    """
    if average is None:
        console.say("No comments were reviewed; saving as practice.")
        return False
    if average < timing.MIN_SECONDS_PER_COMMENT:
        console.say(
            f"Warning: {average} seconds per comment is under "
            f"{timing.MIN_SECONDS_PER_COMMENT}. That is faster than reading each comment "
            "and its reply chain; this looks like a practice run."
        )
    if not complete:
        console.say("Warning: the review stopped before the end of the week.")
    try:
        while True:
            answer = console.ask("Record this as a valid timing? (y/n) ").lower()
            if answer in ("y", "n"):
                return answer == "y"
            console.say("  Answer y or n.")
    except (Quit, KeyboardInterrupt):
        return False
