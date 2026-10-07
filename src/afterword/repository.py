"""The storage interface (ADR-013, rule 5). Only :mod:`afterword.service` calls it.

Implementations keep their query language to themselves: SQLite SQL lives in
:mod:`afterword.sqlite_store` and nowhere else. Every method is scoped to one
platform connection.
"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import AbstractContextManager
from datetime import datetime
from typing import Protocol

from afterword import domain


class Repository(Protocol):
    """Reads and writes canonical records."""

    def transaction(self) -> AbstractContextManager[None]:
        """Group writes so they all happen or none do.

        :returns: A context manager; leaving it with an exception rolls back.
        """
        ...

    def close(self) -> None:
        """Release the store."""
        ...

    # Connections -------------------------------------------------------------

    def find_connection(
        self, platform: str, account_source_user_id: str
    ) -> domain.PlatformConnection | None:
        """Find the connection for a platform account.

        :param platform: Platform name.
        :param account_source_user_id: The platform's ID for the connected account.
        :returns: The connection, or ``None``.
        """
        ...

    def get_connection(self, connection_id: str) -> domain.PlatformConnection | None:
        """Get a connection by ID.

        :param connection_id: Connection ID.
        :returns: The connection, or ``None``.
        """
        ...

    def list_connections(self) -> list[domain.PlatformConnection]:
        """List every connection.

        :returns: Connections, oldest first.
        """
        ...

    def add_connection(self, connection: domain.PlatformConnection) -> None:
        """Store a new connection.

        :param connection: The connection.
        """
        ...

    def forget_connection(self, connection_id: str) -> dict[str, int]:
        """Delete every record of a connection, the connection included.

        :param connection_id: Connection ID.
        :returns: Rows deleted, by record type.
        """
        ...

    def count_connection(self, connection_id: str) -> dict[str, int]:
        """Count a connection's records, by type.

        :param connection_id: Connection ID.
        :returns: Row counts.
        """
        ...

    def lifecycle_counts(self, connection_id: str) -> dict[str, dict[str, int]]:
        """Count a connection's comments and lifecycle events, for a status report.

        :param connection_id: Connection ID.
        :returns: Counts only, under ``comments`` (keyed ``<state> <who>``, who being
            ``others``, ``author``, or ``unknown``), ``events`` (keyed
            ``<run> <from>-><to> <reason>``), and ``content_check`` (deleted or
            purged comments still holding text, and unpurged source records of
            purged comments; both should be 0).
        """
        ...

    # Sync runs ---------------------------------------------------------------

    def get_sync_run(self, connection_id: str, sync_run_id: str) -> domain.SyncRun | None:
        """Get an ingested run.

        :param connection_id: Connection ID.
        :param sync_run_id: Run ID.
        :returns: The run, or ``None``.
        """
        ...

    def latest_sync_run(self, connection_id: str) -> domain.SyncRun | None:
        """Get the most recently finished ingested run.

        :param connection_id: Connection ID.
        :returns: The run, or ``None``.
        """
        ...

    def add_sync_run(self, run: domain.SyncRun) -> None:
        """Store an ingested run.

        :param run: The run.
        """
        ...

    # Source records ----------------------------------------------------------

    def add_source_records(self, records: Iterable[domain.SourceRecord]) -> None:
        """Append source records.

        :param records: Records to append.
        """
        ...

    def purge_source_records(
        self, connection_id: str, source_object_id: str, *, keep: str | None, purged_at: datetime
    ) -> int:
        """Remove the raw payloads of a comment's source records.

        :param connection_id: Connection ID.
        :param source_object_id: The comment's source ID.
        :param keep: A record exempt from the purge (a deletion placeholder's own).
        :param purged_at: Purge time.
        :returns: Records purged.
        """
        ...

    # Posts, identities, comments ---------------------------------------------

    def contents(self, connection_id: str) -> dict[str, domain.ContentItem]:
        """Get a connection's posts.

        :param connection_id: Connection ID.
        :returns: Posts by ID.
        """
        ...

    def put_contents(self, items: Iterable[domain.ContentItem]) -> None:
        """Insert or replace posts.

        :param items: Posts.
        """
        ...

    def put_identities(self, identities: Iterable[domain.PlatformIdentity]) -> None:
        """Insert or replace platform identities.

        :param identities: Identities.
        """
        ...

    def comments(
        self, connection_id: str, *, content_ids: Iterable[str] | None = None
    ) -> dict[str, domain.Comment]:
        """Get a connection's comments, optionally only those on some posts.

        :param connection_id: Connection ID.
        :param content_ids: Restrict to these posts; ``None`` for all.
        :returns: Comments by ID.
        """
        ...

    def put_comments(self, comments: Iterable[domain.Comment]) -> None:
        """Insert or replace comments.

        :param comments: Comments.
        """
        ...

    def add_lifecycle_events(self, events: Iterable[domain.LifecycleEvent]) -> None:
        """Append lifecycle events.

        :param events: Events.
        """
        ...

    # Classification and priority ---------------------------------------------

    def find_classification(
        self, connection_id: str, comment_id: str, key: domain.CacheKey, outcomes: Iterable[str]
    ) -> domain.Classification | None:
        """Find the latest classification of a comment with a given cache key and outcome.

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :param key: Cache key.
        :param outcomes: Acceptable outcomes (``OK`` and ``MALFORMED`` are reused).
        :returns: The classification, or ``None``.
        """
        ...

    def classifications(self, connection_id: str, comment_id: str) -> list[domain.Classification]:
        """List a comment's classifications, oldest first.

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Classifications.
        """
        ...

    def add_classification(self, classification: domain.Classification) -> None:
        """Store a classification.

        :param classification: The classification.
        """
        ...

    def purge_classifications(self, connection_id: str, comment_id: str) -> int:
        """Remove model text derived from a comment (raw output, explanation).

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Classifications purged.
        """
        ...

    def find_priority(
        self, classification_id: str, policy_version: str, tier: str, rules_fired: tuple[str, ...]
    ) -> domain.PriorityAssignment | None:
        """Find an identical assignment already recorded for a classification.

        :param classification_id: Classification ID.
        :param policy_version: Policy version.
        :param tier: Tier.
        :param rules_fired: Rules fired, in policy order.
        :returns: The assignment, or ``None``.
        """
        ...

    def add_priority_assignment(self, assignment: domain.PriorityAssignment) -> None:
        """Store a priority assignment.

        :param assignment: The assignment.
        """
        ...
