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

import hashlib
import json
import random
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from afterword import (
    baseline,
    bench,
    classifier,
    domain,
    heuristic,
    label_records,
    labeling,
    lifecycle,
    normalize,
    policy,
    precheck,
    scoring,
    taxonomy,
    timing,
)
from afterword.adapters.dev import records
from afterword.adapters.dev import sync as dev_sync
from afterword.adapters.dev.client import ENV_VAR, DevClient, MissingCredentialError
from afterword.adapters.dev.probe import (
    FINDINGS_FILE,
    INDEX_FILE,
    Probe,
    ProbeLockedError,
    probe_lock,
)
from afterword.providers import (
    ModelIdentity,
    ModelVerificationError,
    Provider,
    ProviderError,
    anthropic,
    ollama,
)
from afterword.repository import Repository
from afterword.sqlite_store import SqliteRepository

RAW_ROOT: Path = Path("fixtures/dev-api/source/real")
# The local store (git-ignored). It holds real comment text once the author ingests.
STORE_PATH: Path = Path("data/afterword.sqlite3")
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
    post_order: str = "published",
    seed: int | None = None,
) -> int:
    """Label one batch of comments not yet labeled in a pass, in the terminal.

    :param session: An opened run.
    :param console: Terminal.
    :param root: Repository root.
    :param pass_name: ``initial``, ``calibration``, or ``self_agreement``.
    :param corpus_version: Output directory name and label field.
    :param corpus_set: ``dev`` or ``test``.
    :param batch_size: Comments in the batch, at most :data:`afterword.labeling.MAX_BATCH`.
    :param only_ids: Restrict to these comment IDs.
    :param post_order: ``published`` or ``random``.
    :param seed: Seed for ``random``.
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
        post_order=post_order,
        seed=seed,
    )


def labelable_ids(session: LabelingSession) -> set[str]:
    """Return the IDs of comments that can be labeled from a run.

    :param session: An opened run.
    :returns: Comment IDs.
    """
    return {c.source_object_id for c in session.snapshot.subjects()}


def label_progress(
    session: LabelingSession, *, root: Path, corpus_version: str
) -> label_records.LabelProgress:
    """Count labeling progress for a run: totals only, never classes or grades.

    The one count behind ``afterword label status``, the terminal tool's closing
    line, and the label UI's badge. Eligibility is the labeling tools' own.

    :param session: An opened run.
    :param root: Repository root.
    :param corpus_version: Which labels to count.
    :returns: Labeled, remaining, relabeled, and counts by pass and by tool.
    :raises ServiceError: If the corpus version is not a safe name.
    """
    try:
        labeling.safe_name(corpus_version)
    except ValueError as exc:
        raise ServiceError(str(exc), code=2) from None
    return label_records.progress(
        labelable_ids(session),
        label_records.read_labels(root, corpus_version),
        label_records.read_batches(root, corpus_version),
    )


def start_label_batch(
    session: LabelingSession,
    *,
    root: Path,
    pass_name: str,
    corpus_version: str,
    corpus_set: str,
    batch_size: int,
    only_ids: set[str] | None,
    post_order: str = "published",
    seed: int | None = None,
) -> labeling.LabelBatch | None:
    """Choose and start one labeling batch, for a transport other than the terminal.

    The batch, its order, and its records are the same as ``afterword label``;
    its batch record names the transport as ``browser`` and records whether the
    post panel was available (the run captured post bodies).

    :param session: An opened run.
    :param root: Repository root.
    :param pass_name: ``initial``, ``calibration``, or ``self_agreement``.
    :param corpus_version: Output directory name and label field.
    :param corpus_set: ``dev`` or ``test``.
    :param batch_size: Comments in the batch, at most :data:`afterword.labeling.MAX_BATCH`.
    :param only_ids: Restrict to these comment IDs.
    :param post_order: ``published`` or ``random``.
    :param seed: Seed for ``random``.
    :returns: The started batch, or ``None`` when nothing is left to label.
    """
    batch = labeling.LabelBatch(
        session.snapshot,
        root=root,
        pass_name=pass_name,
        corpus_version=corpus_version,
        corpus_set=corpus_set,
        batch_size=batch_size,
        only_ids=only_ids,
        post_order=post_order,
        seed=seed,
        tool="browser",
        post_panel=session.snapshot.has_post_bodies(),
    )
    if not batch.items:
        return None
    batch.start()
    return batch


def label_view(batch: labeling.LabelBatch, index: int) -> dict[str, Any]:
    """Describe one comment of a batch and its as-of context.

    :param batch: A started batch.
    :param index: Position in the batch, from 0.
    :returns: JSON-ready view (:func:`afterword.labeling.comment_view`).
    """
    return labeling.comment_view(batch.snap, batch.items[index])


def post_view(batch: labeling.LabelBatch, index: int) -> dict[str, Any]:
    """Describe the post of one comment of a batch, for the label UI's post panel.

    :param batch: A started batch.
    :param index: Position in the batch, from 0.
    :returns: JSON-ready view (:func:`afterword.labeling.post_view`).
    """
    return labeling.post_view(batch.snap, batch.items[index])


def save_label(
    batch: labeling.LabelBatch,
    index: int,
    *,
    primary: str,
    flags: list[str],
    prospective: int,
    retrospective: int | None,
    reason: str,
    note: str,
    duration_seconds: float,
    read_via_translation: bool = False,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> dict[str, Any]:
    """Save the label for one comment of a batch, and its hard-to-label note if any.

    :param batch: A started batch.
    :param index: Position in the batch, from 0.
    :param primary: Primary class.
    :param flags: Labeler-chosen flags.
    :param prospective: Grade 0 to 3.
    :param retrospective: Grade 0 to 3, or ``None`` when skipped.
    :param reason: Required for a prospective grade of 2 or 3.
    :param note: Optional note for the batch record, never stored in the label.
    :param duration_seconds: Time from the comment being shown to saving.
    :param read_via_translation: The labeler read the comment through a translation.
    :param now: Wall clock for ``labeled_at``.
    :returns: The saved record.
    :raises ServiceError: If the label is invalid (see :func:`afterword.labeling.make_label`).
    """
    c = batch.items[index]
    try:
        record = labeling.make_label(
            batch.snap,
            c,
            batch.context(),
            primary=primary,
            flags=flags,
            prospective=prospective,
            retrospective=retrospective,
            reason=reason,
            duration_seconds=duration_seconds,
            labeled_at=now(),
            read_via_translation=read_via_translation,
        )
    except ValueError as exc:
        raise ServiceError(str(exc)) from None
    batch.note(c, note)
    batch.save(record)
    return record


def skip_label(batch: labeling.LabelBatch, index: int, *, note: str) -> None:
    """Pass over one comment of a batch without a label, keeping any note.

    :param batch: A started batch.
    :param index: Position in the batch, from 0.
    :param note: Optional note for the batch record.
    """
    batch.note(batch.items[index], note)
    batch.skip()


def end_label_batch(batch: labeling.LabelBatch, *, ended_by: str) -> None:
    """Write a batch's end record (once).

    :param batch: A started batch.
    :param ended_by: ``complete`` or ``quit``.
    """
    batch.end(ended_by)


# Store: ingest and forget (ADR-009, ADR-013) ---------------------------------------


def open_store(root: Path) -> Repository:
    """Open the local store, creating it on first use.

    :param root: Repository root; the store is the git-ignored :data:`STORE_PATH`.
    :returns: The repository.
    """
    return SqliteRepository(root / STORE_PATH)


@dataclass(frozen=True)
class IngestResult:
    """What one ingest did. Counts and IDs only, safe to print."""

    connection_id: str
    created_connection: bool
    sync_run_id: str
    counts: dict[str, int]
    limitations: tuple[str, ...]


def ingest_run(
    root: Path, run_id: str, *, now: Callable[[], datetime] = lambda: datetime.now(UTC)
) -> IngestResult:
    """Ingest one saved probe run into the store, applying the lifecycle rules and the purge.

    Runs are ingested oldest first, each once. The connection is the one for the
    run's account; it is created on first ingest.

    :param root: Repository root.
    :param run_id: Probe run ID.
    :param now: Wall clock.
    :returns: The connection, counts by lifecycle outcome, and limitations.
    :raises ServiceError: If the run is missing or failed, names no account, was
        already ingested, or finished before the last ingested run.
    """
    run_dir = root / RAW_ROOT / run_id
    if not (run_dir / records.RUN_FILE).exists():
        raise ServiceError(f"no probe run {run_id}")
    obs = dev_sync.load_sync(run_dir)
    if obs.outcome == "FAILED":
        raise ServiceError(f"run {run_id} failed; nothing to ingest")
    if obs.account_source_user_id is None:
        raise ServiceError(f"run {run_id} has no account ID; cannot choose a connection")
    repo = open_store(root)
    try:
        with repo.transaction():
            connection = repo.find_connection(obs.platform, obs.account_source_user_id)
            created = connection is None
            if connection is None:
                connection = domain.PlatformConnection(
                    domain.new_id(), obs.platform, obs.account_source_user_id, domain.utc(now())
                )
                repo.add_connection(connection)
            cid = connection.connection_id
            if repo.get_sync_run(cid, run_id) is not None:
                raise ServiceError(f"run {run_id} is already ingested")
            latest = repo.latest_sync_run(cid)
            if (
                latest is not None
                and latest.finished_at is not None
                and obs.finished_at is not None
                and obs.finished_at <= latest.finished_at
            ):
                raise ServiceError(
                    f"run {run_id} finished before the last ingested run {latest.sync_run_id}; "
                    "runs are ingested oldest first"
                )
            content_ids = {c.source_object_id for c in obs.contents}
            plan = lifecycle.plan_sync(
                obs,
                connection_id=cid,
                existing_comments=repo.comments(cid, content_ids=content_ids),
                existing_contents=repo.contents(cid),
                now=now(),
            )
            repo.add_sync_run(plan.sync_run)
            repo.put_identities(plan.identities)
            repo.add_source_records(plan.source_records)
            repo.put_contents(plan.contents)
            repo.put_comments(plan.comments)
            repo.add_lifecycle_events(plan.events)
            purged_at = domain.utc(now())
            for comment_id, keep in plan.purges:
                repo.purge_source_records(cid, comment_id, keep=keep, purged_at=purged_at)
                repo.purge_classifications(cid, comment_id)
    finally:
        repo.close()
    return IngestResult(
        connection_id=cid,
        created_connection=created,
        sync_run_id=run_id,
        counts=dict(plan.counts),
        limitations=plan.sync_run.limitations_observed,
    )


@dataclass(frozen=True)
class ConnectionSummary:
    """A connection and how many records it holds."""

    connection: domain.PlatformConnection
    counts: dict[str, int]


def list_connections(root: Path) -> list[ConnectionSummary]:
    """List the store's connections with their record counts.

    :param root: Repository root.
    :returns: Connections, oldest first.
    """
    repo = open_store(root)
    try:
        return [
            ConnectionSummary(c, repo.count_connection(c.connection_id))
            for c in repo.list_connections()
        ]
    finally:
        repo.close()


def store_status(root: Path, connection_id: str | None = None) -> dict[str, dict[str, int]]:
    """Count a connection's comments by lifecycle state and its lifecycle events.

    :param root: Repository root.
    :param connection_id: Connection ID; ``None`` when the store has exactly one.
    :returns: Counts only (:meth:`afterword.repository.Repository.lifecycle_counts`).
        An unknown or ambiguous connection raises :class:`ServiceError`.
    """
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        return repo.lifecycle_counts(cid)
    finally:
        repo.close()


def forget_connection(root: Path, connection_id: str, *, confirm: bool) -> dict[str, int]:
    """Remove all local data for one connection (``PRIVACY-AND-BOUNDARIES.md``).

    :param root: Repository root.
    :param connection_id: Connection ID.
    :param confirm: ``False`` only counts what would be deleted.
    :returns: Rows deleted (or that would be), by record type.
    :raises ServiceError: If the connection does not exist.
    """
    repo = open_store(root)
    try:
        if repo.get_connection(connection_id) is None:
            raise ServiceError(f"no connection {connection_id}")
        if not confirm:
            return repo.count_connection(connection_id)
        return repo.forget_connection(connection_id)
    finally:
        repo.close()


# Classification (Stage 3a groundwork) ------------------------------------------------

# Model-boundary paths the author has signed off (PRIVACY-AND-BOUNDARIES.md). Only
# these may receive comments from the store. Path B (Anthropic) is not signed off.
SIGNED_OFF_PATHS: frozenset[str] = frozenset({ollama.PROVIDER})
PROVIDERS: tuple[str, ...] = (ollama.PROVIDER, anthropic.PROVIDER)
CONDITIONS: tuple[str, ...] = ("b1", "b2")


def make_provider(name: str, model: str | None, *, host: str = ollama.DEFAULT_HOST) -> Provider:
    """Create a model provider.

    :param name: ``ollama`` or ``anthropic``.
    :param model: Model ID; required for Ollama, defaults to the pinned ID for Anthropic.
    :param host: Ollama base URL (loopback only).
    :returns: The provider, not yet verified.
    :raises ServiceError: For an unknown provider or model, a non-loopback host, or a
        missing Anthropic key.
    """
    try:
        if name == ollama.PROVIDER:
            if not model:
                approved = ", ".join(ollama.PINNED_DIGESTS)
                raise ServiceError(f"--model is required; approved: {approved}")
            return ollama.OllamaProvider(model, host=host)
        if name == anthropic.PROVIDER:
            return anthropic.AnthropicProvider.from_env(model=model or anthropic.DEFAULT_MODEL)
    except ModelVerificationError as exc:
        raise ServiceError(str(exc)) from None
    except anthropic.MissingCredentialError:
        raise ServiceError(
            f"{anthropic.ENV_VAR} is not set. It is read from the environment only."
        ) from None
    raise ServiceError(f"unknown provider: {name}")


def _verify(provider: Provider) -> ModelIdentity:
    try:
        return provider.verify()
    except ModelVerificationError as exc:
        raise ServiceError(str(exc), code=3) from None
    except ProviderError as exc:
        raise ServiceError(f"cannot reach the model provider ({exc.kind})", code=3) from None


@dataclass(frozen=True)
class ModelCheck:
    """One pinned model checked against what is installed."""

    model: str
    pinned: str
    installed: str | None
    status: str


def verify_models(*, host: str = ollama.DEFAULT_HOST) -> list[ModelCheck]:
    """Check every approved Ollama model's installed digest against its pin.

    :param host: Ollama base URL (loopback only).
    :returns: One check per approved model: ``OK``, ``MISMATCH``, or ``MISSING``.
    :raises ServiceError: If Ollama cannot be reached or the host is not loopback.
    """
    checks = []
    for model, pinned in ollama.PINNED_DIGESTS.items():
        try:
            provider = ollama.OllamaProvider(model, host=host)
        except ModelVerificationError as exc:
            raise ServiceError(str(exc)) from None
        try:
            installed = provider.installed_digest()
        except ProviderError as exc:
            raise ServiceError(f"cannot reach Ollama ({exc.kind})", code=3) from None
        finally:
            provider.close()
        status = "MISSING" if installed is None else ("OK" if installed == pinned else "MISMATCH")
        checks.append(ModelCheck(model, pinned, installed, status))
    return checks


@dataclass(frozen=True)
class ClassifyResult:
    """What one classification run did. Counts only, safe to print."""

    connection_id: str
    condition: str
    model_provider: str
    model_id: str
    model_digest: str | None
    subjects: int
    reused: int
    classified: int
    outcomes: dict[str, int]
    errors: dict[str, int]
    tiers: dict[str, int]


def _pick_connection(repo: Repository, connection_id: str | None) -> str:
    if connection_id is not None:
        if repo.get_connection(connection_id) is None:
            raise ServiceError(f"no connection {connection_id}")
        return connection_id
    connections = repo.list_connections()
    if len(connections) != 1:
        raise ServiceError(
            f"{len(connections)} connections in the store; name one with --connection"
        )
    return connections[0].connection_id


def _union(by_source: dict[str, list[str]]) -> tuple[str, ...]:
    return tuple(f for f in taxonomy.FLAGS if any(f in v for v in by_source.values()))


def structural_flags(c: domain.Comment, *, reply_to_author: bool) -> list[str]:
    """Return the flags a comment carries by structure, the same for B1 and B2.

    ``REPLY_TO_AUTHOR`` from the thread, and, from `tax-v0.2`, ``CONTAINS_CODE``
    and ``CONTAINS_LINK`` from the comment's normalization. Neither condition
    sets them by judgment.

    :param c: A stored comment with its source body.
    :param reply_to_author: Whether its parent was written by the post's author.
    :returns: Flag names in taxonomy order.
    """
    found = set(
        normalize.content_flags(normalize.normalize(c.body_source, c.body_source_format or "HTML"))
    )
    if reply_to_author:
        found.add(taxonomy.REPLY_TO_AUTHOR)
    return [f for f in taxonomy.FLAGS if f in found]


@dataclass(frozen=True)
class _Subject:
    """A comment from others to classify, with exactly what its classifiers receive."""

    comment: domain.Comment
    inp: classifier.ClassifierInput
    extra: dict[str, list[str]]


def _subjects(repo: Repository, cid: str) -> list[_Subject]:
    """List the live comments from others with their classifier input and fixed flags.

    Author comments, deleted comments, and placeholders are never subjects
    (ADR-011, ADR-009). ``extra`` holds the structural flags and the pre-check's
    flag, the same for B1 and B2.
    """
    comments = repo.comments(cid)
    contents = repo.contents(cid)
    out = []
    for c in comments.values():
        if not (
            c.is_content_author is False
            and c.lifecycle_state in (domain.ACTIVE, domain.EDITED)
            and c.body_text is not None
        ):
            continue
        parent = comments.get(c.parent_comment_id) if c.parent_comment_id else None
        parent_text = None
        if c.parent_comment_id is not None:
            parent_text = (parent.body_text if parent else None) or ""
        reply_to_author = bool(
            parent and parent.is_content_author and parent.is_content_author_state == domain.PRESENT
        )
        content = contents.get(c.content_id)
        inp = classifier.build_input(
            post_title=content.title if content else None,
            comment=c.body_text or "",
            parent=parent_text,
            reply_to_author=reply_to_author,
        )
        pre = precheck.precheck(inp.comment)
        extra = {
            "structure": structural_flags(c, reply_to_author=reply_to_author),
            "precheck": [taxonomy.POSSIBLE_INSTRUCTION_TEXT] if pre.flagged else [],
        }
        out.append(_Subject(c, inp, extra))
    return out


def _b1_hash(inp: classifier.ClassifierInput) -> str:
    # B1 sees the comment only, so only the comment is in its key.
    canonical = json.dumps({"comment": inp.comment}, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _b1(
    cid: str,
    c: domain.Comment,
    key: domain.CacheKey,
    extra: dict[str, list[str]],
    now: datetime,
) -> domain.Classification:
    normalized = normalize.normalize(c.body_source, c.body_source_format or "HTML")
    result = heuristic.classify(normalized, key.model_id)
    by_source = {"heuristic": sorted(result.flags)} | extra
    return domain.Classification(
        classification_id=domain.new_id(),
        connection_id=cid,
        comment_id=c.comment_id,
        comment_source_record_id=c.current_source_record_id,
        key=key,
        primary_class=result.primary_class,
        flags=_union(by_source),
        flags_by_source=by_source,
        confidence=None,
        confidence_state=domain.NOT_EXPOSED,
        explanation=result.explanation,
        classifier_kind=domain.HEURISTIC,
        model_digest_state=domain.NOT_EXPOSED,
        normalization_version=normalized.version,
        precheck_version=precheck.PRECHECK_VERSION,
        input_fields_sent=("comment",),
        raw_output=None,
        latency_ms=None,
        classified_at=domain.utc(now),
        outcome=domain.OK,
    )


def _b2(
    cid: str,
    c: domain.Comment,
    key: domain.CacheKey,
    extra: dict[str, list[str]],
    provider: Provider,
    identity: ModelIdentity,
    inp: classifier.ClassifierInput,
    now: datetime,
) -> domain.Classification:
    result = classifier.classify(provider, inp)
    by_source = {"model": list(result.flags)} | extra
    return domain.Classification(
        classification_id=domain.new_id(),
        connection_id=cid,
        comment_id=c.comment_id,
        comment_source_record_id=c.current_source_record_id,
        key=key,
        primary_class=result.primary_class,
        flags=_union(by_source),
        flags_by_source=by_source,
        confidence=result.confidence,
        confidence_state=domain.PRESENT if result.confidence else domain.NOT_YET_INTERPRETED,
        explanation=result.explanation,
        classifier_kind=domain.MODEL,
        model_digest_state=identity.digest_state,
        normalization_version=c.normalization_version or normalize.NORMALIZATION_VERSION,
        precheck_version=precheck.PRECHECK_VERSION,
        input_fields_sent=inp.fields_sent,
        raw_output=result.raw_output,
        latency_ms=result.latency_ms,
        classified_at=domain.utc(now),
        outcome=result.outcome,
        error=result.error,
    )


def _assign(
    repo: Repository, cid: str, c: domain.Comment, k: domain.Classification, now: datetime
) -> str:
    ok = k.outcome == domain.OK
    decision = policy.assign(
        policy.PolicyInput(
            outcome=k.outcome,
            primary_class=k.primary_class if ok else None,
            flags=frozenset(k.flags),
            confidence=k.confidence if ok else None,
            edited_since_review=c.lifecycle_state == domain.EDITED,
        )
    )
    tier = decision.tier.name
    known = repo.find_priority(
        k.classification_id, decision.policy_version, tier, decision.rules_fired
    )
    if known is None:
        with repo.transaction():
            repo.add_priority_assignment(
                domain.PriorityAssignment(
                    priority_assignment_id=domain.new_id(),
                    connection_id=cid,
                    comment_id=c.comment_id,
                    classification_id=k.classification_id,
                    policy_version=decision.policy_version,
                    tier=tier,
                    rule_applied=decision.rule_applied,
                    rules_fired=decision.rules_fired,
                    assigned_at=domain.utc(now),
                )
            )
    return tier


def classify_comments(
    root: Path,
    *,
    condition: str,
    provider_name: str = ollama.PROVIDER,
    model: str | None = None,
    connection_id: str | None = None,
    host: str = ollama.DEFAULT_HOST,
    heuristic_version: str = heuristic.HEURISTIC_VERSION,
    only_ids: set[str] | None = None,
    progress: Callable[[int, int], None] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> ClassifyResult:
    """Classify the store's comments from others with B1 or B2, then apply the policy.

    Incremental: a comment is classified only when no ``OK`` or ``MALFORMED``
    classification exists for its current cache key; ``FAILED`` is retried.
    Author comments, deleted comments, and placeholders are never classified
    (ADR-011, ADR-009). B2 sends comments only through a signed-off
    model-boundary path, and only after the model's digest is verified.

    :param root: Repository root.
    :param condition: ``b1`` (heuristic) or ``b2`` (model).
    :param provider_name: Model provider for ``b2``.
    :param model: Model ID for ``b2``.
    :param connection_id: Connection; may be omitted when the store has exactly one.
    :param host: Ollama base URL (loopback only).
    :param heuristic_version: Heuristic version for ``b1``.
    :param only_ids: Restrict to these comment IDs, such as a fixed dev subset.
    :param progress: Called with the number done and the total.
    :param now: Wall clock.
    :returns: Counts of reuse, outcomes, errors, and tiers.
    :raises ServiceError: For an unknown condition or heuristic version, an
        unsigned boundary path, a model that fails verification, or an
        ambiguous connection.
    """
    if condition not in CONDITIONS:
        raise ServiceError(f"unknown condition: {condition}")
    if heuristic_version not in heuristic.HEURISTIC_VERSIONS:
        raise ServiceError(f"unknown heuristic version: {heuristic_version}")
    provider: Provider | None = None
    if condition == "b2":
        if provider_name not in SIGNED_OFF_PATHS:
            raise ServiceError(
                f"the {provider_name} model-boundary path is not signed off "
                "(PRIVACY-AND-BOUNDARIES.md); store comments may not be sent to it"
            )
        provider = make_provider(provider_name, model, host=host)
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        if provider is not None:
            identity = _verify(provider)
            prompt_version: str | None = classifier.PROMPT_VERSION
        else:
            identity = ModelIdentity("afterword", heuristic_version, None, domain.NOT_EXPOSED)
            prompt_version = None
        subjects = [
            s for s in _subjects(repo, cid) if only_ids is None or s.comment.comment_id in only_ids
        ]
        reused = 0
        outcomes: Counter[str] = Counter()
        errors: Counter[str] = Counter()
        tiers: Counter[str] = Counter()
        for i, s in enumerate(subjects, start=1):
            c, inp, extra = s.comment, s.inp, s.extra
            hashed = _b1_hash(inp) if provider is None else inp.input_hash
            key = domain.CacheKey(
                hashed,
                identity.provider,
                identity.model_id,
                identity.digest,
                prompt_version,
                taxonomy.TAXONOMY_VERSION,
                None if provider is None else provider.options_key,
            )
            k = repo.find_classification(cid, c.comment_id, key, (domain.OK, domain.MALFORMED))
            if k is not None:
                reused += 1
            else:
                if provider is None:
                    k = _b1(cid, c, key, extra, now())
                else:
                    k = _b2(cid, c, key, extra, provider, identity, inp, now())
                with repo.transaction():
                    repo.add_classification(k)
            outcomes[k.outcome] += 1
            if k.error:
                errors[k.error] += 1
            tiers[_assign(repo, cid, c, k, now())] += 1
            if progress is not None:
                progress(i, len(subjects))
    finally:
        repo.close()
        if provider is not None:
            provider.close()
    return ClassifyResult(
        connection_id=cid,
        condition=condition,
        model_provider=identity.provider,
        model_id=identity.model_id,
        model_digest=identity.digest,
        subjects=len(subjects),
        reused=reused,
        classified=len(subjects) - reused,
        outcomes=dict(outcomes),
        errors=dict(errors),
        tiers=dict(tiers),
    )


# Evaluation on dev labels (Stage 3a) -------------------------------------------------

EVAL_ROOT: Path = REPORT_ROOT / "eval"


@dataclass(frozen=True)
class EvaluationResult:
    """One condition scored against the analysis labels under one policy. Counts only.

    ``missed_ids`` are for :func:`write_evaluation_report` alone, and
    ``failed_ids`` (classifications not ``OK``) for re-scoring without them;
    neither is ever printed.
    """

    condition: str
    model_provider: str
    model_id: str
    model_digests: tuple[str, ...]
    prompt_version: str | None
    model_options: str | None
    policy_version: str
    labels: int
    calibration_labels: int
    scored: int
    not_scored: dict[str, int]
    scores: dict[str, dict[str, Any]]
    oracle: dict[str, dict[str, Any]]
    missed_ids: list[str]
    failed_ids: list[str] = field(default_factory=list)

    def report(self) -> dict[str, Any]:
        """Return everything but the missed IDs, for a counts-only JSON report.

        :returns: JSON-ready counts and versions.
        """
        out = {k: v for k, v in self.__dict__.items() if k not in ("missed_ids", "failed_ids")}
        out["model_digests"] = list(self.model_digests)
        return out


def _labels_with_content_flags(
    root: Path, corpus_version: str, subjects: dict[str, _Subject]
) -> tuple[dict[str, dict[str, Any]], dict[str, str], int]:
    labels = label_records.read_labels(root, labeling.safe_name(corpus_version))
    batches = label_records.read_batches(root, corpus_version)
    chosen = label_records.analysis_labels(labels)
    orders = label_records.batch_post_orders(batches)
    out: dict[str, dict[str, Any]] = {}
    order_of: dict[str, str] = {}
    for comment_id, record in chosen.items():
        s = subjects.get(comment_id)
        flags = s.extra["structure"] if s is not None else []
        out[comment_id] = label_records.with_content_flags(record, flags)
        order_of[comment_id] = orders.get(str(record.get("batch_id")), label_records.UNKNOWN_ORDER)
    calibration = sum(1 for r in chosen.values() if r.get("pass") == "calibration")
    return out, order_of, calibration


def _cached(
    repo: Repository,
    cid: str,
    s: _Subject,
    identity: tuple[str, str, str | None],
    b1: bool,
    model_options: str | None,
) -> domain.Classification | None:
    provider, model_id, prompt_version = identity
    wanted = _b1_hash(s.inp) if b1 else s.inp.input_hash
    matches = [
        k
        for k in repo.classifications(cid, s.comment.comment_id)
        if k.key.input_hash == wanted
        and k.key.model_provider == provider
        and k.key.model_id == model_id
        and k.key.prompt_version == prompt_version
        and k.key.taxonomy_version == taxonomy.TAXONOMY_VERSION
        and k.key.model_options == model_options
    ]
    kept = [k for k in matches if k.outcome in (domain.OK, domain.MALFORMED)]
    pool = kept or matches
    return pool[-1] if pool else None


def _decide(
    outcome: str,
    primary_class: str | None,
    flags: frozenset[str],
    c: domain.Comment,
    policy_version: str,
) -> str:
    return _decision(outcome, primary_class, flags, c, policy_version).tier.name


def evaluate_condition(
    root: Path,
    *,
    condition: str,
    policy_version: str = policy.POLICY_VERSION,
    heuristic_version: str = heuristic.HEURISTIC_VERSION,
    provider_name: str = ollama.PROVIDER,
    model: str | None = None,
    corpus_version: str = labeling.DEFAULT_CORPUS_VERSION,
    only_ids: set[str] | None = None,
    num_ctx: int | None = None,
    connection_id: str | None = None,
) -> EvaluationResult:
    """Score cached classifications of labeled comments against the labels, offline.

    No model runs: each labeled comment's classification is looked up by its
    current input hash and the classifier's identity, and the policy version is
    applied afresh, so any policy can be compared on any cached classifications.
    Comments without a cached classification are counted, not scored. Confidence
    is not passed to the policy (the floor is unset in every version).

    :param root: Repository root.
    :param condition: ``b1`` or ``b2``.
    :param policy_version: One of :data:`afterword.policy.POLICY_VERSIONS`.
    :param heuristic_version: Heuristic version, for ``b1``.
    :param provider_name: Model provider, for ``b2``.
    :param model: Model ID, required for ``b2``.
    :param corpus_version: Label directory.
    :param only_ids: Restrict to these comment IDs, such as a fixed dev subset.
    :param num_ctx: For an Ollama ``b2``, score classifications made with this
        context size instead of the current one (``ollama.NUM_CTX``).
    :param connection_id: Connection; may be omitted when the store has exactly one.
    :returns: Scores for all labels and for each post order, the oracle ceilings
        under the same policy, and the consequential comments collapsed.
    :raises ServiceError: For an unknown condition, policy, or heuristic version,
        or ``b2`` without a model.
    """
    if condition not in CONDITIONS:
        raise ServiceError(f"unknown condition: {condition}")
    if policy_version not in policy.POLICY_VERSIONS:
        raise ServiceError(f"unknown policy version: {policy_version}")
    if condition == "b1":
        if heuristic_version not in heuristic.HEURISTIC_VERSIONS:
            raise ServiceError(f"unknown heuristic version: {heuristic_version}")
        identity: tuple[str, str, str | None] = ("afterword", heuristic_version, None)
        source = "heuristic"
    else:
        if model is None:
            raise ServiceError("b2 needs --model")
        identity = (provider_name, model, classifier.PROMPT_VERSION)
        source = "model"
    options: str | None = None
    if condition == "b2" and provider_name == ollama.PROVIDER:
        options = ollama.options_key(num_ctx or ollama.NUM_CTX)
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        subjects = {s.comment.comment_id: s for s in _subjects(repo, cid)}
        labels, order_of, calibration = _labels_with_content_flags(root, corpus_version, subjects)
        wanted = [i for i in labels if only_ids is None or i in only_ids]
        not_scored: Counter[str] = Counter()
        items: list[scoring.Scored] = []
        digests: set[str] = set()
        for comment_id in sorted(wanted):
            s = subjects.get(comment_id)
            if s is None:
                not_scored["not_a_live_subject_in_store"] += 1
                continue
            k = _cached(repo, cid, s, identity, condition == "b1", options)
            if k is None:
                not_scored["not_classified"] += 1
                continue
            if k.key.model_digest:
                digests.add(k.key.model_digest)
            own = frozenset(k.flags_by_source.get(source, [])) & frozenset(taxonomy.FLAGS)
            fixed = frozenset(f for v in s.extra.values() for f in v)
            items.append(
                scoring.Scored(
                    comment_id=comment_id,
                    label=labels[comment_id],
                    post_order=order_of[comment_id],
                    outcome=k.outcome,
                    primary_class=k.primary_class,
                    classifier_flags=own,
                    tier=_decide(
                        k.outcome, k.primary_class, own | fixed, s.comment, policy_version
                    ),
                    base_tier=_decide(k.outcome, k.primary_class, fixed, s.comment, policy_version),
                )
            )
    finally:
        repo.close()
    scored = scoring.score_by_post_order(items)
    scored_labels = [i.label for i in items]
    return EvaluationResult(
        condition=condition,
        model_provider=identity[0],
        model_id=identity[1],
        model_digests=tuple(sorted(digests)),
        prompt_version=identity[2],
        model_options=options,
        policy_version=policy_version,
        labels=len(wanted),
        calibration_labels=calibration,
        scored=len(items),
        not_scored=dict(not_scored),
        scores={k: v.counts for k, v in scored.items()},
        oracle=label_records.oracle_ceiling(scored_labels, policy_version=policy_version),
        missed_ids=scored["all"].missed_ids,
        failed_ids=scored["all"].failed_ids,
    )


SUBSET_MIN: int = 40
SUBSET_MAX: int = 60


@dataclass(frozen=True)
class DevSubset:
    """A fixed, seeded, class-balanced subset of labeled `dev` comments. Counts only.

    ``ids`` are for the git-ignored ID file alone and are never printed.
    """

    seed: int
    size: int
    by_class: dict[str, int]
    consequential: int
    by_post_order: dict[str, int]
    ids: list[str]


def select_dev_subset(
    root: Path,
    *,
    size: int,
    seed: int,
    corpus_version: str = labeling.DEFAULT_CORPUS_VERSION,
    connection_id: str | None = None,
) -> DevSubset:
    """Choose a class-balanced subset of labeled comments for a short model run.

    Selection: the labeled comments that are live subjects in the store, grouped
    by their analysis label's class. Quotas are filled evenly across classes
    (classes with fewer labels than their share give all they have, and the rest
    is spread over the others, in taxonomy order). Within a class, IDs are sorted
    and shuffled by one ``random.Random(seed)`` taken through the classes in
    taxonomy order, and the first ones are taken. The same labels, store, size,
    and seed always give the same subset.

    :param root: Repository root.
    :param size: Number of comments, :data:`SUBSET_MIN` to :data:`SUBSET_MAX`.
    :param seed: Seed for the shuffle.
    :param corpus_version: Label directory.
    :param connection_id: Connection; may be omitted when the store has exactly one.
    :returns: The subset, with counts by class, consequential, and post order.
    :raises ServiceError: For a size out of range or fewer labeled comments than asked.
    """
    if not SUBSET_MIN <= size <= SUBSET_MAX:
        raise ServiceError(f"subset size must be {SUBSET_MIN} to {SUBSET_MAX}")
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        subjects = {s.comment.comment_id: s for s in _subjects(repo, cid)}
    finally:
        repo.close()
    labels, order_of, _ = _labels_with_content_flags(root, corpus_version, subjects)
    live = {i: r for i, r in labels.items() if i in subjects}
    if len(live) < size:
        raise ServiceError(f"only {len(live)} labeled comments are live in the store")
    rng = random.Random(seed)
    pools: dict[str, list[str]] = {}
    for name in taxonomy.CLASSES:
        ids = sorted(i for i, r in live.items() if r.get("primary_class") == name)
        rng.shuffle(ids)
        pools[name] = ids
    quota = dict.fromkeys(taxonomy.CLASSES, 0)
    remaining = size
    active = [c for c in taxonomy.CLASSES if pools[c]]
    while remaining and active:
        share = max(1, remaining // len(active))
        for name in list(active):
            take = min(share, len(pools[name]) - quota[name], remaining)
            quota[name] += take
            remaining -= take
            if quota[name] == len(pools[name]):
                active.remove(name)
            if not remaining:
                break
    chosen = sorted(i for name in taxonomy.CLASSES for i in pools[name][: quota[name]])
    grades = [live[i].get("consequential_prospective") for i in chosen]
    return DevSubset(
        seed=seed,
        size=len(chosen),
        by_class={name: quota[name] for name in taxonomy.CLASSES},
        consequential=sum(
            1 for g in grades if isinstance(g, int) and g >= label_records.CONSEQUENTIAL_FROM
        ),
        by_post_order=dict(Counter(order_of[i] for i in chosen)),
        ids=chosen,
    )


def write_dev_subset(root: Path, subset: DevSubset) -> Path:
    """Write a subset's IDs, one per line, under ``reports/eval/`` (git-ignored).

    :param root: Repository root.
    :param subset: The subset.
    :returns: The file, named by seed and size so it can be recreated and named in a command.
    """
    out = root / EVAL_ROOT
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"dev-subset-s{subset.seed}-n{subset.size}.txt"
    path.write_text("".join(f"{i}\n" for i in subset.ids), encoding="utf-8")
    return path


def tune_b1_threshold(
    root: Path,
    thresholds: Iterable[int],
    *,
    policy_version: str = policy.POLICY_VERSION,
    corpus_version: str = labeling.DEFAULT_CORPUS_VERSION,
    connection_id: str | None = None,
) -> dict[int, dict[str, dict[str, Any]]]:
    """Score B1's rules at each length threshold on the labeled comments, in memory.

    Tuning on `dev`, not measurement: nothing is stored, and the chosen threshold
    becomes a new heuristic version.

    :param root: Repository root.
    :param thresholds: Prose lengths to try.
    :param policy_version: Policy to apply.
    :param corpus_version: Label directory.
    :param connection_id: Connection; may be omitted when the store has exactly one.
    :returns: Per threshold, :func:`afterword.scoring.score_by_post_order` counts.
    """
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        subjects = {s.comment.comment_id: s for s in _subjects(repo, cid)}
    finally:
        repo.close()
    labels, order_of, _ = _labels_with_content_flags(root, corpus_version, subjects)
    base = {
        i: heuristic.features(
            normalize.normalize(s.comment.body_source, s.comment.body_source_format or "HTML")
        )
        for i, s in subjects.items()
        if i in labels
    }
    out: dict[int, dict[str, dict[str, Any]]] = {}
    for t in thresholds:
        items = []
        for comment_id, f in sorted(base.items()):
            s = subjects[comment_id]
            primary, _ = heuristic.decide(replace(f, long=f.prose_length >= t))
            fixed = frozenset(x for v in s.extra.values() for x in v)
            tier = _decide(domain.OK, primary, fixed, s.comment, policy_version)
            items.append(
                scoring.Scored(
                    comment_id=comment_id,
                    label=labels[comment_id],
                    post_order=order_of[comment_id],
                    outcome=domain.OK,
                    primary_class=primary,
                    classifier_flags=frozenset(),
                    tier=tier,
                    base_tier=tier,
                )
            )
        out[t] = {k: v.counts for k, v in scoring.score_by_post_order(items).items()}
    return out


def write_evaluation_report(
    root: Path,
    result: EvaluationResult,
    *,
    with_misses: bool,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> tuple[Path, Path | None]:
    """Write an evaluation's counts, and optionally its miss list, under ``reports/eval/``.

    Both files are git-ignored. The miss list holds comment IDs only, one per
    line, for the author to review in a local view; no text is written.

    :param root: Repository root.
    :param result: The evaluation.
    :param with_misses: Also write the IDs of consequential comments collapsed.
    :param now: Wall clock, for the file names.
    :returns: The report path and the miss list path (``None`` when not written).
    """
    stamp = now().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{result.model_id}-{result.policy_version}")
    out = root / EVAL_ROOT
    out.mkdir(parents=True, exist_ok=True)
    report = out / f"{stamp}-{result.condition}-{name}.json"
    report.write_text(json.dumps(result.report(), indent=2) + "\n", encoding="utf-8")
    misses = None
    if with_misses:
        misses = out / f"{stamp}-{result.condition}-{name}-misses.txt"
        misses.write_text("".join(f"{i}\n" for i in result.missed_ids), encoding="utf-8")
    return report, misses


# Dev-set analysis: tier causes, class confusion, language (counts only) ---------------


@dataclass(frozen=True)
class DevAnalysis:
    """Counts behind the dev-set evaluation, for a git-ignored JSON report. Counts only.

    No comment text, ID, or name appears anywhere in it.
    """

    model_id: str
    model_options: str | None
    heuristic_version: str
    subjects: int
    labels: int
    conditions: dict[str, dict[str, Any]]
    precheck: dict[str, Any]
    confusion: dict[str, dict[str, int]]
    language: dict[str, Any]

    def report(self) -> dict[str, Any]:
        """Return the counts as JSON-ready data.

        :returns: Every field.
        """
        return dict(self.__dict__)


def _decision(
    outcome: str,
    primary_class: str | None,
    flags: frozenset[str],
    c: domain.Comment,
    policy_version: str,
) -> policy.PriorityDecision:
    ok = outcome == domain.OK
    return policy.assign(
        policy.PolicyInput(
            outcome=outcome,
            primary_class=primary_class if ok else None,
            flags=flags,
            confidence=None,
            edited_since_review=c.lifecycle_state == domain.EDITED,
        ),
        policy_version=policy_version,
    )


def _is_consequential_label(label: dict[str, Any] | None) -> bool:
    grade = None if label is None else label.get("consequential_prospective")
    return isinstance(grade, int) and grade >= label_records.CONSEQUENTIAL_FROM


def _flags_for(s: _Subject, k: domain.Classification, source: str) -> frozenset[str]:
    own = frozenset(k.flags_by_source.get(source, [])) & frozenset(taxonomy.FLAGS)
    return own | frozenset(f for v in s.extra.values() for f in v)


type _Row = tuple[_Subject, domain.Classification, dict[str, Any] | None]


def _tier_causes(rows: list[_Row], source: str, policy_version: str) -> dict[str, Any]:
    pit = taxonomy.POSSIBLE_INSTRUCTION_TEXT
    by_rule: dict[str, Counter[str]] = {"all": Counter(), "labeled": Counter()}
    by_tier: dict[str, Counter[str]] = {"all": Counter(), "labeled": Counter()}
    surface: Counter[str] = Counter()
    surface_consequential: Counter[str] = Counter()
    raised: Counter[str] = Counter()
    for s, k, label in rows:
        flags = _flags_for(s, k, source)
        d = _decision(k.outcome, k.primary_class, flags, s.comment, policy_version)
        for scope in ["all"] + (["labeled"] if label is not None else []):
            by_rule[scope][d.rule_applied] += 1
            by_tier[scope][d.tier.name] += 1
        if label is not None and d.tier == policy.Tier.SURFACE:
            surface[d.rule_applied] += 1
            if _is_consequential_label(label):
                surface_consequential[d.rule_applied] += 1
        if pit in s.extra["precheck"] and d.tier == policy.Tier.SURFACE:
            without = _decision(
                k.outcome, k.primary_class, flags - {pit}, s.comment, policy_version
            )
            if without.tier != policy.Tier.SURFACE:
                raised["all"] += 1
                if label is not None:
                    raised["labeled"] += 1
                    raised["labeled_consequential"] += _is_consequential_label(label)
    return {
        "rule_applied": {k: dict(sorted(v.items())) for k, v in by_rule.items()},
        "by_tier": {k: {t: v[t] for t in scoring.TIERS} for k, v in by_tier.items()},
        "labeled_surface_by_rule": dict(sorted(surface.items())),
        "labeled_surface_consequential_by_rule": dict(sorted(surface_consequential.items())),
        "raised_to_surface_by_precheck_alone": {
            k: raised[k] for k in ("all", "labeled", "labeled_consequential")
        },
    }


def _counted(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(v) for v in values).items()))


def _group_counts(
    group: list[tuple[_Subject, domain.Classification | None, dict[str, Any] | None]],
) -> dict[str, Any]:
    labeled = [label for _, _, label in group if label is not None]
    model = [(s, k) for s, k, _ in group if k is not None]
    out: dict[str, Any] = {
        "comments": len(group),
        "precheck_fired": sum(
            1 for s, _, _ in group if taxonomy.POSSIBLE_INSTRUCTION_TEXT in s.extra["precheck"]
        ),
        "labeled": len(labeled),
        "labeled_consequential": sum(1 for r in labeled if _is_consequential_label(r)),
        "label_class": _counted(r.get("primary_class") for r in labeled),
        "label_grade": _counted(r.get("consequential_prospective") for r in labeled),
        "read_via_translation": sum(1 for r in labeled if r.get("read_via_translation") is True),
        "model_outcomes": _counted(k.outcome for _, k in model),
        "model_class": _counted(k.primary_class for _, k in model if k.outcome == domain.OK),
    }
    for pv in policy.POLICY_VERSIONS:
        tiers = Counter(
            _decision(
                k.outcome, k.primary_class, _flags_for(s, k, "model"), s.comment, pv
            ).tier.name
            for s, k in model
        )
        out[f"model_tiers_{pv}"] = {t: tiers[t] for t in scoring.TIERS}
    return out


def analyze_dev(
    root: Path,
    *,
    model: str,
    provider_name: str = ollama.PROVIDER,
    num_ctx: int | None = None,
    heuristic_version: str = "hb-v0.2",
    corpus_version: str = labeling.DEFAULT_CORPUS_VERSION,
    connection_id: str | None = None,
) -> DevAnalysis:
    """Count what decided each tier, the class confusion, and the language mix, offline.

    No model runs. For every stored comment from others, the cached B1 and B2
    classifications are found as :func:`evaluate_condition` finds them, and each
    policy version is applied in memory, recording the rule that decided the
    tier. Also: how often the deterministic pre-check fired and on what labels;
    B2's predicted class against the label (``OK`` outcomes only); and comments
    by detected language (:mod:`afterword.language`), with B2's outcomes and the
    labels for each. Counts only.

    :param root: Repository root.
    :param model: B2 model ID.
    :param provider_name: B2 provider.
    :param num_ctx: For an Ollama B2, the context size its runs used
        (default: the current one).
    :param heuristic_version: B1 heuristic version.
    :param corpus_version: Label directory.
    :param connection_id: Connection; may be omitted when the store has exactly one.
    :returns: The counts.
    :raises ServiceError: For an unknown heuristic version or an ambiguous connection.
    """
    from afterword import language

    if heuristic_version not in heuristic.HEURISTIC_VERSIONS:
        raise ServiceError(f"unknown heuristic version: {heuristic_version}")
    options = None
    if provider_name == ollama.PROVIDER:
        options = ollama.options_key(num_ctx or ollama.NUM_CTX)
    b1_identity: tuple[str, str, str | None] = ("afterword", heuristic_version, None)
    b2_identity: tuple[str, str, str | None] = (provider_name, model, classifier.PROMPT_VERSION)
    repo = open_store(root)
    try:
        cid = _pick_connection(repo, connection_id)
        subjects = {s.comment.comment_id: s for s in _subjects(repo, cid)}
        labels, _, _ = _labels_with_content_flags(root, corpus_version, subjects)
        b1 = {i: _cached(repo, cid, s, b1_identity, True, None) for i, s in subjects.items()}
        b2 = {i: _cached(repo, cid, s, b2_identity, False, options) for i, s in subjects.items()}
    finally:
        repo.close()
    labels = {i: r for i, r in labels.items() if i in subjects}

    conditions: dict[str, dict[str, Any]] = {}
    for name, cached, source in (("b1", b1, "heuristic"), ("b2", b2, "model")):
        rows: list[_Row] = []
        for i, s in subjects.items():
            k = cached[i]
            if k is not None:
                rows.append((s, k, labels.get(i)))
        conditions[name] = {
            "classified": len(rows),
            "not_classified": len(subjects) - len(rows),
            "outcomes": _counted(k.outcome for _, k, _ in rows),
        } | {pv: _tier_causes(rows, source, pv) for pv in policy.POLICY_VERSIONS}

    pit = taxonomy.POSSIBLE_INSTRUCTION_TEXT
    fired = [s for s in subjects.values() if pit in s.extra["precheck"]]
    fired_labels = [labels[s.comment.comment_id] for s in fired if s.comment.comment_id in labels]
    rules: Counter[str] = Counter()
    for s in fired:
        rules.update(precheck.precheck(s.inp.comment).rules_matched)
    model_set = [
        i for i, k in b2.items() if k is not None and pit in k.flags_by_source.get("model", [])
    ]
    precheck_counts: dict[str, Any] = {
        "version": precheck.PRECHECK_VERSION,
        "fired": len(fired),
        "of": len(subjects),
        "rules_matched": dict(sorted(rules.items())),
        "labeled": len(fired_labels),
        "labeled_consequential": sum(1 for r in fired_labels if _is_consequential_label(r)),
        "label_grade": _counted(r.get("consequential_prospective") for r in fired_labels),
        "label_class": _counted(r.get("primary_class") for r in fired_labels),
        "model_set_flag": {
            "set": len(model_set),
            "also_precheck": sum(1 for i in model_set if pit in subjects[i].extra["precheck"]),
            "labeled": sum(1 for i in model_set if i in labels),
            "labeled_consequential": sum(
                1 for i in model_set if _is_consequential_label(labels.get(i))
            ),
        },
    }

    confusion: dict[str, Counter[str]] = {}
    for i, label in labels.items():
        k = b2.get(i)
        if k is not None and k.outcome == domain.OK:
            confusion.setdefault(str(k.primary_class), Counter())[
                str(label.get("primary_class"))
            ] += 1

    groups: dict[str, list[tuple[_Subject, domain.Classification | None, dict[str, Any] | None]]]
    groups = {}
    for i, s in subjects.items():
        text = normalize.normalize(s.comment.body_source, s.comment.body_source_format or "HTML")
        guess = language.detect(heuristic.prose(text.text))
        groups.setdefault(guess.language, []).append((s, b2[i], labels.get(i)))
    not_languages = ("en", language.TOO_SHORT, language.UNCERTAIN)
    non_english = [row for code, g in groups.items() if code not in not_languages for row in g]
    language_counts: dict[str, Any] = {
        "detector": language.DETECTOR,
        "min_chars": language.MIN_CHARS,
        "min_confidence": language.MIN_CONFIDENCE,
        "text": "normalized prose: code and link targets removed (heuristic.prose)",
        "by_language": {code: len(g) for code, g in sorted(groups.items())},
        "groups": {code: _group_counts(g) for code, g in sorted(groups.items())},
        "non_english": _group_counts(non_english),
    }
    return DevAnalysis(
        model_id=model,
        model_options=options,
        heuristic_version=heuristic_version,
        subjects=len(subjects),
        labels=len(labels),
        conditions=conditions,
        precheck=precheck_counts,
        confusion={k: dict(sorted(v.items())) for k, v in sorted(confusion.items())},
        language=language_counts,
    )


def write_dev_analysis(
    root: Path,
    result: DevAnalysis,
    *,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> Path:
    """Write a dev analysis under ``reports/eval/`` (git-ignored), counts only.

    :param root: Repository root.
    :param result: The analysis.
    :param now: Wall clock, for the file name.
    :returns: The report path.
    """
    stamp = now().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", result.model_id)
    out = root / EVAL_ROOT
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{stamp}-dev-analysis-{name}.json"
    path.write_text(json.dumps(result.report(), indent=2) + "\n", encoding="utf-8")
    return path


# Benchmark (synthetic only) -------------------------------------------------------------


@dataclass(frozen=True)
class BenchResult:
    """A finished benchmark and where its report was written."""

    identity: ModelIdentity
    report: dict[str, Any]
    report_path: Path


def run_benchmark(
    root: Path,
    *,
    synthetic: bool,
    provider_name: str,
    model: str | None,
    sets: list[str],
    repeat: int = 3,
    host: str = ollama.DEFAULT_HOST,
    progress: Callable[[int, int, dict[str, Any]], None] | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> BenchResult:
    """Benchmark one model on the committed synthetic sets and write the report.

    :param root: Repository root.
    :param synthetic: Must be ``True``: the benchmark never runs on anything else.
    :param provider_name: ``ollama`` or ``anthropic``.
    :param model: Model ID.
    :param sets: Synthetic set names.
    :param repeat: How many of the first cases to run twice (repeat stability).
    :param host: Ollama base URL (loopback only).
    :param progress: Called after each case.
    :param now: Wall clock.
    :returns: The verified model, the report, and its path under ``reports/bench/``.
    :raises ServiceError: Without ``synthetic``, for input that is not a verified
        synthetic set, or for a model that fails verification.
    """
    if not synthetic:
        raise ServiceError("bench runs on the committed synthetic sets only; pass --synthetic")
    try:
        cases = bench.load_cases(root, sets)
    except bench.BenchRefused as exc:
        raise ServiceError(f"refused: {exc}") from None
    provider = make_provider(provider_name, model, host=host)
    started = now()
    try:
        identity = _verify(provider)
        try:
            outcome = bench.run_bench(provider, cases, repeat=repeat, progress=progress)
        except ProviderError as exc:
            raise ServiceError(f"the model provider failed ({exc.kind})", code=3) from None
    finally:
        provider.close()
    options: dict[str, Any] = {"temperature": 0, "max_output_tokens": classifier.MAX_OUTPUT_TOKENS}
    if identity.provider == ollama.PROVIDER:
        options |= {"seed": ollama.SEED, "num_ctx": ollama.NUM_CTX, "think": False}
    report = {
        "kind": "synthetic-benchmark",
        "started_at": domain.utc(started).isoformat(),
        "finished_at": domain.utc(now()).isoformat(),
        "provider": identity.provider,
        "model_id": identity.model_id,
        "model_digest": identity.digest,
        "prompt_version": classifier.PROMPT_VERSION,
        "taxonomy_version": taxonomy.TAXONOMY_VERSION,
        "normalization_version": normalize.NORMALIZATION_VERSION,
        "precheck_version": precheck.PRECHECK_VERSION,
        "policy_version": policy.POLICY_VERSION,
        "options": options,
        "sets": sets,
    } | outcome
    stamp = domain.utc(started).strftime("%Y%m%dT%H%M%SZ")
    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "_", identity.model_id)
    path = root / REPORT_ROOT / "bench" / f"{stamp}-{identity.provider}-{safe_model}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return BenchResult(identity, report, path)
