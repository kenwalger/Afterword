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
import random
import re
import string
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from afterword import label_records, normalize, taxonomy, timing
from afterword.baseline import week_start
from afterword.display import DISPLAY_VERSION, html_to_display_text, strip_controls
from afterword.observations import ObservedComment, ObservedContent, RunObservations

LABEL_ROOT: Path = label_records.LABEL_ROOT
TIMING_ROOT: Path = timing.TIMING_ROOT

LABEL_GUIDE_VERSION: str = "lg-v0.4"
TAXONOMY_VERSION: str = taxonomy.TAXONOMY_VERSION
DEFAULT_CORPUS_VERSION: str = "unfrozen"
# Every historical comment is `dev` (ADR-010); prospective test labels pass `--set test`.
DEFAULT_CORPUS_SET: str = "dev"
# Who produced a label and how it was sampled. Every V1 label is the researcher's
# own (EVALUATION.md); other sources are a future design (LABELING-AT-SCALE.md).
SAMPLE_KIND: str = "researcher"
PASSES: tuple[str, ...] = label_records.PASSES
# A calibration pass re-labels only comments that already have an initial label.
CALIBRATION_PASS: str = "calibration"
MAX_BATCH: int = 40
STALE_AFTER: timedelta = timedelta(days=7)
# Post order: by publication time, or shuffled by a recorded seed. Comments
# within a post are always oldest first (LABELING-GUIDE.md).
POST_ORDERS: tuple[str, ...] = ("published", "random")

# Precedence order from TAXONOMY.md, then UNCERTAIN.
CLASSES: tuple[str, ...] = taxonomy.CLASSES
# REPLY_TO_AUTHOR is structural (TAXONOMY.md) and set by the tool, not chosen.
REPLY_TO_AUTHOR: str = taxonomy.REPLY_TO_AUTHOR
# From tax-v0.2 the code and link flags are structural too: the tool sets them
# from the comment's classification normalization, shown read-only.
LABELER_FLAGS: tuple[str, ...] = tuple(
    f for f in taxonomy.FLAGS if f not in taxonomy.STRUCTURAL_FLAGS
)

_SAFE_NAME: re.Pattern[str] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
# Elements whose content is not post text: dropped before the display rendering.
_NON_TEXT: re.Pattern[str] = re.compile(
    r"<(script|style|template|noscript)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_MAX_INDENT: int = 8
_RULE: str = "=" * 72
_THIN_RULE: str = "-" * 72


class Quit(Exception):
    """Raised when the labeler asks to stop."""


class Abandoned(Quit):
    """Raised when the session stops while a comment is on screen, unsaved."""

    def __init__(self, *, answered: bool) -> None:
        """Record whether any answer had been given for the comment.

        :param answered: ``True`` once a class was chosen for the comment.
        """
        super().__init__()
        self.answered = answered


class SavedThenQuit(Quit):
    """Raised when the labeler confirms the summary with ``q``: save, then stop."""

    def __init__(self, record: dict[str, Any], note: str) -> None:
        """Carry the confirmed label to be saved before stopping.

        :param record: The label record, built and valid.
        :param note: The hard-to-label note, possibly empty.
        """
        super().__init__()
        self.record = record
        self.note = note


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


def _batch_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        str(json.loads(line).get("batch_id"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


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

    def subjects(
        self, *, post_order: str = "published", seed: int | None = None
    ) -> list[ObservedComment]:
        """List the comments to label, post by post and oldest first within a post.

        Time order within a post means a comment is never labeled after a later
        comment from the same post has been seen. Posts come in publication
        order, or in a shuffled order that a seed makes reproducible, so a
        resumed session continues the same order.

        :param post_order: ``published`` or ``random``.
        :param seed: Seed for ``random``; required for it, ignored otherwise.
        :returns: Labelable comments.
        :raises ValueError: For an unknown order, or ``random`` without a seed.
        """
        if post_order not in POST_ORDERS:
            raise ValueError(f"unknown post order: {post_order}")
        if post_order == "random" and seed is None:
            raise ValueError("random post order needs a seed")
        floor = datetime.min.replace(tzinfo=UTC)

        def post_key(ref: str) -> tuple[datetime, str]:
            content = self.contents.get(ref)
            return (content.published_at if content and content.published_at else floor, ref)

        by_post: dict[str, list[ObservedComment]] = defaultdict(list)
        for c in self.obs.comments:
            if self.is_subject(c):
                by_post[c.content_ref].append(c)
        posts = sorted(by_post, key=post_key)
        if post_order == "random":
            random.Random(seed).shuffle(posts)
        return [
            c
            for ref in posts
            for c in sorted(by_post[ref], key=lambda c: (c.created_at or floor, c.source_object_id))
        ]

    def has_post_bodies(self) -> bool:
        """Report whether the run captured any post body, for the label UI's post panel.

        :returns: ``True`` when at least one post's body was loaded.
        """
        return any(c.body_source is not None for c in self.contents.values())

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

    def structural_flags(self, c: ObservedComment) -> list[str]:
        """Return the flags the tool sets for a comment, never the labeler.

        ``REPLY_TO_AUTHOR`` from the thread, and ``CONTAINS_CODE`` and
        ``CONTAINS_LINK`` from the comment's classification normalization
        (`norm-v0.1`), not from the display rendering.

        :param c: A comment.
        :returns: Flag names in taxonomy order.
        """
        found = set(
            normalize.content_flags(
                normalize.normalize(c.body_source, c.body_source_format or "HTML")
            )
        )
        if self.reply_to_author(c):
            found.add(REPLY_TO_AUTHOR)
        return [f for f in taxonomy.FLAGS if f in found]

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


def _ask_valid[T](
    console: Console, prompt: str, parse: Callable[[str], T], *, help_text: str | None = None
) -> T:
    while True:
        answer = console.ask(prompt)
        if help_text is not None and answer.lower() == "h":
            console.say(help_text)
            continue
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


def make_label(
    snap: Snapshot,
    c: ObservedComment,
    ctx: LabelContext,
    *,
    primary: str,
    flags: list[str],
    prospective: int,
    retrospective: int | None,
    reason: str,
    duration_seconds: float,
    labeled_at: datetime,
) -> dict[str, Any]:
    """Build one label record, the same for every transport (terminal or browser).

    Structural flags are added here and refused if a labeler supplies one:
    ``REPLY_TO_AUTHOR`` when the comment replies to the author, and, from
    `tax-v0.2`, ``CONTAINS_CODE`` and ``CONTAINS_LINK`` from normalization.

    :param snap: The run being labeled.
    :param c: The labeled comment.
    :param ctx: Batch-wide label fields.
    :param primary: Primary class.
    :param flags: Labeler-chosen flags, any order.
    :param prospective: Grade 0 to 3, as of when the comment was posted.
    :param retrospective: Grade 0 to 3 with hindsight, or ``None`` when skipped.
    :param reason: One line; required for a prospective grade of 2 or 3.
    :param duration_seconds: Time from the comment being shown to the label being saved.
    :param labeled_at: Wall-clock time of saving.
    :returns: The record, per the schema in ``fixtures/README.md``.
    :raises ValueError: For an unknown class or flag, a grade outside 0 to 3, or a
        missing reason on a consequential grade.
    """
    if primary not in CLASSES:
        raise ValueError(f"unknown class: {primary}")
    unknown = set(flags) - set(LABELER_FLAGS)
    if unknown:
        raise ValueError(f"not a labeler flag: {sorted(unknown)}")
    grades = (prospective,) if retrospective is None else (prospective, retrospective)
    if any(isinstance(g, bool) or g not in (0, 1, 2, 3) for g in grades):
        raise ValueError("grades are 0 to 3")
    reason = reason.strip()
    if prospective >= 2 and not reason:
        raise ValueError("a reason is required for grade 2 or 3")
    ordered = [f for f in LABELER_FLAGS if f in flags]
    all_flags = snap.structural_flags(c) + ordered
    return {
        "label_id": f"l_{c.source_object_id}_{ctx.pass_name}",
        "comment_id": c.source_object_id,
        "snapshot_run_id": ctx.snapshot_run_id,
        "corpus_version": ctx.corpus_version,
        "corpus_set": ctx.corpus_set,
        "sample_kind": SAMPLE_KIND,
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
        "duration_seconds": round(duration_seconds, 1),
        "labeled_at": _utc(labeled_at),
    }


def comment_view(snap: Snapshot, c: ObservedComment) -> dict[str, Any]:
    """Describe one comment and its as-of context as data, for a non-terminal transport.

    The same context as :func:`render`: the post title, and the thread as of the
    comment's time, with later comments hidden and commenters as pseudonyms.

    :param snap: The run being labeled.
    :param c: The comment to show.
    :returns: JSON-ready fields. Contains no commenter names or handles.
    """
    content = snap.contents.get(c.content_ref)
    names = snap.pseudonyms(c)
    chain = {t.source_object_id for t in snap.ancestors(c)}
    earlier = snap.as_of(c)
    return {
        "comment_id": c.source_object_id,
        "post_title": strip_controls(content.title) if content and content.title else None,
        "posted": _shown_time(c.created_at),
        "earlier_shown": len(earlier) - 1,
        "later_hidden": snap.hidden_later(c),
        "context_gaps": snap.context_gaps(c),
        "context_reconstructed": snap.context_reconstructed(c),
        "replied_before_labeling": snap.author_replied(c),
        "reply_to_author": snap.reply_to_author(c),
        "structural_flags": snap.structural_flags(c),
        "thread": [
            {
                "who": names[t.source_object_id],
                "posted": _shown_time(t.created_at),
                "depth": t.depth,
                "is_this": t is c,
                "in_reply_chain": t.source_object_id in chain,
                "deleted": t.is_deletion_placeholder,
                "body": None
                if t.is_deletion_placeholder
                else (html_to_display_text(t.body_source) or "(empty)"),
            }
            for t in earlier
        ],
    }


def post_view(snap: Snapshot, c: ObservedComment) -> dict[str, Any]:
    """Describe the post a comment was left on, for the label UI's post panel.

    The body comes from the saved run's single fetch of the post, rendered with
    the display rendering as plain text, so it carries no live links, images,
    or scripts. It is the post as of the run, which may differ from what the
    commenter saw if the post was edited after the comment. No comments, no
    profiles, nothing fetched.

    :param snap: The run being labeled.
    :param c: The comment whose post to show.
    :returns: JSON-ready fields: ``available``, and when available the title,
        publication and edit times, ``edited_after_comment``, and the body text;
        otherwise ``reason``.
    """
    content = snap.contents.get(c.content_ref)
    if content is None or content.body_source is None:
        return {
            "available": False,
            "reason": "This run did not capture the post's body (only runs from "
            "dev-probe-0.2 on fetch every post singly). Run a fresh full probe.",
        }
    edited_after = bool(content.edited_at and c.created_at and content.edited_at > c.created_at)
    return {
        "available": True,
        "title": strip_controls(content.title) if content.title else None,
        "published": _shown_time(content.published_at),
        "edited": _shown_time(content.edited_at) if content.edited_at else None,
        "edited_after_comment": edited_after,
        "body": html_to_display_text(_NON_TEXT.sub("", content.body_source)) or "(empty)",
    }


class LabelBatch:
    """One labeling batch: what to label, and its records under ``fixtures/labels/``.

    Shared by every transport, so the terminal and the browser write the same
    labels, notes, and batch records. Labels are appended as they are saved, so
    stopping at any point loses at most the comment on screen, and the next
    batch resumes with the next unlabeled comment in the same order.
    """

    def __init__(
        self,
        snap: Snapshot,
        *,
        root: Path,
        pass_name: str = "initial",
        corpus_version: str = DEFAULT_CORPUS_VERSION,
        corpus_set: str = DEFAULT_CORPUS_SET,
        batch_size: int = MAX_BATCH,
        only_ids: set[str] | None = None,
        post_order: str = "published",
        seed: int | None = None,
        tool: str = "terminal",
        post_panel: bool = False,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Choose the batch. Nothing is written until :meth:`start`.

        A calibration pass queues only comments that already have an initial
        label (narrowed further by ``only_ids``), and never shows that label.

        :param snap: The run to label from.
        :param root: Repository root; outputs go under ``fixtures/labels/``.
        :param pass_name: ``initial``, ``calibration``, or ``self_agreement``.
        :param corpus_version: Output directory name and label field.
        :param corpus_set: ``dev`` for historical comments, ``test`` for prospective ones.
        :param batch_size: At most :data:`MAX_BATCH`.
        :param only_ids: Restrict to these comment IDs, such as a self-agreement sample.
        :param post_order: ``published`` or ``random`` (:meth:`Snapshot.subjects`).
        :param seed: Seed for ``random``.
        :param tool: The transport, ``terminal`` or ``browser``, recorded on the batch.
        :param post_panel: Whether the transport can show the post's body (the label
            UI's post panel, when the run captured post bodies), recorded on the batch.
        :param now: Wall clock.
        :raises ValueError: For an unknown pass, order, or tool, an unsafe name, a
            batch size out of range, or ``random`` without a seed.
        """
        if pass_name not in PASSES:
            raise ValueError(f"unknown pass: {pass_name}")
        if tool not in label_records.TOOLS:
            raise ValueError(f"unknown tool: {tool}")
        if not 1 <= batch_size <= MAX_BATCH:
            raise ValueError(f"batch size must be 1 to {MAX_BATCH}")
        self.snap = snap
        self.now = now
        self.pass_name = pass_name
        self.post_order = post_order
        self.seed = seed if post_order == "random" else None
        self.tool = tool
        self.post_panel = post_panel
        self.root = root
        self.corpus_version = safe_name(corpus_version)
        self.corpus_set = safe_name(corpus_set)
        out_dir = root / LABEL_ROOT / self.corpus_version
        self.labels_path = out_dir / f"{pass_name}.jsonl"
        self.batches_path = out_dir / "batches.jsonl"
        done = _labeled_ids(self.labels_path)
        self.done_before = len(done)
        allowed = only_ids
        if pass_name == CALIBRATION_PASS:
            initial = _labeled_ids(out_dir / "initial.jsonl")
            allowed = initial if only_ids is None else initial & only_ids
        self.queue = [
            c
            for c in snap.subjects(post_order=post_order, seed=seed)
            if c.source_object_id not in done and (allowed is None or c.source_object_id in allowed)
        ]
        self.items = self.queue[:batch_size]
        self.ctx: LabelContext | None = None
        self.saved = 0
        self.skipped = 0
        self.ended_by: str | None = None

    def start(self) -> LabelContext:
        """Write the batch start record.

        :returns: The batch-wide label fields.
        """
        started = self.now()
        # A batch started within the same second as an earlier one (the browser's
        # "next batch") gets a suffix, so batch IDs stay unique.
        used = _batch_ids(self.batches_path)
        batch_id = base = f"b_{_stamp(started)}"
        n = 1
        while batch_id in used:
            n += 1
            batch_id = f"{base}_{n}"
        self.ctx = LabelContext(
            snapshot_run_id=self.snap.obs.run_id,
            corpus_version=self.corpus_version,
            corpus_set=self.corpus_set,
            pass_name=self.pass_name,
            batch_id=batch_id,
        )
        record: dict[str, Any] = {
            "event": "batch_start",
            "batch_id": self.ctx.batch_id,
            "pass": self.pass_name,
            "snapshot_run_id": self.ctx.snapshot_run_id,
            "mode": "label",
            "tool": self.tool,
            "post_panel": self.post_panel,
            "planned": len(self.items),
            "post_order": self.post_order,
            "started_at": _utc(started),
        }
        if self.seed is not None:
            record["seed"] = self.seed
        _append_jsonl(self.batches_path, record)
        return self.ctx

    def context(self) -> LabelContext:
        """Return the batch-wide label fields of a started batch.

        :returns: The context.
        :raises RuntimeError: If the batch has not been started.
        """
        if self.ctx is None:
            raise RuntimeError("batch not started")
        return self.ctx

    def save(self, record: dict[str, Any]) -> None:
        """Append one label.

        :param record: A record from :func:`make_label`.
        """
        self.context()
        _append_jsonl(self.labels_path, record)
        self.saved += 1

    def skip(self) -> None:
        """Count one comment passed over without a label."""
        self.skipped += 1

    def note(self, c: ObservedComment, note: str) -> None:
        """Append a hard-to-label note to the batch record (never to the label).

        :param c: The comment the note is about.
        :param note: Free text; empty notes are ignored.
        """
        if note.strip():
            _append_jsonl(
                self.batches_path,
                {
                    "event": "note",
                    "batch_id": self.context().batch_id,
                    "comment_id": c.source_object_id,
                    "note": note.strip(),
                },
            )

    def end(self, ended_by: str, *, abandoned_in_progress: bool | None = None) -> None:
        """Write the batch end record, once.

        :param ended_by: ``complete`` or ``quit``.
        :param abandoned_in_progress: For the terminal: whether the session stopped
            with answers entered for the comment on screen, which were not saved.
            ``None`` (a transport that cannot tell) leaves the field out.
        """
        if self.ended_by is not None:
            return
        self.ended_by = ended_by
        record: dict[str, Any] = {
            "event": "batch_end",
            "batch_id": self.context().batch_id,
            "ended_at": _utc(self.now()),
            "labeled": self.saved,
            "skipped": self.skipped,
            "ended_by": ended_by,
        }
        if abandoned_in_progress is not None:
            record["abandoned_in_progress"] = abandoned_in_progress
        _append_jsonl(self.batches_path, record)

    def progress(self) -> label_records.LabelProgress:
        """Count progress for this batch's run and corpus version, from disk.

        :returns: Counts from :func:`afterword.label_records.progress`.
        """
        eligible = {c.source_object_id for c in self.snap.subjects()}
        return label_records.progress(
            eligible,
            label_records.read_labels(self.root, self.corpus_version),
            label_records.read_batches(self.root, self.corpus_version),
        )

    @property
    def still_unlabeled(self) -> int:
        """Comments in the queue not labeled in this batch.

        :returns: A count.
        """
        return len(self.queue) - self.saved


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
    A label is written once its summary is confirmed: Enter, or ``q`` (or end of
    input) at the ``Save?`` prompt, which saves and then stops. Stopping at any
    earlier prompt leaves the comment unsaved, and :class:`Abandoned` says
    whether any answer had been entered for it.

    :param console: Terminal.
    :param snap: The run being labeled.
    :param c: The comment to label.
    :param ctx: Batch-wide label fields.
    :param position: Progress text, such as ``3 of 40``.
    :param now: Wall clock for ``labeled_at``.
    :param monotonic: Clock for ``duration_seconds``.
    :returns: The label record, or ``None`` if skipped; and an optional hard-to-label note.
    :raises SavedThenQuit: If ``q`` or end of input confirmed the summary.
    :raises Abandoned: If the session stopped before the summary was confirmed.
    """
    seen = _Seen()
    try:
        return _ask_label(
            console, snap, c, ctx, position=position, now=now, monotonic=monotonic, seen=seen
        )
    except SavedThenQuit:
        raise
    except (Quit, KeyboardInterrupt):
        raise Abandoned(answered=seen.answered) from None


@dataclass
class _Seen:
    """Whether any answer has been entered for the comment on screen."""

    answered: bool = False


def _ask_label(
    console: Console,
    snap: Snapshot,
    c: ObservedComment,
    ctx: LabelContext,
    *,
    position: str,
    now: Callable[[], datetime],
    monotonic: Callable[[], float],
    seen: _Seen,
) -> tuple[dict[str, Any] | None, str]:
    started = monotonic()
    full = False
    console.say(render(snap, c, position=position, full_thread=full))
    structural = snap.structural_flags(c)
    while True:
        console.say("Primary class (TAXONOMY.md precedence order):\n" + _menu(CLASSES))
        while True:
            answer = console.ask(
                f"Class [1-{len(CLASSES)}], h = help, t = toggle full thread, s = skip: "
            )
            if answer.lower() == "h":
                console.say(taxonomy.help_text())
                continue
            if answer.lower() == "t":
                full = not full
                console.say(render(snap, c, position=position, full_thread=full))
                continue
            if answer.lower() == "s":
                return None, ""
            if answer.isdigit() and 1 <= int(answer) <= len(CLASSES):
                primary = CLASSES[int(answer) - 1]
                seen.answered = True
                break
            console.say("  Not understood, try again.")

        auto = f"  (Set automatically: {', '.join(structural)}.)"
        console.say("Flags:\n" + _menu(LABELER_FLAGS) + ("\n" + auto if structural else ""))
        flags = _ask_valid(
            console,
            "Flags [numbers, comma-separated; Enter for none; h = help]: ",
            _flags,
            help_text=taxonomy.help_text(),
        )
        prospective = _ask_valid(
            console,
            "Prospective grade, as of when it was posted [0-3]: ",
            lambda a: _grade(a, optional=False),
        )
        assert prospective is not None  # not optional
        retrospective = _ask_valid(
            console,
            "Retrospective grade, with hindsight [0-3; Enter to skip]: ",
            lambda a: _grade(a, optional=True),
        )
        needs_reason = prospective >= 2
        reason_prompt = "Reason (one line, required for grade 2 or 3): "
        reason = console.ask(reason_prompt if needs_reason else "Reason (optional): ")
        while needs_reason and not reason:
            reason = console.ask(reason_prompt)
        note = console.ask(
            "Hard to label? Note for the session notes (optional, not stored in the label): "
        )

        all_flags = structural + flags
        retro = "skipped" if retrospective is None else str(retrospective)
        console.say(
            f"\n  {primary} | flags: {', '.join(all_flags) or 'none'} | "
            f"prospective {prospective} | retrospective {retro}"
        )
        try:
            decision = console.ask(
                "Save? [Enter = yes, r = redo, s = skip, q = save and stop]: "
            ).lower()
        except Quit:
            decision = "q"
        if decision == "r":
            continue
        if decision == "s":
            return None, note
        break

    record = make_label(
        snap,
        c,
        ctx,
        primary=primary,
        flags=flags,
        prospective=prospective,
        retrospective=retrospective,
        reason=reason,
        duration_seconds=monotonic() - started,
        labeled_at=now(),
    )
    if decision == "q":
        raise SavedThenQuit(record, note)
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
    post_order: str = "published",
    seed: int | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    monotonic: Callable[[], float] = time.monotonic,
) -> int:
    """Label one batch of comments not yet labeled in this pass, in the terminal, then stop.

    Every confirmed label is written before the next comment is shown. When
    the batch ends, by completion or by ``q``, the closing lines say what
    happened to the comment on screen and how far the pass has come, as counts
    only (:func:`afterword.label_records.progress`).

    :param snap: The run to label from.
    :param console: Terminal.
    :param root: Repository root; outputs go under ``fixtures/labels/``.
    :param pass_name: ``initial``, ``calibration``, or ``self_agreement``.
    :param corpus_version: Output directory name and label field.
    :param corpus_set: Label field: ``dev`` for historical comments, ``test`` for prospective ones.
    :param batch_size: At most :data:`MAX_BATCH`.
    :param only_ids: Restrict to these comment IDs, such as a self-agreement sample.
    :param post_order: ``published`` or ``random``.
    :param seed: Seed for ``random``.
    :param now: Wall clock.
    :param monotonic: Clock for durations.
    :returns: Number of labels saved in this batch.
    """
    batch = LabelBatch(
        snap,
        root=root,
        pass_name=pass_name,
        corpus_version=corpus_version,
        corpus_set=corpus_set,
        batch_size=batch_size,
        only_ids=only_ids,
        post_order=post_order,
        seed=seed,
        now=now,
    )
    if not batch.items:
        console.say(
            f"Nothing left to label in pass {pass_name} ({batch.done_before} already labeled)."
        )
        return 0
    ctx = batch.start()
    console.say(
        f"Batch {ctx.batch_id}: {len(batch.items)} comments ({len(batch.queue)} unlabeled, "
        f"{batch.done_before} done). q stops: at Save? it saves first; at any earlier "
        "prompt the comment on screen is not saved. Saved labels are kept."
    )
    ended_by = "complete"
    abandoned = False
    closing = ""
    current = batch.items[0]
    try:
        for i, c in enumerate(batch.items, start=1):
            current = c
            record, note = label_one(
                console,
                snap,
                c,
                ctx,
                position=f"{i} of {len(batch.items)}",
                now=now,
                monotonic=monotonic,
            )
            batch.note(c, note)
            if record is None:
                batch.skip()
                continue
            batch.save(record)
    except SavedThenQuit as stop:
        batch.note(current, stop.note)
        batch.save(stop.record)
        ended_by = "quit"
        closing = "The comment on screen was saved before stopping."
    except Abandoned as stop:
        ended_by = "quit"
        abandoned = stop.answered
        closing = (
            "The comment on screen was NOT saved: the answers entered for it were discarded. "
            "It comes back in a later batch."
            if stop.answered
            else "The comment on screen was not labeled. It comes back in a later batch."
        )
    except (Quit, KeyboardInterrupt):
        ended_by = "quit"
    batch.end(ended_by, abandoned_in_progress=abandoned)
    if closing:
        console.say("\n" + closing)
    console.say(
        f"\nBatch {ctx.batch_id} ended ({ended_by}): {batch.saved} labeled, {batch.skipped} "
        f"skipped, {batch.still_unlabeled} still unlabeled in pass {pass_name}."
    )
    console.say(progress_line(batch))
    return batch.saved


def progress_line(batch: LabelBatch) -> str:
    """Say how far the pass has come after a batch: totals only, no classes or grades.

    :param batch: A batch that has ended.
    :returns: Such as ``12 labeled this session, bringing the total to 162 of 438.``
    """
    counts = batch.progress()
    in_pass = "" if batch.pass_name == "initial" else f" in pass {batch.pass_name}"
    return (
        f"{batch.saved} labeled this session, bringing the total{in_pass} to "
        f"{counts.by_pass[batch.pass_name]} of {counts.eligible}."
    )


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
