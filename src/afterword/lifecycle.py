"""Ingest planning: the lifecycle rules of ``DATA-MODEL.md`` and ADR-009, as a pure function.

:func:`plan_sync` compares one sync run with what is already stored and returns
every record to write and every purge to perform. It reads and writes nothing
itself; the service layer applies the plan through the repository in one
transaction (ADR-012, ADR-013).

Rules, per comment:

- **New:** stored ``ACTIVE`` with its normalized text (``norm-v0.1``).
- **Unchanged payload:** only ``last_observed_at`` moves.
- **Payload changed, text unchanged:** a new SourceRecord; no state change.
- **Edited:** the normalized text changed; a new SourceRecord, state ``EDITED``.
- **Missing:** absent from a complete fetch of its post; ``MISSING_FROM_SOURCE``.
- **Deleted (absence):** absent from two consecutive complete fetches; deleted
  with ``ABSENT_TWICE``, then purged.
- **Deleted (placeholder):** returned in the exact placeholder shape; deleted with
  ``SOURCE_PLACEHOLDER`` at once, then purged. The placeholder's own record holds
  no commenter content and is kept as thread structure.
- **Placeholder first seen:** stored directly as ``DELETED_UPSTREAM`` with unknown
  authorship and no body.
- **Unexpected shape:** nothing stored, state unchanged, a limitation recorded.

The purge happens in the same ingest that detects the deletion, which is no
later than ADR-009's "at the next sync".
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime

from afterword import domain
from afterword.normalize import normalize, text_changed
from afterword.observations import (
    SHAPE_COMMENT,
    SHAPE_PLACEHOLDER,
    SHAPE_UNEXPECTED,
    SourcePayload,
    SyncedComment,
    SyncedIdentity,
    SyncObservations,
)


@dataclass
class SyncPlan:
    """Everything one ingest writes. Applied in one transaction."""

    sync_run: domain.SyncRun
    identities: list[domain.PlatformIdentity] = field(default_factory=list)
    contents: list[domain.ContentItem] = field(default_factory=list)
    source_records: list[domain.SourceRecord] = field(default_factory=list)
    comments: list[domain.Comment] = field(default_factory=list)
    events: list[domain.LifecycleEvent] = field(default_factory=list)
    # (comment ID, source record to keep): body text, earlier raw payloads, and
    # model text derived from the comment are removed.
    purges: list[tuple[str, str | None]] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)


@dataclass
class _Planner:
    obs: SyncObservations
    connection_id: str
    existing_comments: dict[str, domain.Comment]
    existing_contents: dict[str, domain.ContentItem]
    observed_at: datetime
    new_id: Callable[[], str]
    limitations: list[str] = field(default_factory=list)
    plan_records: list[domain.SourceRecord] = field(default_factory=list)
    comments: list[domain.Comment] = field(default_factory=list)
    events: list[domain.LifecycleEvent] = field(default_factory=list)
    purges: list[tuple[str, str | None]] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)

    def record(self, source: SourcePayload) -> domain.SourceRecord:
        rec = domain.SourceRecord(
            source_record_id=self.new_id(),
            connection_id=self.connection_id,
            sync_run_id=self.obs.sync_run_id,
            platform=self.obs.platform,
            source_type=source.source_type,
            source_object_id=source.source_object_id,
            observed_at=self.observed_at,
            source_created_at=source.source_created_at,
            source_updated_at=source.source_updated_at,
            source_updated_at_state=source.source_updated_at_state,
            raw_payload=json.dumps(source.payload, sort_keys=True, ensure_ascii=False),
            payload_hash=source.payload_hash,
            ingestion_version=self.obs.ingestion_version,
        )
        self.plan_records.append(rec)
        return rec

    def event(self, comment_id: str, before: str | None, after: str, reason: str) -> None:
        self.events.append(
            domain.LifecycleEvent(
                event_id=self.new_id(),
                connection_id=self.connection_id,
                comment_id=comment_id,
                sync_run_id=self.obs.sync_run_id,
                from_state=before,
                to_state=after,
                reason=reason,
                occurred_at=self.observed_at,
            )
        )

    def delete_and_purge(
        self, c: domain.Comment, evidence: str, keep: str | None, **changes: object
    ) -> domain.Comment:
        self.event(c.comment_id, c.lifecycle_state, domain.DELETED_UPSTREAM, evidence.lower())
        self.event(c.comment_id, domain.DELETED_UPSTREAM, domain.PURGED, "purge")
        self.purges.append((c.comment_id, keep))
        self.counts["purged"] += 1
        return replace(
            c,
            lifecycle_state=domain.PURGED,
            deletion_evidence=evidence,
            body_source=None,
            body_text=None,
            body_text_hash=None,
            consecutive_absences=0,
            **changes,  # type: ignore[arg-type]
        )


def _body(s: SyncedComment) -> tuple[str | None, str | None, str | None, str | None]:
    if s.body_source is None or s.body_source_format is None:
        return None, None, None, None
    n = normalize(s.body_source, s.body_source_format)
    return s.body_source, n.text, n.text_hash, n.version


def plan_sync(
    obs: SyncObservations,
    *,
    connection_id: str,
    existing_comments: dict[str, domain.Comment],
    existing_contents: dict[str, domain.ContentItem],
    now: datetime,
    new_id: Callable[[], str] = domain.new_id,
) -> SyncPlan:
    """Plan the ingest of one sync run.

    :param obs: The run, from the adapter.
    :param connection_id: The connection the run belongs to.
    :param existing_comments: Stored comments of this connection on the run's posts, by ID.
    :param existing_contents: Stored posts of this connection, by ID.
    :param now: Ingest time; also the observation time when the run has none.
    :param new_id: Identifier factory, injectable for tests.
    :returns: The records to write, the purges, and counts by outcome.
    """
    observed_at = domain.utc(obs.finished_at or obs.started_at or now)
    p = _Planner(obs, connection_id, existing_comments, existing_contents, observed_at, new_id)
    identities: dict[str, domain.PlatformIdentity] = {}
    contents: list[domain.ContentItem] = []

    def identity_id(synced: SyncedIdentity | None) -> str | None:
        if synced is None:
            return None
        identities[synced.source_user_id] = domain.PlatformIdentity(
            connection_id=connection_id,
            platform_identity_id=synced.source_user_id,
            platform=obs.platform,
            source_user_id=synced.source_user_id,
            handle=synced.handle,
            display_name=synced.display_name,
            last_observed_at=observed_at,
        )
        return synced.source_user_id

    for sc in obs.contents:
        stored = existing_contents.get(sc.source_object_id)
        author = identity_id(sc.author)
        if stored is not None and stored.current_payload_hash == sc.source.payload_hash:
            record_id = stored.source_record_id
        else:
            record_id = p.record(sc.source).source_record_id
        contents.append(
            domain.ContentItem(
                connection_id=connection_id,
                content_id=sc.source_object_id,
                platform=obs.platform,
                source_object_id=sc.source_object_id,
                author_platform_identity_id=author,
                title=sc.title,
                canonical_url=sc.canonical_url,
                canonical_url_state=domain.PRESENT if sc.canonical_url else domain.SOURCE_EMPTY,
                published_at=sc.published_at,
                source_record_id=record_id,
                current_payload_hash=sc.source.payload_hash,
            )
        )

    roots: dict[str, str] = {}
    seen: set[str] = set()
    live_by_content: Counter[str] = Counter()
    for s in obs.comments:
        if s.source_object_id in seen:
            p.limitations.append(f"comment {s.source_object_id} appeared twice; second ignored")
            continue
        seen.add(s.source_object_id)
        parent = s.parent_source_object_id
        roots[s.source_object_id] = roots.get(parent, parent) if parent else s.source_object_id
        stored_c = existing_comments.get(s.source_object_id)
        if s.shape == SHAPE_UNEXPECTED:
            p.counts["unexpected_shapes"] += 1
            p.limitations.append(
                f"unexpected node shape: comment {s.source_object_id} on post "
                f"{s.content_source_object_id} (ADR-009); not stored, friction entry needed"
            )
            continue
        if s.shape == SHAPE_COMMENT:
            live_by_content[s.content_source_object_id] += 1
        if stored_c is None:
            _new_comment(p, s, roots[s.source_object_id], identity_id(s.author))
        elif s.shape == SHAPE_PLACEHOLDER:
            _known_placeholder(p, s, stored_c)
        else:
            _known_comment(p, s, stored_c, identity_id(s.author))

    complete = {c.source_object_id for c in obs.contents if c.comments_complete}
    for stored_c in existing_comments.values():
        if stored_c.content_id in complete and stored_c.comment_id not in seen:
            _absent(p, stored_c)

    for sc in obs.contents:
        live = live_by_content[sc.source_object_id]
        reported = sc.reported_comment_count
        if sc.comments_complete and reported is not None and reported != live:
            p.limitations.append(
                f"post {sc.source_object_id}: source reports {reported} comments, "
                f"{live} live comments observed"
            )

    run = domain.SyncRun(
        connection_id=connection_id,
        sync_run_id=obs.sync_run_id,
        platform=obs.platform,
        started_at=obs.started_at,
        finished_at=obs.finished_at,
        scope=obs.scope,
        adapter_version=obs.adapter_version,
        outcome=obs.outcome,
        limitations_observed=tuple(obs.limitations + p.limitations),
        ingested_at=domain.utc(now),
    )
    return SyncPlan(
        sync_run=run,
        identities=list(identities.values()),
        contents=contents,
        source_records=p.plan_records,
        comments=p.comments,
        events=p.events,
        purges=p.purges,
        counts=p.counts,
    )


def _new_comment(p: _Planner, s: SyncedComment, root: str, author: str | None) -> None:
    rec = p.record(s.source)
    parent_state = domain.PRESENT if s.parent_source_object_id else domain.SOURCE_EMPTY
    base = domain.Comment(
        connection_id=p.connection_id,
        comment_id=s.source_object_id,
        platform=p.obs.platform,
        source_object_id=s.source_object_id,
        content_id=s.content_source_object_id,
        parent_comment_id=s.parent_source_object_id,
        parent_comment_id_state=parent_state,
        thread_root_comment_id=root,
        author_platform_identity_id=author,
        author_state=domain.PRESENT if author else domain.UNKNOWN,
        is_content_author=s.is_content_author,
        is_content_author_state=domain.PRESENT,
        body_source=None,
        body_source_format=None,
        body_text=None,
        normalization_version=None,
        body_text_hash=None,
        created_at=s.created_at,
        first_observed_at=p.observed_at,
        last_observed_at=p.observed_at,
        lifecycle_state=domain.ACTIVE,
        deletion_evidence=domain.NOT_YET_INTERPRETED,
        consecutive_absences=0,
        current_source_record_id=rec.source_record_id,
        current_payload_hash=s.source.payload_hash,
    )
    if s.shape == SHAPE_PLACEHOLDER:
        p.counts["placeholder_first_seen"] += 1
        p.event(s.source_object_id, None, domain.DELETED_UPSTREAM, "source_placeholder")
        p.comments.append(
            replace(
                base,
                author_state=domain.UNKNOWN,
                is_content_author=None,
                is_content_author_state=domain.UNKNOWN,
                lifecycle_state=domain.DELETED_UPSTREAM,
                deletion_evidence=domain.SOURCE_PLACEHOLDER,
            )
        )
        return
    body, text, text_hash, version = _body(s)
    p.counts["new"] += 1
    p.event(s.source_object_id, None, domain.ACTIVE, "first_observed")
    p.comments.append(
        replace(
            base,
            body_source=body,
            body_source_format=s.body_source_format,
            body_text=text,
            normalization_version=version,
            body_text_hash=text_hash,
        )
    )


def _known_placeholder(p: _Planner, s: SyncedComment, c: domain.Comment) -> None:
    if c.lifecycle_state not in domain.LIVE_STATES:
        p.counts["unchanged"] += 1
        p.comments.append(replace(c, last_observed_at=p.observed_at))
        return
    rec = p.record(s.source)
    p.counts["deleted_placeholder"] += 1
    # Authorship and is_content_author are carried from the last observation (ADR-009).
    p.comments.append(
        p.delete_and_purge(
            c,
            domain.SOURCE_PLACEHOLDER,
            rec.source_record_id,
            last_observed_at=p.observed_at,
            current_source_record_id=rec.source_record_id,
            current_payload_hash=s.source.payload_hash,
        )
    )


def _known_comment(p: _Planner, s: SyncedComment, c: domain.Comment, author: str | None) -> None:
    if c.lifecycle_state not in domain.LIVE_STATES:
        p.limitations.append(
            f"comment {c.comment_id} was deleted upstream but is returned with content; "
            "left purged (ADR-009)"
        )
        return
    state = c.lifecycle_state
    changes: dict[str, object] = {
        "last_observed_at": p.observed_at,
        "consecutive_absences": 0,
        "author_platform_identity_id": author,
        "author_state": domain.PRESENT if author else domain.UNKNOWN,
        "is_content_author": s.is_content_author,
        "is_content_author_state": domain.PRESENT,
    }
    if state == domain.MISSING_FROM_SOURCE:
        state = domain.ACTIVE
        p.counts["reappeared"] += 1
        p.event(c.comment_id, domain.MISSING_FROM_SOURCE, domain.ACTIVE, "reappeared")
    if s.source.payload_hash == c.current_payload_hash:
        p.counts["unchanged"] += 1
    else:
        rec = p.record(s.source)
        changes["current_source_record_id"] = rec.source_record_id
        changes["current_payload_hash"] = s.source.payload_hash
        edited = text_changed(
            c.body_source,
            c.body_source_format or "HTML",
            s.body_source,
            s.body_source_format or "HTML",
        )
        body, text, text_hash, version = _body(s)
        changes["body_source"] = body
        changes["body_source_format"] = s.body_source_format
        if edited:
            p.counts["edited"] += 1
            p.event(c.comment_id, state, domain.EDITED, "text_changed")
            state = domain.EDITED
        else:
            p.counts["payload_changed"] += 1
        # Renormalized under the current version either way, so the stored text and
        # its version always agree.
        changes["body_text"] = text
        changes["body_text_hash"] = text_hash
        changes["normalization_version"] = version
    changes["lifecycle_state"] = state
    p.comments.append(replace(c, **changes))  # type: ignore[arg-type]


def _absent(p: _Planner, c: domain.Comment) -> None:
    if c.lifecycle_state in (domain.ACTIVE, domain.EDITED):
        p.counts["missing"] += 1
        p.event(c.comment_id, c.lifecycle_state, domain.MISSING_FROM_SOURCE, "absent")
        p.comments.append(
            replace(c, lifecycle_state=domain.MISSING_FROM_SOURCE, consecutive_absences=1)
        )
    elif c.lifecycle_state == domain.MISSING_FROM_SOURCE:
        p.counts["deleted_absent"] += 1
        p.comments.append(p.delete_and_purge(c, domain.ABSENT_TWICE, None))
