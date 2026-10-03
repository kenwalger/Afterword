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
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from afterword import (
    baseline,
    bench,
    classifier,
    domain,
    heuristic,
    labeling,
    lifecycle,
    normalize,
    policy,
    precheck,
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
    :param pass_name: ``initial`` or ``self_agreement``.
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

    The batch, its order, and its records are the same as ``afterword label``.

    :param session: An opened run.
    :param root: Repository root.
    :param pass_name: ``initial`` or ``self_agreement``.
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


def _b1(
    cid: str,
    c: domain.Comment,
    key: domain.CacheKey,
    extra: dict[str, list[str]],
    now: datetime,
) -> domain.Classification:
    normalized = normalize.normalize(c.body_source, c.body_source_format or "HTML")
    result = heuristic.classify(normalized)
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
    :param progress: Called with the number done and the total.
    :param now: Wall clock.
    :returns: Counts of reuse, outcomes, errors, and tiers.
    :raises ServiceError: For an unknown condition, an unsigned boundary path, a
        model that fails verification, or an ambiguous connection.
    """
    if condition not in CONDITIONS:
        raise ServiceError(f"unknown condition: {condition}")
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
            identity = ModelIdentity(
                "afterword", heuristic.HEURISTIC_VERSION, None, domain.NOT_EXPOSED
            )
            prompt_version = None
        comments = repo.comments(cid)
        contents = repo.contents(cid)
        subjects = [
            c
            for c in comments.values()
            if c.is_content_author is False
            and c.lifecycle_state in (domain.ACTIVE, domain.EDITED)
            and c.body_text is not None
        ]
        reused = 0
        outcomes: Counter[str] = Counter()
        errors: Counter[str] = Counter()
        tiers: Counter[str] = Counter()
        for i, c in enumerate(subjects, start=1):
            parent = comments.get(c.parent_comment_id) if c.parent_comment_id else None
            parent_text = None
            if c.parent_comment_id is not None:
                parent_text = (parent.body_text if parent else None) or ""
            reply_to_author = bool(
                parent
                and parent.is_content_author
                and parent.is_content_author_state == domain.PRESENT
            )
            content = contents.get(c.content_id)
            inp = classifier.build_input(
                post_title=content.title if content else None,
                comment=c.body_text or "",
                parent=parent_text,
                reply_to_author=reply_to_author,
            )
            if provider is None:
                # B1 sees the comment only, so only the comment is in its key.
                canonical = json.dumps({"comment": inp.comment}, ensure_ascii=False)
                hashed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            else:
                hashed = inp.input_hash
            key = domain.CacheKey(
                hashed,
                identity.provider,
                identity.model_id,
                identity.digest,
                prompt_version,
                taxonomy.TAXONOMY_VERSION,
            )
            pre = precheck.precheck(inp.comment)
            extra = {
                "structure": [taxonomy.REPLY_TO_AUTHOR] if reply_to_author else [],
                "precheck": [taxonomy.POSSIBLE_INSTRUCTION_TEXT] if pre.flagged else [],
            }
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
