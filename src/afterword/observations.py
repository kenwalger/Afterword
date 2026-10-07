"""Source-neutral observations consumed outside the adapter boundary.

These are deliberately smaller than the Stage 2 data model. They carry only
what Stage 0 needs (the volume baseline and the labeling tool), and nothing
platform-specific (ADR-001).

Text fields (titles, bodies, author references) are filled only when a run is
loaded with `include_text=True`, which the labeling tool does and the baseline
does not. `None` there means "not loaded or not captured", not a value state;
Stage 2 replaces these records with the canonical model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ObservedContent:
    """A published post, as observed in one run."""

    content_ref: str
    published_at: datetime | None
    reported_comment_count: int | None
    title: str | None = None
    # Last edit of the post, when the run captured it (not every run does).
    edited_at: datetime | None = None
    # The post body as the source supplied it, loaded only with text and only
    # when the run fetched the post singly (not every run does).
    body_source: str | None = None
    body_source_format: str | None = None


@dataclass(frozen=True)
class ObservedComment:
    """A comment node, as observed in one run."""

    content_ref: str
    source_object_id: str
    parent_source_object_id: str | None
    depth: int
    created_at: datetime | None
    is_content_author: bool
    # The source still shows this comment's place in the thread, but its content
    # and author were removed upstream (ADR-009). Not a comment from anyone.
    is_deletion_placeholder: bool = False
    # Authorless or unknown keys, but not the known placeholder shape (ADR-009).
    is_unexpected_shape: bool = False
    # Opaque, platform-local reference to the commenter. Used only to tell
    # commenters apart within a thread, never shown or stored.
    author_ref: str | None = None
    body_source: str | None = None
    body_source_format: str | None = None


@dataclass(frozen=True)
class RunObservations:
    """Everything one run observed, in source-neutral form."""

    run_id: str
    scope: str
    finished_at: datetime | None
    contents: list[ObservedContent]
    comments: list[ObservedComment]


# Sync observations (Stage 1 and 2): everything the store needs from one run.
# Payloads are opaque here: the adapter has already removed unneeded personal
# fields, and nothing outside the adapter reads a key inside them.

SHAPE_COMMENT: str = "COMMENT"
SHAPE_PLACEHOLDER: str = "PLACEHOLDER"
SHAPE_UNEXPECTED: str = "UNEXPECTED"


@dataclass(frozen=True)
class SourcePayload:
    """What the source returned for one object, reduced to what the experiment keeps."""

    source_type: str
    source_object_id: str
    payload: dict[str, Any]
    payload_hash: str
    source_created_at: datetime | None
    source_updated_at: datetime | None
    # Value state of source_updated_at: PRESENT, SOURCE_EMPTY, or NOT_EXPOSED.
    source_updated_at_state: str


@dataclass(frozen=True)
class SyncedIdentity:
    """A platform-local identity as it arrived with a post or comment."""

    source_user_id: str
    handle: str | None
    display_name: str | None


@dataclass(frozen=True)
class SyncedContent:
    """A post as observed in one sync run."""

    source_object_id: str
    title: str | None
    canonical_url: str | None
    published_at: datetime | None
    author: SyncedIdentity | None
    reported_comment_count: int | None
    # Whether the post's whole comment tree was fetched in this run. Only a
    # complete fetch counts toward deletion by absence (ADR-009).
    comments_complete: bool
    source: SourcePayload


@dataclass(frozen=True)
class SyncedComment:
    """A comment node as observed in one sync run, in depth-first order."""

    content_source_object_id: str
    source_object_id: str
    parent_source_object_id: str | None
    created_at: datetime | None
    # SHAPE_COMMENT, SHAPE_PLACEHOLDER (the exact known deletion shape), or
    # SHAPE_UNEXPECTED (authorless or unknown keys, never treated as either).
    shape: str
    author: SyncedIdentity | None
    is_content_author: bool
    body_source: str | None
    body_source_format: str | None
    source: SourcePayload


@dataclass(frozen=True)
class SyncObservations:
    """One saved sync run, ready to ingest."""

    platform: str
    sync_run_id: str
    account_source_user_id: str | None
    scope: str
    adapter_version: str
    ingestion_version: str
    outcome: str
    started_at: datetime | None
    finished_at: datetime | None
    contents: list[SyncedContent]
    comments: list[SyncedComment]
    limitations: list[str]
