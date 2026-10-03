"""SQLite implementation of :class:`afterword.repository.Repository` (stdlib ``sqlite3``).

The only module that contains SQL. Timestamps are stored as RFC 3339 text in
UTC with an explicit offset; lists and maps as JSON text; booleans as 0 or 1.
``secure_delete`` is on, so purged and forgotten content is overwritten in the
file rather than left in free pages.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from afterword import domain

SCHEMA_VERSION: int = 1

_SCHEMA: str = """
CREATE TABLE IF NOT EXISTS connections (
    connection_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    account_source_user_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (platform, account_source_user_id)
);
CREATE TABLE IF NOT EXISTS sync_runs (
    connection_id TEXT NOT NULL,
    sync_run_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    scope TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    outcome TEXT NOT NULL,
    limitations_observed TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (connection_id, sync_run_id)
);
CREATE TABLE IF NOT EXISTS source_records (
    source_record_id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    sync_run_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_object_id TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    source_created_at TEXT,
    source_updated_at TEXT,
    source_updated_at_state TEXT NOT NULL,
    raw_payload TEXT,
    payload_hash TEXT NOT NULL,
    ingestion_version TEXT NOT NULL,
    purged_at TEXT
);
CREATE INDEX IF NOT EXISTS source_records_object
    ON source_records (connection_id, source_type, source_object_id);
CREATE TABLE IF NOT EXISTS platform_identities (
    connection_id TEXT NOT NULL,
    platform_identity_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_user_id TEXT NOT NULL,
    handle TEXT,
    display_name TEXT,
    last_observed_at TEXT NOT NULL,
    PRIMARY KEY (connection_id, platform_identity_id)
);
CREATE TABLE IF NOT EXISTS content_items (
    connection_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_object_id TEXT NOT NULL,
    author_platform_identity_id TEXT,
    title TEXT,
    canonical_url TEXT,
    canonical_url_state TEXT NOT NULL,
    published_at TEXT,
    source_record_id TEXT NOT NULL,
    current_payload_hash TEXT NOT NULL,
    PRIMARY KEY (connection_id, content_id)
);
CREATE TABLE IF NOT EXISTS comments (
    connection_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_object_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    parent_comment_id TEXT,
    parent_comment_id_state TEXT NOT NULL,
    thread_root_comment_id TEXT NOT NULL,
    author_platform_identity_id TEXT,
    author_state TEXT NOT NULL,
    is_content_author INTEGER,
    is_content_author_state TEXT NOT NULL,
    body_source TEXT,
    body_source_format TEXT,
    body_text TEXT,
    normalization_version TEXT,
    body_text_hash TEXT,
    created_at TEXT,
    updated_at_state TEXT NOT NULL,
    first_observed_at TEXT NOT NULL,
    last_observed_at TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    deletion_evidence TEXT NOT NULL,
    consecutive_absences INTEGER NOT NULL,
    current_source_record_id TEXT,
    current_payload_hash TEXT,
    PRIMARY KEY (connection_id, comment_id)
);
CREATE INDEX IF NOT EXISTS comments_content ON comments (connection_id, content_id);
CREATE TABLE IF NOT EXISTS lifecycle_events (
    event_id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    sync_run_id TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    reason TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS classifications (
    classification_id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    comment_source_record_id TEXT,
    input_hash TEXT NOT NULL,
    model_provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_digest TEXT,
    model_digest_state TEXT NOT NULL,
    prompt_version TEXT,
    taxonomy_version TEXT NOT NULL,
    primary_class TEXT,
    flags TEXT NOT NULL,
    flags_by_source TEXT NOT NULL,
    confidence TEXT,
    confidence_state TEXT NOT NULL,
    explanation TEXT,
    classifier_kind TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    precheck_version TEXT NOT NULL,
    input_fields_sent TEXT NOT NULL,
    raw_output TEXT,
    latency_ms INTEGER,
    classified_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS classifications_key
    ON classifications (connection_id, comment_id, input_hash, model_provider, model_id);
CREATE TABLE IF NOT EXISTS priority_assignments (
    priority_assignment_id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    comment_id TEXT NOT NULL,
    classification_id TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    tier TEXT NOT NULL,
    rule_applied TEXT NOT NULL,
    rules_fired TEXT NOT NULL,
    assigned_at TEXT NOT NULL
);
"""

# Every table holding a connection's records, in deletion order.
_TABLES: tuple[str, ...] = (
    "priority_assignments",
    "classifications",
    "lifecycle_events",
    "comments",
    "content_items",
    "platform_identities",
    "source_records",
    "sync_runs",
    "connections",
)


def _ts(moment: datetime | None) -> str | None:
    return None if moment is None else domain.utc(moment).isoformat()


def _dt(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value)


def _req_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _bool(value: int | None) -> bool | None:
    return None if value is None else bool(value)


class SqliteRepository:
    """A store in one SQLite file."""

    def __init__(self, path: Path | str) -> None:
        """Open (and if needed create) a store.

        :param path: Database file, or ``:memory:``.
        :raises RuntimeError: If the file has a newer schema than this code knows.
        """
        if isinstance(path, Path):
            path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA secure_delete = ON")
        self.db.execute("PRAGMA foreign_keys = ON")
        version = int(self.db.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise RuntimeError(f"store schema {version} is newer than {SCHEMA_VERSION}")
        self.db.executescript(_SCHEMA)
        self.db.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self._depth = 0

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Group writes; nested calls join the outer transaction.

        :yields: Nothing.
        :raises BaseException: Whatever the block raised, after rolling back.
        """
        if self._depth:
            self._depth += 1
            try:
                yield
            finally:
                self._depth -= 1
            return
        self.db.execute("BEGIN")
        self._depth = 1
        try:
            yield
        except BaseException:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")
        finally:
            self._depth = 0

    def close(self) -> None:
        """Close the file."""
        self.db.close()

    def _insert(self, table: str, row: dict[str, Any], *, replace: bool = False) -> None:
        verb = "INSERT OR REPLACE" if replace else "INSERT"
        names = ", ".join(row)
        marks = ", ".join("?" for _ in row)
        self.db.execute(f"{verb} INTO {table} ({names}) VALUES ({marks})", tuple(row.values()))

    # Connections -------------------------------------------------------------

    @staticmethod
    def _connection(row: sqlite3.Row) -> domain.PlatformConnection:
        return domain.PlatformConnection(
            row["connection_id"],
            row["platform"],
            row["account_source_user_id"],
            _req_dt(row["created_at"]),
        )

    def find_connection(
        self, platform: str, account_source_user_id: str
    ) -> domain.PlatformConnection | None:
        """Find the connection for a platform account.

        :param platform: Platform name.
        :param account_source_user_id: The platform's ID for the connected account.
        :returns: The connection, or ``None``.
        """
        row = self.db.execute(
            "SELECT * FROM connections WHERE platform = ? AND account_source_user_id = ?",
            (platform, account_source_user_id),
        ).fetchone()
        return None if row is None else self._connection(row)

    def get_connection(self, connection_id: str) -> domain.PlatformConnection | None:
        """Get a connection by ID.

        :param connection_id: Connection ID.
        :returns: The connection, or ``None``.
        """
        row = self.db.execute(
            "SELECT * FROM connections WHERE connection_id = ?", (connection_id,)
        ).fetchone()
        return None if row is None else self._connection(row)

    def list_connections(self) -> list[domain.PlatformConnection]:
        """List every connection.

        :returns: Connections, oldest first.
        """
        rows = self.db.execute("SELECT * FROM connections ORDER BY created_at").fetchall()
        return [self._connection(r) for r in rows]

    def add_connection(self, connection: domain.PlatformConnection) -> None:
        """Store a new connection.

        :param connection: The connection.
        """
        self._insert(
            "connections",
            {
                "connection_id": connection.connection_id,
                "platform": connection.platform,
                "account_source_user_id": connection.account_source_user_id,
                "created_at": _ts(connection.created_at),
            },
        )

    def count_connection(self, connection_id: str) -> dict[str, int]:
        """Count a connection's records, by type.

        :param connection_id: Connection ID.
        :returns: Row counts.
        """
        return {
            table: int(
                self.db.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE connection_id = ?", (connection_id,)
                ).fetchone()[0]
            )
            for table in _TABLES
        }

    def forget_connection(self, connection_id: str) -> dict[str, int]:
        """Delete every record of a connection, the connection included.

        :param connection_id: Connection ID.
        :returns: Rows deleted, by record type.
        """
        deleted = {}
        with self.transaction():
            for table in _TABLES:
                cur = self.db.execute(
                    f"DELETE FROM {table} WHERE connection_id = ?", (connection_id,)
                )
                deleted[table] = cur.rowcount
        self.db.execute("VACUUM")
        return deleted

    # Sync runs ---------------------------------------------------------------

    @staticmethod
    def _run(row: sqlite3.Row) -> domain.SyncRun:
        return domain.SyncRun(
            connection_id=row["connection_id"],
            sync_run_id=row["sync_run_id"],
            platform=row["platform"],
            started_at=_dt(row["started_at"]),
            finished_at=_dt(row["finished_at"]),
            scope=row["scope"],
            adapter_version=row["adapter_version"],
            outcome=row["outcome"],
            limitations_observed=tuple(json.loads(row["limitations_observed"])),
            ingested_at=_req_dt(row["ingested_at"]),
        )

    def get_sync_run(self, connection_id: str, sync_run_id: str) -> domain.SyncRun | None:
        """Get an ingested run.

        :param connection_id: Connection ID.
        :param sync_run_id: Run ID.
        :returns: The run, or ``None``.
        """
        row = self.db.execute(
            "SELECT * FROM sync_runs WHERE connection_id = ? AND sync_run_id = ?",
            (connection_id, sync_run_id),
        ).fetchone()
        return None if row is None else self._run(row)

    def latest_sync_run(self, connection_id: str) -> domain.SyncRun | None:
        """Get the most recently finished ingested run.

        :param connection_id: Connection ID.
        :returns: The run, or ``None``.
        """
        row = self.db.execute(
            "SELECT * FROM sync_runs WHERE connection_id = ? "
            "ORDER BY finished_at DESC, ingested_at DESC LIMIT 1",
            (connection_id,),
        ).fetchone()
        return None if row is None else self._run(row)

    def add_sync_run(self, run: domain.SyncRun) -> None:
        """Store an ingested run.

        :param run: The run.
        """
        self._insert(
            "sync_runs",
            {
                "connection_id": run.connection_id,
                "sync_run_id": run.sync_run_id,
                "platform": run.platform,
                "started_at": _ts(run.started_at),
                "finished_at": _ts(run.finished_at),
                "scope": run.scope,
                "adapter_version": run.adapter_version,
                "outcome": run.outcome,
                "limitations_observed": json.dumps(list(run.limitations_observed)),
                "ingested_at": _ts(run.ingested_at),
            },
        )

    # Source records ----------------------------------------------------------

    def add_source_records(self, records: Iterable[domain.SourceRecord]) -> None:
        """Append source records.

        :param records: Records to append.
        """
        for r in records:
            self._insert(
                "source_records",
                {
                    "source_record_id": r.source_record_id,
                    "connection_id": r.connection_id,
                    "sync_run_id": r.sync_run_id,
                    "platform": r.platform,
                    "source_type": r.source_type,
                    "source_object_id": r.source_object_id,
                    "observed_at": _ts(r.observed_at),
                    "source_created_at": _ts(r.source_created_at),
                    "source_updated_at": _ts(r.source_updated_at),
                    "source_updated_at_state": r.source_updated_at_state,
                    "raw_payload": r.raw_payload,
                    "payload_hash": r.payload_hash,
                    "ingestion_version": r.ingestion_version,
                    "purged_at": _ts(r.purged_at),
                },
            )

    def source_records(
        self, connection_id: str, source_object_id: str
    ) -> list[domain.SourceRecord]:
        """List the source records of one object, oldest first.

        :param connection_id: Connection ID.
        :param source_object_id: Source ID.
        :returns: Records.
        """
        rows = self.db.execute(
            "SELECT * FROM source_records WHERE connection_id = ? AND source_object_id = ? "
            "ORDER BY observed_at, rowid",
            (connection_id, source_object_id),
        ).fetchall()
        return [
            domain.SourceRecord(
                source_record_id=r["source_record_id"],
                connection_id=r["connection_id"],
                sync_run_id=r["sync_run_id"],
                platform=r["platform"],
                source_type=r["source_type"],
                source_object_id=r["source_object_id"],
                observed_at=_req_dt(r["observed_at"]),
                source_created_at=_dt(r["source_created_at"]),
                source_updated_at=_dt(r["source_updated_at"]),
                source_updated_at_state=r["source_updated_at_state"],
                raw_payload=r["raw_payload"],
                payload_hash=r["payload_hash"],
                ingestion_version=r["ingestion_version"],
                purged_at=_dt(r["purged_at"]),
            )
            for r in rows
        ]

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
        cur = self.db.execute(
            "UPDATE source_records SET raw_payload = NULL, purged_at = ? "
            "WHERE connection_id = ? AND source_type = 'comment' AND source_object_id = ? "
            "AND source_record_id IS NOT ? AND raw_payload IS NOT NULL",
            (_ts(purged_at), connection_id, source_object_id, keep),
        )
        return cur.rowcount

    # Posts, identities, comments ---------------------------------------------

    def contents(self, connection_id: str) -> dict[str, domain.ContentItem]:
        """Get a connection's posts.

        :param connection_id: Connection ID.
        :returns: Posts by ID.
        """
        rows = self.db.execute(
            "SELECT * FROM content_items WHERE connection_id = ?", (connection_id,)
        ).fetchall()
        return {
            r["content_id"]: domain.ContentItem(
                connection_id=r["connection_id"],
                content_id=r["content_id"],
                platform=r["platform"],
                source_object_id=r["source_object_id"],
                author_platform_identity_id=r["author_platform_identity_id"],
                title=r["title"],
                canonical_url=r["canonical_url"],
                canonical_url_state=r["canonical_url_state"],
                published_at=_dt(r["published_at"]),
                source_record_id=r["source_record_id"],
                current_payload_hash=r["current_payload_hash"],
            )
            for r in rows
        }

    def put_contents(self, items: Iterable[domain.ContentItem]) -> None:
        """Insert or replace posts.

        :param items: Posts.
        """
        for c in items:
            self._insert(
                "content_items",
                {
                    "connection_id": c.connection_id,
                    "content_id": c.content_id,
                    "platform": c.platform,
                    "source_object_id": c.source_object_id,
                    "author_platform_identity_id": c.author_platform_identity_id,
                    "title": c.title,
                    "canonical_url": c.canonical_url,
                    "canonical_url_state": c.canonical_url_state,
                    "published_at": _ts(c.published_at),
                    "source_record_id": c.source_record_id,
                    "current_payload_hash": c.current_payload_hash,
                },
                replace=True,
            )

    def put_identities(self, identities: Iterable[domain.PlatformIdentity]) -> None:
        """Insert or replace platform identities.

        :param identities: Identities.
        """
        for i in identities:
            self._insert(
                "platform_identities",
                {
                    "connection_id": i.connection_id,
                    "platform_identity_id": i.platform_identity_id,
                    "platform": i.platform,
                    "source_user_id": i.source_user_id,
                    "handle": i.handle,
                    "display_name": i.display_name,
                    "last_observed_at": _ts(i.last_observed_at),
                },
                replace=True,
            )

    @staticmethod
    def _comment(r: sqlite3.Row) -> domain.Comment:
        return domain.Comment(
            connection_id=r["connection_id"],
            comment_id=r["comment_id"],
            platform=r["platform"],
            source_object_id=r["source_object_id"],
            content_id=r["content_id"],
            parent_comment_id=r["parent_comment_id"],
            parent_comment_id_state=r["parent_comment_id_state"],
            thread_root_comment_id=r["thread_root_comment_id"],
            author_platform_identity_id=r["author_platform_identity_id"],
            author_state=r["author_state"],
            is_content_author=_bool(r["is_content_author"]),
            is_content_author_state=r["is_content_author_state"],
            body_source=r["body_source"],
            body_source_format=r["body_source_format"],
            body_text=r["body_text"],
            normalization_version=r["normalization_version"],
            body_text_hash=r["body_text_hash"],
            created_at=_dt(r["created_at"]),
            first_observed_at=_req_dt(r["first_observed_at"]),
            last_observed_at=_req_dt(r["last_observed_at"]),
            lifecycle_state=r["lifecycle_state"],
            deletion_evidence=r["deletion_evidence"],
            consecutive_absences=int(r["consecutive_absences"]),
            current_source_record_id=r["current_source_record_id"],
            current_payload_hash=r["current_payload_hash"],
            updated_at_state=r["updated_at_state"],
        )

    def comments(
        self, connection_id: str, *, content_ids: Iterable[str] | None = None
    ) -> dict[str, domain.Comment]:
        """Get a connection's comments, optionally only those on some posts.

        :param connection_id: Connection ID.
        :param content_ids: Restrict to these posts; ``None`` for all.
        :returns: Comments by ID.
        """
        rows = self.db.execute(
            "SELECT * FROM comments WHERE connection_id = ? ORDER BY created_at, comment_id",
            (connection_id,),
        ).fetchall()
        wanted = None if content_ids is None else set(content_ids)
        return {
            r["comment_id"]: self._comment(r)
            for r in rows
            if wanted is None or r["content_id"] in wanted
        }

    def put_comments(self, comments: Iterable[domain.Comment]) -> None:
        """Insert or replace comments.

        :param comments: Comments.
        """
        for c in comments:
            self._insert(
                "comments",
                {
                    "connection_id": c.connection_id,
                    "comment_id": c.comment_id,
                    "platform": c.platform,
                    "source_object_id": c.source_object_id,
                    "content_id": c.content_id,
                    "parent_comment_id": c.parent_comment_id,
                    "parent_comment_id_state": c.parent_comment_id_state,
                    "thread_root_comment_id": c.thread_root_comment_id,
                    "author_platform_identity_id": c.author_platform_identity_id,
                    "author_state": c.author_state,
                    "is_content_author": None
                    if c.is_content_author is None
                    else int(c.is_content_author),
                    "is_content_author_state": c.is_content_author_state,
                    "body_source": c.body_source,
                    "body_source_format": c.body_source_format,
                    "body_text": c.body_text,
                    "normalization_version": c.normalization_version,
                    "body_text_hash": c.body_text_hash,
                    "created_at": _ts(c.created_at),
                    "updated_at_state": c.updated_at_state,
                    "first_observed_at": _ts(c.first_observed_at),
                    "last_observed_at": _ts(c.last_observed_at),
                    "lifecycle_state": c.lifecycle_state,
                    "deletion_evidence": c.deletion_evidence,
                    "consecutive_absences": c.consecutive_absences,
                    "current_source_record_id": c.current_source_record_id,
                    "current_payload_hash": c.current_payload_hash,
                },
                replace=True,
            )

    def add_lifecycle_events(self, events: Iterable[domain.LifecycleEvent]) -> None:
        """Append lifecycle events.

        :param events: Events.
        """
        for e in events:
            self._insert(
                "lifecycle_events",
                {
                    "event_id": e.event_id,
                    "connection_id": e.connection_id,
                    "comment_id": e.comment_id,
                    "sync_run_id": e.sync_run_id,
                    "from_state": e.from_state,
                    "to_state": e.to_state,
                    "reason": e.reason,
                    "occurred_at": _ts(e.occurred_at),
                },
            )

    def lifecycle_events(self, connection_id: str, comment_id: str) -> list[domain.LifecycleEvent]:
        """List a comment's lifecycle events, oldest first.

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Events.
        """
        rows = self.db.execute(
            "SELECT * FROM lifecycle_events WHERE connection_id = ? AND comment_id = ? "
            "ORDER BY occurred_at, rowid",
            (connection_id, comment_id),
        ).fetchall()
        return [
            domain.LifecycleEvent(
                r["event_id"],
                r["connection_id"],
                r["comment_id"],
                r["sync_run_id"],
                r["from_state"],
                r["to_state"],
                r["reason"],
                _req_dt(r["occurred_at"]),
            )
            for r in rows
        ]

    # Classification and priority ---------------------------------------------

    @staticmethod
    def _classification(r: sqlite3.Row) -> domain.Classification:
        return domain.Classification(
            classification_id=r["classification_id"],
            connection_id=r["connection_id"],
            comment_id=r["comment_id"],
            comment_source_record_id=r["comment_source_record_id"],
            key=domain.CacheKey(
                input_hash=r["input_hash"],
                model_provider=r["model_provider"],
                model_id=r["model_id"],
                model_digest=r["model_digest"],
                prompt_version=r["prompt_version"],
                taxonomy_version=r["taxonomy_version"],
            ),
            primary_class=r["primary_class"],
            flags=tuple(json.loads(r["flags"])),
            flags_by_source=json.loads(r["flags_by_source"]),
            confidence=r["confidence"],
            confidence_state=r["confidence_state"],
            explanation=r["explanation"],
            classifier_kind=r["classifier_kind"],
            model_digest_state=r["model_digest_state"],
            normalization_version=r["normalization_version"],
            precheck_version=r["precheck_version"],
            input_fields_sent=tuple(json.loads(r["input_fields_sent"])),
            raw_output=r["raw_output"],
            latency_ms=r["latency_ms"],
            classified_at=_req_dt(r["classified_at"]),
            outcome=r["outcome"],
            error=r["error"],
        )

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
        wanted = list(outcomes)
        marks = ", ".join("?" for _ in wanted)
        row = self.db.execute(
            "SELECT * FROM classifications WHERE connection_id = ? AND comment_id = ? "
            "AND input_hash = ? AND model_provider = ? AND model_id = ? "
            "AND model_digest IS ? AND prompt_version IS ? AND taxonomy_version = ? "
            f"AND outcome IN ({marks}) ORDER BY classified_at DESC, rowid DESC LIMIT 1",
            (
                connection_id,
                comment_id,
                key.input_hash,
                key.model_provider,
                key.model_id,
                key.model_digest,
                key.prompt_version,
                key.taxonomy_version,
                *wanted,
            ),
        ).fetchone()
        return None if row is None else self._classification(row)

    def classifications(self, connection_id: str, comment_id: str) -> list[domain.Classification]:
        """List a comment's classifications, oldest first.

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Classifications.
        """
        rows = self.db.execute(
            "SELECT * FROM classifications WHERE connection_id = ? AND comment_id = ? "
            "ORDER BY classified_at, rowid",
            (connection_id, comment_id),
        ).fetchall()
        return [self._classification(r) for r in rows]

    def add_classification(self, classification: domain.Classification) -> None:
        """Store a classification.

        :param classification: The classification.
        """
        c, k = classification, classification.key
        self._insert(
            "classifications",
            {
                "classification_id": c.classification_id,
                "connection_id": c.connection_id,
                "comment_id": c.comment_id,
                "comment_source_record_id": c.comment_source_record_id,
                "input_hash": k.input_hash,
                "model_provider": k.model_provider,
                "model_id": k.model_id,
                "model_digest": k.model_digest,
                "model_digest_state": c.model_digest_state,
                "prompt_version": k.prompt_version,
                "taxonomy_version": k.taxonomy_version,
                "primary_class": c.primary_class,
                "flags": json.dumps(list(c.flags)),
                "flags_by_source": json.dumps(c.flags_by_source, sort_keys=True),
                "confidence": c.confidence,
                "confidence_state": c.confidence_state,
                "explanation": c.explanation,
                "classifier_kind": c.classifier_kind,
                "normalization_version": c.normalization_version,
                "precheck_version": c.precheck_version,
                "input_fields_sent": json.dumps(list(c.input_fields_sent)),
                "raw_output": c.raw_output,
                "latency_ms": c.latency_ms,
                "classified_at": _ts(c.classified_at),
                "outcome": c.outcome,
                "error": c.error,
            },
        )

    def purge_classifications(self, connection_id: str, comment_id: str) -> int:
        """Remove model text derived from a comment (raw output, explanation).

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Classifications purged.
        """
        cur = self.db.execute(
            "UPDATE classifications SET raw_output = NULL, explanation = NULL "
            "WHERE connection_id = ? AND comment_id = ? "
            "AND (raw_output IS NOT NULL OR explanation IS NOT NULL)",
            (connection_id, comment_id),
        )
        return cur.rowcount

    @staticmethod
    def _priority(r: sqlite3.Row) -> domain.PriorityAssignment:
        return domain.PriorityAssignment(
            priority_assignment_id=r["priority_assignment_id"],
            connection_id=r["connection_id"],
            comment_id=r["comment_id"],
            classification_id=r["classification_id"],
            policy_version=r["policy_version"],
            tier=r["tier"],
            rule_applied=r["rule_applied"],
            rules_fired=tuple(json.loads(r["rules_fired"])),
            assigned_at=_req_dt(r["assigned_at"]),
        )

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
        row = self.db.execute(
            "SELECT * FROM priority_assignments WHERE classification_id = ? "
            "AND policy_version = ? AND tier = ? AND rules_fired = ? LIMIT 1",
            (classification_id, policy_version, tier, json.dumps(list(rules_fired))),
        ).fetchone()
        return None if row is None else self._priority(row)

    def priority_assignments(
        self, connection_id: str, comment_id: str
    ) -> list[domain.PriorityAssignment]:
        """List a comment's priority assignments, oldest first.

        :param connection_id: Connection ID.
        :param comment_id: Comment ID.
        :returns: Assignments.
        """
        rows = self.db.execute(
            "SELECT * FROM priority_assignments WHERE connection_id = ? AND comment_id = ? "
            "ORDER BY assigned_at, rowid",
            (connection_id, comment_id),
        ).fetchall()
        return [self._priority(r) for r in rows]

    def add_priority_assignment(self, assignment: domain.PriorityAssignment) -> None:
        """Store a priority assignment.

        :param assignment: The assignment.
        """
        a = assignment
        self._insert(
            "priority_assignments",
            {
                "priority_assignment_id": a.priority_assignment_id,
                "connection_id": a.connection_id,
                "comment_id": a.comment_id,
                "classification_id": a.classification_id,
                "policy_version": a.policy_version,
                "tier": a.tier,
                "rule_applied": a.rule_applied,
                "rules_fired": json.dumps(list(a.rules_fired)),
                "assigned_at": _ts(a.assigned_at),
            },
        )
