"""Source-neutral observations consumed outside the adapter boundary.

These are deliberately smaller than the Stage 2 data model. They carry only
what the Stage 0 volume baseline needs, and nothing platform-specific
(ADR-001).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ObservedContent:
    content_ref: str
    published_at: datetime | None
    reported_comment_count: int | None


@dataclass(frozen=True)
class ObservedComment:
    content_ref: str
    source_object_id: str
    parent_source_object_id: str | None
    depth: int
    created_at: datetime | None
    is_content_author: bool
    # The source still shows this comment's place in the thread, but its content
    # and author were removed upstream (ADR-009). Not a comment from anyone.
    is_deletion_placeholder: bool = False


@dataclass(frozen=True)
class RunObservations:
    run_id: str
    scope: str
    finished_at: datetime | None
    contents: list[ObservedContent]
    comments: list[ObservedComment]
