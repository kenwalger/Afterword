"""Read a saved DEV probe run as sync observations for the store (Stages 1 and 2).

The only code that turns DEV payloads into :class:`afterword.observations.SyncObservations`.
Payloads are reduced before they leave the adapter: a comment keeps its own
fields and an author reduced to ``user_id``, ``username``, and ``name``; a post
keeps the fields a ContentItem needs. Profile images, other platform handles,
websites, and post bodies are dropped as unneeded personal or bulk fields
(``DATA-MODEL.md``, SourceRecord).

Nothing here reads comment text beyond passing ``body_html`` through.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from afterword.adapters.dev import records
from afterword.observations import (
    SHAPE_COMMENT,
    SHAPE_PLACEHOLDER,
    SHAPE_UNEXPECTED,
    SourcePayload,
    SyncedComment,
    SyncedContent,
    SyncedIdentity,
    SyncObservations,
)

PLATFORM: str = "dev"
INGESTION_VERSION: str = "dev-sync-0.1"

_USER_KEEP: tuple[str, ...] = ("user_id", "username", "name")
_ARTICLE_KEEP: tuple[str, ...] = (
    "type_of",
    "id",
    "title",
    "url",
    "canonical_url",
    "published_at",
    "created_at",
    "edited_at",
    "comments_count",
    "user",
)


def _reduce_user(user: Any) -> Any:
    if not isinstance(user, dict):
        return user
    return {k: user[k] for k in _USER_KEEP if k in user}


def reduce_comment(node: dict[str, Any]) -> dict[str, Any]:
    """Keep a comment's own fields, without its children and with a reduced author.

    :param node: Comment payload.
    :returns: A new dict; the placeholder's empty ``user`` stays empty.
    """
    out = {k: v for k, v in node.items() if k != "children"}
    if "user" in out:
        out["user"] = _reduce_user(out["user"])
    return out


def reduce_article(article: dict[str, Any]) -> dict[str, Any]:
    """Keep the post fields a ContentItem needs.

    :param article: Article payload.
    :returns: A new dict.
    """
    out = {k: article[k] for k in _ARTICLE_KEEP if k in article}
    if "user" in out:
        out["user"] = _reduce_user(out["user"])
    return out


def payload_hash(payload: dict[str, Any]) -> str:
    """Hash a reduced payload canonically.

    :param payload: Reduced payload.
    :returns: Lowercase hex SHA-256 of its sorted, compact JSON.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _identity(user: Any) -> SyncedIdentity | None:
    if not isinstance(user, dict) or user.get("user_id") is None:
        return None
    handle, name = user.get("username"), user.get("name")
    return SyncedIdentity(
        source_user_id=str(user["user_id"]),
        handle=handle if isinstance(handle, str) else None,
        display_name=name if isinstance(name, str) else None,
    )


def _ok_body(path: Path) -> tuple[bool, Any]:
    if not path.exists():
        return False, None
    record = json.loads(path.read_text(encoding="utf-8"))
    response = record.get("response", {})
    ok = response.get("status") == 200 and response.get("body_is_json", True)
    return ok, response.get("body")


def _article(run_dir: Path, article_id: int, listed: dict[int, dict[str, Any]]) -> dict[str, Any]:
    ok, single = _ok_body(run_dir / records.article_file(article_id))
    if ok and isinstance(single, dict):
        return single
    return listed.get(article_id, {"id": article_id})


def _content(article: dict[str, Any], article_id: int, comments_complete: bool) -> SyncedContent:
    reduced = reduce_article(article)
    edited = records.parse_timestamp(article.get("edited_at"))
    title, url = article.get("title"), article.get("canonical_url") or article.get("url")
    count = article.get("comments_count")
    return SyncedContent(
        source_object_id=str(article_id),
        title=title if isinstance(title, str) else None,
        canonical_url=url if isinstance(url, str) else None,
        published_at=records.parse_timestamp(article.get("published_at")),
        author=_identity(article.get("user")),
        reported_comment_count=count if isinstance(count, int) else None,
        comments_complete=comments_complete,
        source=SourcePayload(
            source_type="content",
            source_object_id=str(article_id),
            payload=reduced,
            payload_hash=payload_hash(reduced),
            source_created_at=records.parse_timestamp(article.get("published_at")),
            source_updated_at=edited,
            source_updated_at_state="PRESENT" if edited else "SOURCE_EMPTY",
        ),
    )


def _comment(
    article_id: int, n: records.CommentNode, author: records.AuthorIdentity
) -> SyncedComment:
    node = n.node
    if records.is_deletion_placeholder(node):
        shape = SHAPE_PLACEHOLDER
    elif records.is_unexpected_shape(node):
        shape = SHAPE_UNEXPECTED
    else:
        shape = SHAPE_COMMENT
    reduced = reduce_comment(node)
    body = node.get("body_html") if shape == SHAPE_COMMENT else None
    created = records.parse_timestamp(node.get("created_at"))
    return SyncedComment(
        content_source_object_id=str(article_id),
        source_object_id=str(n.id_code),
        parent_source_object_id=None if n.parent_id_code is None else str(n.parent_id_code),
        created_at=created,
        shape=shape,
        author=_identity(node.get("user")) if shape == SHAPE_COMMENT else None,
        is_content_author=shape == SHAPE_COMMENT and records.is_by(author, node),
        body_source=body if isinstance(body, str) else None,
        body_source_format="HTML" if isinstance(body, str) else None,
        source=SourcePayload(
            source_type="comment",
            source_object_id=str(n.id_code),
            payload=reduced,
            payload_hash=payload_hash(reduced),
            source_created_at=created,
            source_updated_at=None,
            # DEV comments carry no edit time (verified 2026-10-02).
            source_updated_at_state="NOT_EXPOSED",
        ),
    )


def load_sync(run_dir: Path) -> SyncObservations:
    """Read one saved probe run for ingestion.

    :param run_dir: Raw run directory.
    :returns: Posts, comments in depth-first order, and the run's limitations.
    """
    run = json.loads((run_dir / records.RUN_FILE).read_text(encoding="utf-8"))
    article_ids: list[int] = run.get("article_ids", [])
    _, me_body = _ok_body(run_dir / records.ME_FILE)
    me = records.identity_from_me(me_body if isinstance(me_body, dict) else {})
    listed = records.listed_articles(run_dir)
    limitations: list[str] = []
    contents: list[SyncedContent] = []
    comments: list[SyncedComment] = []
    for article_id in article_ids:
        article = _article(run_dir, article_id, listed)
        ok, tree = _ok_body(run_dir / records.comments_file(article_id))
        complete = ok and isinstance(tree, list)
        if not complete:
            limitations.append(f"comments for post {article_id} not fetched in full")
        contents.append(_content(article, article_id, complete))
        author = records.content_author(article, me)
        for n in records.flatten_comments(tree) if complete else []:
            if n.id_code is None:
                limitations.append(f"post {article_id}: a comment node without an ID")
                continue
            comments.append(_comment(article_id, n, author))
    return SyncObservations(
        platform=PLATFORM,
        sync_run_id=str(run["run_id"]),
        account_source_user_id=None if me.user_id is None else str(me.user_id),
        scope=str(run.get("scope")),
        adapter_version=str(run.get("adapter_version")),
        ingestion_version=INGESTION_VERSION,
        outcome=str(run.get("outcome")),
        started_at=records.parse_timestamp(run.get("started_at")),
        finished_at=records.parse_timestamp(run.get("finished_at")),
        contents=contents,
        comments=comments,
        limitations=limitations,
    )
