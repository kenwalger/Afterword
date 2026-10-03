"""DEV payload interpretation.

Together with the client and the probe, the only code that knows DEV field
names (`id_code`, `children`, `user.user_id`, `comments_count`, ...). It turns
raw DEV responses into source-neutral observations (ADR-001).
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from afterword.observations import ObservedComment, ObservedContent, RunObservations

# Raw file names inside one probe run directory.
RUN_FILE: str = "run.json"
ME_FILE: str = "users-me.json"
ARTICLE_PAGE_GLOB: str = "articles-page-*.json"
ARTICLES_ALL_FILE: str = "articles-all.json"


def article_file(article_id: int) -> str:
    """Return the raw file name for a single-article fetch.

    :param article_id: DEV article ID.
    :returns: File name inside a run directory.
    """
    return f"article-{article_id}.json"


def comments_file(article_id: int, suffix: str = "") -> str:
    """Return the raw file name for an article's comment tree.

    :param article_id: DEV article ID.
    :param suffix: Variant marker, such as ``-unauthenticated``.
    :returns: File name inside a run directory.
    """
    return f"comments-a{article_id}{suffix}.json"


_EDIT_KEY: re.Pattern[str] = re.compile(r"edit|updated|modified", re.IGNORECASE)
_PARENT_KEY: re.Pattern[str] = re.compile(r"parent|ancestr|reply_to|in_reply|thread", re.IGNORECASE)
_TAG: re.Pattern[str] = re.compile(r"<[^>]+>")
_PLACEHOLDER_WORDS: tuple[str, ...] = ("deleted", "removed", "hidden")


@dataclass(frozen=True)
class AuthorIdentity:
    """Who wrote something: a DEV user ID and handle, either of which may be absent."""

    user_id: int | None
    username: str | None


@dataclass(frozen=True)
class CommentNode:
    """One flattened comment node with its derived parent and depth."""

    id_code: str | None
    parent_id_code: str | None
    depth: int
    node: dict[str, Any]


def identity_from_me(me: dict[str, Any]) -> AuthorIdentity:
    """Build the account holder's identity from ``/api/users/me``.

    :param me: Parsed response body.
    :returns: The identity, with absent fields as ``None``.
    """
    return AuthorIdentity(user_id=me.get("id"), username=me.get("username"))


def identity_from_user(user: Any) -> AuthorIdentity | None:
    """Build an identity from an embedded ``user`` object.

    :param user: The ``user`` value of an article or comment.
    :returns: The identity, or ``None`` if ``user`` is not an object.
    """
    if not isinstance(user, dict):
        return None
    return AuthorIdentity(user_id=user.get("user_id"), username=user.get("username"))


def is_by(identity: AuthorIdentity, node: dict[str, Any]) -> bool:
    """Report whether a node was written by ``identity``.

    Matches on user ID when both sides have one, otherwise on username.

    :param identity: The identity to test against.
    :param node: An article or comment payload.
    :returns: ``True`` only on a positive match.
    """
    other = identity_from_user(node.get("user"))
    if other is None:
        return False
    if identity.user_id is not None and other.user_id is not None:
        return identity.user_id == other.user_id
    if identity.username and other.username:
        return identity.username == other.username
    return False


def content_author(article: dict[str, Any], fallback: AuthorIdentity) -> AuthorIdentity:
    """Return the author of an article, falling back to the account holder.

    :param article: Article payload.
    :param fallback: Identity used when the article has no usable ``user``.
    :returns: The article author's identity.
    """
    return identity_from_user(article.get("user")) or fallback


def flatten_comments(roots: Any) -> list[CommentNode]:
    """Flatten a DEV comment tree depth first. Depth 0 is top level.

    :param roots: A list of top-level comments, or a single comment object.
    :returns: Nodes in depth-first order, so parents precede their children.
    """
    if isinstance(roots, dict):
        roots = [roots]
    if not isinstance(roots, list):
        return []
    out: list[CommentNode] = []

    def visit(node: Any, parent: str | None, depth: int) -> None:
        if not isinstance(node, dict):
            return
        id_code = node.get("id_code")
        out.append(CommentNode(id_code, parent, depth, node))
        for child in node.get("children") or []:
            visit(child, id_code, depth + 1)

    for root in roots:
        visit(root, None, 0)
    return out


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an RFC 3339 timestamp that carries a timezone.

    :param value: Raw field value.
    :returns: The timestamp, or ``None`` if absent, unparsable, or naive.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def edit_key_candidates(keys: set[str]) -> list[str]:
    """Return key names that look like edit timestamps.

    :param keys: Observed key names.
    :returns: Matching names, sorted.
    """
    return sorted(k for k in keys if _EDIT_KEY.search(k))


def parent_key_candidates(keys: set[str]) -> list[str]:
    """Return key names that look like explicit parent references.

    :param keys: Observed key names.
    :returns: Matching names, sorted.
    """
    return sorted(k for k in keys if _PARENT_KEY.search(k))


AI_DISCLOSURE_KEYS: tuple[str, str] = ("ai_disclosure_label", "ai_disclosure_level")
# Values are reported only when they look like platform enum tokens, so a
# free-text value could never be echoed into findings.
_ENUM_TOKEN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9 _-]{1,40}$")


def enum_distribution(nodes: list[dict[str, Any]], key: str) -> dict[str, int]:
    """Count the values of ``key``, reporting only enum-like tokens.

    Free text is counted as ``<non-enum value>`` so it can never be echoed.

    :param nodes: Payloads to count over.
    :param key: Field name.
    :returns: Counts by value, including ``<absent>`` and ``<null>``.
    """
    counts: Counter[str] = Counter()
    for node in nodes:
        if key not in node:
            counts["<absent>"] += 1
        elif node[key] is None:
            counts["<null>"] += 1
        elif isinstance(node[key], str) and _ENUM_TOKEN.fullmatch(node[key]):
            counts[node[key]] += 1
        else:
            counts["<non-enum value>"] += 1
    return dict(sorted(counts.items()))


def ai_disclosure_distribution(
    trees: dict[int, list[CommentNode]], authors: dict[int, AuthorIdentity]
) -> dict[str, Any]:
    """Summarize the undocumented AI-disclosure fields.

    :param trees: Flattened comment trees by article ID.
    :param authors: Content author by article ID.
    :returns: Value counts for all comments and for comments from others, plus
        label and level pairs.
    """
    everyone = [n.node for ns in trees.values() for n in ns]
    others = [n.node for aid, ns in trees.items() for n in ns if not is_by(authors[aid], n.node)]
    out: dict[str, Any] = {
        key: {
            "all": enum_distribution(everyone, key),
            "from_others": enum_distribution(others, key),
        }
        for key in AI_DISCLOSURE_KEYS
    }
    pairs = Counter(
        (
            str(n.get(AI_DISCLOSURE_KEYS[0], "<absent>")),
            str(n.get(AI_DISCLOSURE_KEYS[1], "<absent>")),
        )
        for n in everyone
        if all(
            n.get(k) is None or (isinstance(n.get(k), str) and _ENUM_TOKEN.fullmatch(n[k]))
            for k in AI_DISCLOSURE_KEYS
        )
    )
    out["label_level_pairs"] = [
        {"label": label, "level": level, "count": count}
        for (label, level), count in sorted(pairs.items())
    ]
    return out


PLACEHOLDER_KEYS: frozenset[str] = frozenset(
    {"type_of", "id_code", "created_at", "body_html", "user", "children"}
)
COMMENT_KEYS: frozenset[str] = PLACEHOLDER_KEYS | {"ai_disclosure_label", "ai_disclosure_level"}
REQUIRED_USER_KEYS: frozenset[str] = frozenset({"user_id"})


def is_deletion_placeholder(node: dict[str, Any]) -> bool:
    """Report whether a node is DEV's deletion placeholder.

    DEV keeps a deleted comment that has replies as a node whose ``user`` is ``{}``.
    Observed 2026-10-02 (hand test, one author-deleted comment): same ``id_code``,
    ``created_at``, ``type_of``, and ``children``; ``body_html`` replaced with a short
    placeholder; ``user`` an empty object. A deleted leaf disappears entirely.

    Only that exact shape qualifies (ADR-009). Anything else authorless is an
    unexpected shape, never silently treated as a placeholder.

    :param node: Comment payload.
    :returns: ``True`` for the exact placeholder shape.
    """
    return set(node) == PLACEHOLDER_KEYS and node.get("user") == {}


def is_unexpected_shape(node: dict[str, Any]) -> bool:
    """Report whether a node is neither a normal comment nor the known placeholder.

    :param node: Comment payload.
    :returns: ``True`` if keys or ``user`` fall outside the observed shapes.
    """
    if is_deletion_placeholder(node):
        return False
    user = node.get("user")
    return (
        not set(node) >= PLACEHOLDER_KEYS
        or not set(node) <= COMMENT_KEYS
        or not isinstance(user, dict)
        or not set(user) >= REQUIRED_USER_KEYS
    )


def placeholder_like(node: dict[str, Any]) -> bool:
    """Apply a short-body heuristic for deletion placeholders. Used for counts only.

    :param node: Comment payload.
    :returns: ``True`` if the body is short and mentions deletion or removal.
    """
    body = node.get("body_html")
    if not isinstance(body, str):
        return False
    text = _TAG.sub("", body).strip().lower()
    return len(text) <= 60 and any(word in text for word in _PLACEHOLDER_WORDS)


def field_hashes(node: dict[str, Any]) -> dict[str, str]:
    """Hash each field except ``children``, so changes can be named without values.

    :param node: Comment payload.
    :returns: Truncated SHA-256 per field name.
    """
    return {
        key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]
        for key, value in sorted(node.items())
        if key != "children"
    }


def child_ids(node: dict[str, Any]) -> list[str | None]:
    """Return the IDs of a node's direct children.

    :param node: Comment payload.
    :returns: Child IDs in source order.
    """
    return [c.get("id_code") for c in node.get("children") or [] if isinstance(c, dict)]


# Loading a saved probe run -------------------------------------------------


def read_body(path: Path) -> Any:
    """Read the response body from a saved exchange record.

    :param path: Saved record file.
    :returns: The parsed body.
    """
    return json.loads(path.read_text(encoding="utf-8"))["response"]["body"]


def listed_articles(run_dir: Path) -> dict[int, dict[str, Any]]:
    """Read the article listing pages of a saved run.

    :param run_dir: Raw run directory.
    :returns: Listed article payloads by ID, first occurrence kept.
    """
    articles: dict[int, dict[str, Any]] = {}
    sources = sorted(run_dir.glob(ARTICLE_PAGE_GLOB))
    if not sources and (run_dir / ARTICLES_ALL_FILE).exists():
        sources = [run_dir / ARTICLES_ALL_FILE]
    for path in sources:
        body = read_body(path)
        for item in body if isinstance(body, list) else []:
            if isinstance(item, dict) and isinstance(item.get("id"), int):
                articles.setdefault(item["id"], item)
    return articles


def iter_run_comments(
    run_dir: Path, article_ids: list[int]
) -> Iterator[tuple[int, list[CommentNode]]]:
    """Yield the flattened comment tree of each article in a saved run.

    :param run_dir: Raw run directory.
    :param article_ids: Articles to read; those without a saved tree are skipped.
    :yields: Pairs of article ID and flattened nodes.
    """
    for article_id in article_ids:
        path = run_dir / comments_file(article_id)
        if path.exists():
            yield article_id, flatten_comments(read_body(path))


def _run_articles(run_dir: Path, article_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Article payloads for a run, from the listing pages or single fetches."""
    listed = listed_articles(run_dir)
    articles = {}
    for article_id in article_ids:
        article = listed.get(article_id)
        single = run_dir / article_file(article_id)
        if article is None and single.exists():
            article = read_body(single)
        articles[article_id] = article or {}
    return articles


def _run_authors(run_dir: Path, articles: dict[int, dict[str, Any]]) -> dict[int, AuthorIdentity]:
    me = identity_from_me(read_body(run_dir / ME_FILE))
    return {aid: content_author(article, me) for aid, article in articles.items()}


def run_trees_and_authors(
    run_dir: Path,
) -> tuple[dict[int, list[CommentNode]], dict[int, AuthorIdentity]]:
    """Load comment trees and content authors for a saved run, for derived findings.

    :param run_dir: Raw run directory.
    :returns: Flattened trees by article ID, and content authors by article ID.
    """
    run = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    articles = _run_articles(run_dir, run["article_ids"])
    return dict(iter_run_comments(run_dir, run["article_ids"])), _run_authors(run_dir, articles)


def _edited_at(run_dir: Path, article_id: int, article: dict[str, Any]) -> datetime | None:
    # List items carry no edit time; only a single-article fetch does.
    edited = parse_timestamp(article.get("edited_at"))
    single = run_dir / article_file(article_id)
    if edited is None and single.exists():
        body = read_body(single)
        edited = parse_timestamp(body.get("edited_at")) if isinstance(body, dict) else None
    return edited


def _author_ref(node: dict[str, Any]) -> str | None:
    user = node.get("user")
    if isinstance(user, dict) and user.get("user_id") is not None:
        return str(user["user_id"])
    return None


def load_run(run_dir: Path, *, include_text: bool = False) -> RunObservations:
    """Load source-neutral observations for a saved run.

    :param run_dir: Raw run directory.
    :param include_text: Also load titles, comment bodies, and author references.
    :returns: The run's contents and comments.
    """
    run = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    article_ids: list[int] = run["article_ids"]
    articles = _run_articles(run_dir, article_ids)
    authors = _run_authors(run_dir, articles)

    contents = []
    for article_id, article in articles.items():
        count = article.get("comments_count")
        title = article.get("title") if include_text else None
        contents.append(
            ObservedContent(
                content_ref=str(article_id),
                published_at=parse_timestamp(article.get("published_at")),
                reported_comment_count=count if isinstance(count, int) else None,
                title=title if isinstance(title, str) else None,
                edited_at=_edited_at(run_dir, article_id, article),
            )
        )

    comments = []
    for article_id, nodes in iter_run_comments(run_dir, article_ids):
        for n in nodes:
            placeholder = is_deletion_placeholder(n.node)
            body = n.node.get("body_html") if include_text and not placeholder else None
            comments.append(
                ObservedComment(
                    content_ref=str(article_id),
                    source_object_id=str(n.id_code),
                    parent_source_object_id=n.parent_id_code,
                    depth=n.depth,
                    created_at=parse_timestamp(n.node.get("created_at")),
                    is_content_author=is_by(authors[article_id], n.node),
                    is_deletion_placeholder=placeholder,
                    is_unexpected_shape=is_unexpected_shape(n.node),
                    author_ref=_author_ref(n.node) if include_text else None,
                    body_source=body if isinstance(body, str) else None,
                    body_source_format="HTML" if isinstance(body, str) else None,
                )
            )
    return RunObservations(
        run_id=run["run_id"],
        scope=run["scope"],
        finished_at=parse_timestamp(run.get("finished_at")),
        contents=contents,
        comments=comments,
    )


# Identity terms for the pre-commit scan ------------------------------------

IDENTITY_FIELDS: tuple[str, ...] = ("username", "name", "github_username", "twitter_username")


@dataclass(frozen=True)
class IdentityTerms:
    """Identity strings found in saved runs. Held in memory only, never printed."""

    author: frozenset[str]
    others: frozenset[str]
    author_emails: frozenset[str]
    runs_read: int


def _iter_users(value: Any) -> Iterator[dict[str, Any]]:
    stack = [value]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            if isinstance(v.get("user"), dict):
                yield v["user"]
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)


def identity_terms(raw_root: Path) -> IdentityTerms:
    """Collect every handle and display name in every saved run, split by content author.

    :param raw_root: Directory holding one subdirectory per raw run.
    :returns: Author terms, other commenters' terms, author emails, and the number of runs read.
    """
    author: set[str] = set()
    others: set[str] = set()
    emails: set[str] = set()
    runs = 0
    run_dirs = sorted(p for p in raw_root.iterdir() if p.is_dir()) if raw_root.exists() else []
    for run_dir in run_dirs:
        if not (run_dir / ME_FILE).exists():
            continue
        runs += 1
        me = read_body(run_dir / ME_FILE)
        me_id = me.get("id") if isinstance(me, dict) else None
        if isinstance(me, dict) and isinstance(me.get("email"), str):
            emails.add(me["email"])
        for path in run_dir.glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            body = record.get("response", {}).get("body") if isinstance(record, dict) else None
            for user in _iter_users(body):
                target = author if me_id is not None and user.get("user_id") == me_id else others
                for field in IDENTITY_FIELDS:
                    value = user.get(field)
                    if isinstance(value, str) and value.strip():
                        target.add(value.strip())
    return IdentityTerms(frozenset(author), frozenset(others), frozenset(emails), runs)
