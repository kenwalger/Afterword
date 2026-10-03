"""Canonical stored records (``docs/DATA-MODEL.md``, v6) and the rules they share.

Records use stable string identifiers (source IDs where they exist, otherwise
UUIDs) and UTC timestamps (ADR-013). Every record carries the
``connection_id`` of the platform connection that produced it, so one
connection's data can be removed completely. No record holds a filesystem path,
hostname, or operating-system user name.

Value states (``DATA-MODEL.md``) are kept beside nullable values as a second
field named ``<field>_state``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

# Value states.
PRESENT: str = "PRESENT"
SOURCE_EMPTY: str = "SOURCE_EMPTY"
NOT_EXPOSED: str = "NOT_EXPOSED"
NOT_REQUESTED: str = "NOT_REQUESTED"
INGESTION_FAILED: str = "INGESTION_FAILED"
NOT_YET_INTERPRETED: str = "NOT_YET_INTERPRETED"
UNKNOWN: str = "UNKNOWN"

# Comment lifecycle states.
ACTIVE: str = "ACTIVE"
EDITED: str = "EDITED"
MISSING_FROM_SOURCE: str = "MISSING_FROM_SOURCE"
DELETED_UPSTREAM: str = "DELETED_UPSTREAM"
PURGED: str = "PURGED"
LIVE_STATES: frozenset[str] = frozenset({ACTIVE, EDITED, MISSING_FROM_SOURCE})

# Deletion evidence (ADR-009).
ABSENT_TWICE: str = "ABSENT_TWICE"
SOURCE_PLACEHOLDER: str = "SOURCE_PLACEHOLDER"

# Classification outcomes and kinds.
OK: str = "OK"
MALFORMED: str = "MALFORMED"
FAILED: str = "FAILED"
HEURISTIC: str = "HEURISTIC"
MODEL: str = "MODEL"


def new_id() -> str:
    """Create a record identifier for a record with no source ID.

    :returns: A random UUID as a string.
    """
    return str(uuid.uuid4())


def utc(moment: datetime) -> datetime:
    """Convert an aware timestamp to UTC.

    :param moment: A timezone-aware timestamp.
    :returns: The same instant in UTC.
    :raises ValueError: If the timestamp is naive.
    """
    if moment.tzinfo is None:
        raise ValueError("timestamps must carry a timezone")
    return moment.astimezone(UTC)


@dataclass(frozen=True)
class PlatformConnection:
    """One configured connection to a source platform (ADR-013, rule 3)."""

    connection_id: str
    platform: str
    account_source_user_id: str
    created_at: datetime


@dataclass(frozen=True)
class SyncRun:
    """One execution of a source adapter, as ingested."""

    connection_id: str
    sync_run_id: str
    platform: str
    started_at: datetime | None
    finished_at: datetime | None
    scope: str
    adapter_version: str
    outcome: str
    limitations_observed: tuple[str, ...]
    ingested_at: datetime


@dataclass(frozen=True)
class SourceRecord:
    """Append-only evidence of what a source returned for one object."""

    source_record_id: str
    connection_id: str
    sync_run_id: str
    platform: str
    source_type: str
    source_object_id: str
    observed_at: datetime
    source_created_at: datetime | None
    source_updated_at: datetime | None
    source_updated_at_state: str
    # None once purged (ADR-009).
    raw_payload: str | None
    payload_hash: str
    ingestion_version: str
    purged_at: datetime | None = None


@dataclass(frozen=True)
class PlatformIdentity:
    """A platform-local identity as it arrived with posts and comments. Not a person."""

    connection_id: str
    platform_identity_id: str
    platform: str
    source_user_id: str
    handle: str | None
    display_name: str | None
    last_observed_at: datetime


@dataclass(frozen=True)
class ContentItem:
    """A published post."""

    connection_id: str
    content_id: str
    platform: str
    source_object_id: str
    author_platform_identity_id: str | None
    title: str | None
    canonical_url: str | None
    canonical_url_state: str
    published_at: datetime | None
    source_record_id: str
    current_payload_hash: str


@dataclass(frozen=True)
class Comment:
    """A comment, normalized, with its lifecycle (``DATA-MODEL.md``)."""

    connection_id: str
    comment_id: str
    platform: str
    source_object_id: str
    content_id: str
    parent_comment_id: str | None
    parent_comment_id_state: str
    thread_root_comment_id: str
    author_platform_identity_id: str | None
    author_state: str
    is_content_author: bool | None
    is_content_author_state: str
    body_source: str | None
    body_source_format: str | None
    body_text: str | None
    normalization_version: str | None
    body_text_hash: str | None
    created_at: datetime | None
    first_observed_at: datetime
    last_observed_at: datetime
    lifecycle_state: str
    deletion_evidence: str
    consecutive_absences: int
    current_source_record_id: str | None
    current_payload_hash: str | None
    # DEV comments have no edit time.
    updated_at_state: str = NOT_EXPOSED


@dataclass(frozen=True)
class LifecycleEvent:
    """One change of a comment's lifecycle state, kept after any purge."""

    event_id: str
    connection_id: str
    comment_id: str
    sync_run_id: str
    from_state: str | None
    to_state: str
    reason: str
    occurred_at: datetime


@dataclass(frozen=True)
class CacheKey:
    """Identifies a classification: same key, same result (``DATA-MODEL.md``, Cache)."""

    input_hash: str
    model_provider: str
    model_id: str
    model_digest: str | None
    prompt_version: str | None
    taxonomy_version: str


@dataclass(frozen=True)
class Classification:
    """One interpretation of one comment by B1 or a model. Never part of the comment."""

    classification_id: str
    connection_id: str
    comment_id: str
    comment_source_record_id: str | None
    key: CacheKey
    primary_class: str | None
    flags: tuple[str, ...]
    flags_by_source: dict[str, list[str]]
    confidence: str | None
    confidence_state: str
    explanation: str | None
    classifier_kind: str
    model_digest_state: str
    normalization_version: str
    precheck_version: str
    input_fields_sent: tuple[str, ...]
    raw_output: str | None
    latency_ms: int | None
    classified_at: datetime
    outcome: str
    # A category such as "malformed:not_json" or "failed:timeout"; never a message
    # that could hold a host name or a path.
    error: str | None = None


@dataclass(frozen=True)
class PriorityAssignment:
    """The policy's output for one classification (ADR-007)."""

    priority_assignment_id: str
    connection_id: str
    comment_id: str
    classification_id: str
    policy_version: str
    tier: str
    rule_applied: str
    rules_fired: tuple[str, ...]
    assigned_at: datetime
