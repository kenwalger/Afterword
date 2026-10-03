"""Application service layer (ADR-012): the single entry point for every frontend.

Frontends (the CLI now; a review UI or other transports later) call these
functions and format what they return. They never read storage, call adapters,
or apply policy themselves. Errors a caller should show are raised as
:class:`ServiceError`, whose message is safe to print: counts, IDs, and paths
only, never comment text, names, handles, or the API key.

Adopted incrementally: the Stage 0 commands moved here when they were next
changed (session 3: probe progress, timing validity, and the review-time
section of the baseline).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from afterword import baseline, labeling, timing
from afterword.adapters.dev import records
from afterword.adapters.dev.client import ENV_VAR, DevClient, MissingCredentialError
from afterword.adapters.dev.probe import (
    FINDINGS_FILE,
    INDEX_FILE,
    Probe,
    ProbeLockedError,
    probe_lock,
)

RAW_ROOT: Path = Path("fixtures/dev-api/source/real")
REPORT_ROOT: Path = Path("reports")
LOCK_FILE: str = ".probe.lock"


class ServiceError(Exception):
    """A failure the caller should report. The message is safe to print."""

    def __init__(self, message: str, *, code: int = 2) -> None:
        """Create an error.

        :param message: Printable explanation.
        :param code: Suggested process exit status for command-line callers.
        """
        super().__init__(message)
        self.code = code


# Probe ------------------------------------------------------------------------------


@dataclass(frozen=True)
class ProbeHooks:
    """Progress callbacks for a probe run. Each receives counts only."""

    request: Callable[[], None] | None = None
    wait: Callable[[int, float], None] | None = None
    step: Callable[[str, int, int], None] | None = None
    started: Callable[[str], object] | None = None
    finished: Callable[[str], object] | None = None


@dataclass(frozen=True)
class ProbeResult:
    """The outcome of one probe run."""

    run_id: str
    findings: dict[str, Any]
    findings_path: Path


def _run_dirs(root: Path) -> list[Path]:
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []


def _resolve_compare(root: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    probe_reports = root / REPORT_ROOT / "probe"
    if value == "latest":
        candidates = [p for p in _run_dirs(probe_reports) if (p / INDEX_FILE).exists()]
        if not candidates:
            raise ServiceError("--compare-to latest: no earlier run with a comment index")
        return candidates[-1]
    path = probe_reports / value
    if not (path / INDEX_FILE).exists():
        raise ServiceError(f"--compare-to: no comment index for run {value}")
    return path


def run_probe(
    root: Path,
    *,
    article: str | None = None,
    compare_to: str | None = None,
    page_size: int = 10,
    min_interval: float = 1.0,
    hooks: ProbeHooks | None = None,
) -> ProbeResult:
    """Run the read-only DEV probe and save its outputs.

    :param root: Repository root.
    :param article: Limit to one article, by numeric ID or URL; ``None`` probes everything.
    :param compare_to: Earlier run ID to diff against, or ``latest``.
    :param page_size: Small page size used to walk the article listing.
    :param min_interval: Minimum seconds between requests.
    :param hooks: Progress callbacks; ``started`` and ``finished`` receive the run ID.
    :returns: The run ID, its findings, and where they were written.
    :raises ServiceError: If the comparison run is missing (code 2), the key is
        not set (code 2), or another probe holds the lock (code 3).
    """
    hooks = hooks or ProbeHooks()
    compare = _resolve_compare(root, compare_to)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = root / REPORT_ROOT / "probe" / run_id
    try:
        client = DevClient.from_env(
            min_interval=min_interval, on_request=hooks.request, backoff_wait=hooks.wait
        )
    except MissingCredentialError:
        raise ServiceError(f"{ENV_VAR} is not set. It is read from the environment only.") from None
    lock = root / REPORT_ROOT / "probe" / LOCK_FILE
    try:
        with probe_lock(lock), client:
            probe = Probe(
                client,
                root / RAW_ROOT / run_id,
                report_dir,
                run_id=run_id,
                page_size=page_size,
                progress=hooks.step,
            )
            if hooks.started is not None:
                hooks.started(run_id)
            try:
                findings = probe.run(article=article, compare_to=compare)
            finally:
                if hooks.finished is not None:
                    hooks.finished(run_id)
    except ProbeLockedError:
        raise ServiceError(
            f"another probe is running (lock file {lock}). "
            "If no probe is running, delete the lock file and retry.",
            code=3,
        ) from None
    return ProbeResult(run_id, findings, report_dir / FINDINGS_FILE)


# Saved runs -------------------------------------------------------------------------


def _full_run_problem(root: Path, run_id: str) -> str | None:
    """Say why a saved run cannot be used, or ``None`` if it is a full run that did not fail."""
    run_file = root / RAW_ROOT / run_id / records.RUN_FILE
    if not run_file.exists():
        return f"no probe run {run_id}"
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if run.get("scope") != "all" or run.get("outcome") == "FAILED":
        return (
            f"run {run_id} is scope {run.get('scope')}, outcome {run.get('outcome')}; "
            "this needs a full-scope run that did not fail"
        )
    return None


# Baseline ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaselineResult:
    """The C-009 baseline report and where it was written."""

    report: dict[str, Any]
    markdown_path: Path
    json_path: Path


def build_baseline(
    root: Path, run_id: str, *, exclude_weeks: Iterable[date] = ()
) -> BaselineResult:
    """Compute the C-009 baseline from an explicit full-scope run and write it.

    The run is always explicit, so a run containing test comments is never
    picked up by default; the report records which run it came from. Review
    times come only from timings confirmed as valid; practice is ignored.

    :param root: Repository root.
    :param run_id: Full-scope probe run ID.
    :param exclude_weeks: Weeks that may not be named as the replacement typical
        week (weeks already re-read); empty means no replacement is named.
    :returns: The report and the paths of its Markdown and JSON forms.
    :raises ServiceError: If the run is missing, scoped, or failed.
    """
    problem = _full_run_problem(root, run_id)
    if problem:
        raise ServiceError(problem)
    obs = records.load_run(root / RAW_ROOT / run_id)
    as_of = (obs.finished_at or datetime.now(UTC)).date()
    report = baseline.build(
        obs, as_of=as_of, review_timing=timing.load_valid(root), exclude_weeks=exclude_weeks
    )
    md = root / REPORT_ROOT / f"baseline-{obs.run_id}.md"
    js = root / REPORT_ROOT / f"baseline-{obs.run_id}.json"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(baseline.render_markdown(report), encoding="utf-8")
    js.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return BaselineResult(report, md, js)


# Labeling and timing ----------------------------------------------------------------


@dataclass(frozen=True)
class LabelingSession:
    """A saved run opened for labeling or timing, with what the caller should warn about."""

    snapshot: labeling.Snapshot
    age: timedelta | None
    stale: bool
    subjects: int
    excluded: dict[str, int] = field(default_factory=dict)


def open_for_labeling(
    root: Path, run_id: str, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)
) -> LabelingSession:
    """Load a full-scope run with text for the author's labeling terminal.

    :param root: Repository root.
    :param run_id: Full-scope probe run ID.
    :param now: Wall clock, for the run's age.
    :returns: The snapshot, its age, whether it is too old to label from (ADR-009),
        and counts of labelable and excluded comments.
    :raises ServiceError: If the run is missing, scoped, or failed.
    """
    problem = _full_run_problem(root, run_id)
    if problem:
        raise ServiceError(problem)
    snap = labeling.Snapshot(records.load_run(root / RAW_ROOT / run_id, include_text=True))
    finished = snap.obs.finished_at
    age = None if finished is None else now() - finished
    return LabelingSession(
        snapshot=snap,
        age=age,
        stale=age is None or age > labeling.STALE_AFTER,
        subjects=len(snap.subjects()),
        excluded=snap.excluded_counts(),
    )


def time_week(
    session: LabelingSession, console: labeling.Console, *, root: Path, week: date
) -> Path | None:
    """Time a chronological review of one week (C-009), asking at the end whether it is valid.

    :param session: An opened run.
    :param console: Terminal.
    :param root: Repository root.
    :param week: Any date in the week.
    :returns: The timing record's path (valid or practice), or ``None`` for an empty week.
    """
    return labeling.run_chronological(session.snapshot, console, root=root, week=week)


def label_batch(
    session: LabelingSession,
    console: labeling.Console,
    *,
    root: Path,
    pass_name: str,
    corpus_version: str,
    corpus_set: str,
    batch_size: int,
    only_ids: set[str] | None,
) -> int:
    """Label one batch of comments not yet labeled in a pass.

    :param session: An opened run.
    :param console: Terminal.
    :param root: Repository root.
    :param pass_name: ``initial`` or ``self_agreement``.
    :param corpus_version: Output directory name and label field.
    :param corpus_set: ``dev`` or ``test``.
    :param batch_size: Comments in the batch, at most :data:`afterword.labeling.MAX_BATCH`.
    :param only_ids: Restrict to these comment IDs.
    :returns: Number of labels saved.
    """
    return labeling.run_labeling(
        session.snapshot,
        console,
        root=root,
        pass_name=pass_name,
        corpus_version=corpus_version,
        corpus_set=corpus_set,
        batch_size=batch_size,
        only_ids=only_ids,
    )


def labelable_ids(session: LabelingSession) -> set[str]:
    """Return the IDs of comments that can be labeled from a run.

    :param session: An opened run.
    :returns: Comment IDs.
    """
    return {c.source_object_id for c in session.snapshot.subjects()}
