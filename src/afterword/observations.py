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


@dataclass(frozen=True)
class ObservedContent:
    """A published post, as observed in one run."""

    content_ref: str
    published_at: datetime | None
    reported_comment_count: int | None
    title: str | None = None
    # Last edit of the post, when the run captured it (not every run does).
    edited_at: datetime | None = None


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
