"""DEV payload interpretation.

The only place outside the client that knows DEV field names (`id_code`,
`children`, `user.user_id`, `comments_count`, ...). It turns raw DEV responses
into source-neutral observations (ADR-001).
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
RUN_FILE = "run.json"
ME_FILE = "users-me.json"
ARTICLE_PAGE_GLOB = "articles-page-*.json"
ARTICLES_ALL_FILE = "articles-all.json"


def article_file(article_id: int) -> str:
    return f"article-{article_id}.json"


def comments_file(article_id: int, suffix: str = "") -> str:
    return f"comments-a{article_id}{suffix}.json"


_EDIT_KEY = re.compile(r"edit|updated|modified", re.IGNORECASE)
_PARENT_KEY = re.compile(r"parent|ancestr|reply_to|in_reply|thread", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_PLACEHOLDER_WORDS = ("deleted", "removed", "hidden")


@dataclass(frozen=True)
class AuthorIdentity:
    user_id: int | None
    username: str | None


@dataclass(frozen=True)
class CommentNode:
    id_code: str | None
    parent_id_code: str | None
    depth: int
    node: dict[str, Any]


def identity_from_me(me: dict[str, Any]) -> AuthorIdentity:
    return AuthorIdentity(user_id=me.get("id"), username=me.get("username"))


def identity_from_user(user: Any) -> AuthorIdentity | None:
    if not isinstance(user, dict):
        return None
    return AuthorIdentity(user_id=user.get("user_id"), username=user.get("username"))


def is_by(identity: AuthorIdentity, node: dict[str, Any]) -> bool:
    other = identity_from_user(node.get("user"))
    if other is None:
        return False
    if identity.user_id is not None and other.user_id is not None:
        return identity.user_id == other.user_id
    if identity.username and other.username:
        return identity.username == other.username
    return False


def content_author(article: dict[str, Any], fallback: AuthorIdentity) -> AuthorIdentity:
    return identity_from_user(article.get("user")) or fallback


def flatten_comments(roots: Any) -> list[CommentNode]:
    """Depth-first flatten of a DEV comment tree. Depth 0 is top level."""
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
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def edit_key_candidates(keys: set[str]) -> list[str]:
    return sorted(k for k in keys if _EDIT_KEY.search(k))


def parent_key_candidates(keys: set[str]) -> list[str]:
    return sorted(k for k in keys if _PARENT_KEY.search(k))


AI_DISCLOSURE_KEYS = ("ai_disclosure_label", "ai_disclosure_level")
# Values are reported only when they look like platform enum tokens, so a
# free-text value could never be echoed into findings.
_ENUM_TOKEN = re.compile(r"^[A-Za-z0-9 _-]{1,40}$")


def enum_distribution(nodes: list[dict[str, Any]], key: str) -> dict[str, int]:
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


PLACEHOLDER_KEYS = frozenset({"type_of", "id_code", "created_at", "body_html", "user", "children"})
COMMENT_KEYS = PLACEHOLDER_KEYS | {"ai_disclosure_label", "ai_disclosure_level"}
REQUIRED_USER_KEYS = frozenset({"user_id"})


def is_deletion_placeholder(node: dict[str, Any]) -> bool:
    """DEV keeps a deleted comment that has replies as a node whose `user` is `{}`.

    Observed 2026-10-02 (hand test, one author-deleted comment): same `id_code`,
    `created_at`, `type_of`, and `children`; `body_html` replaced with a short
    placeholder; `user` an empty object. A deleted leaf disappears entirely.

    Only that exact shape qualifies (ADR-009). Anything else authorless is an
    unexpected shape, never silently treated as a placeholder.
    """
    return set(node) == PLACEHOLDER_KEYS and node.get("user") == {}


def is_unexpected_shape(node: dict[str, Any]) -> bool:
    """A comment node that is neither a normal comment nor the known placeholder."""
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
    """Heuristic for a deletion placeholder body. Used for counts only."""
    body = node.get("body_html")
    if not isinstance(body, str):
        return False
    text = _TAG.sub("", body).strip().lower()
    return len(text) <= 60 and any(word in text for word in _PLACEHOLDER_WORDS)


def field_hashes(node: dict[str, Any]) -> dict[str, str]:
    """Per-field hashes, excluding `children`, so changes can be named without values."""
    return {
        key: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]
        for key, value in sorted(node.items())
        if key != "children"
    }


def child_ids(node: dict[str, Any]) -> list[str | None]:
    return [c.get("id_code") for c in node.get("children") or [] if isinstance(c, dict)]


# Loading a saved probe run -------------------------------------------------


def read_body(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))["response"]["body"]


def _listed_articles(run_dir: Path) -> dict[int, dict[str, Any]]:
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
    for article_id in article_ids:
        path = run_dir / comments_file(article_id)
        if path.exists():
            yield article_id, flatten_comments(read_body(path))


def _run_articles(run_dir: Path, article_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Article payloads for a run, from the listing pages or single fetches."""
    listed = _listed_articles(run_dir)
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
    """Comment trees and content authors for a saved run, for derived findings."""
    run = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    articles = _run_articles(run_dir, run["article_ids"])
    return dict(iter_run_comments(run_dir, run["article_ids"])), _run_authors(run_dir, articles)


def load_run(run_dir: Path) -> RunObservations:
    run = json.loads((run_dir / RUN_FILE).read_text(encoding="utf-8"))
    article_ids: list[int] = run["article_ids"]
    articles = _run_articles(run_dir, article_ids)
    authors = _run_authors(run_dir, articles)

    contents = []
    for article_id, article in articles.items():
        count = article.get("comments_count")
        contents.append(
            ObservedContent(
                content_ref=str(article_id),
                published_at=parse_timestamp(article.get("published_at")),
                reported_comment_count=count if isinstance(count, int) else None,
            )
        )

    comments = [
        ObservedComment(
            content_ref=str(article_id),
            source_object_id=str(n.id_code),
            parent_source_object_id=n.parent_id_code,
            depth=n.depth,
            created_at=parse_timestamp(n.node.get("created_at")),
            is_content_author=is_by(authors[article_id], n.node),
            is_deletion_placeholder=is_deletion_placeholder(n.node),
        )
        for article_id, nodes in iter_run_comments(run_dir, article_ids)
        for n in nodes
    ]
    return RunObservations(
        run_id=run["run_id"],
        scope=run["scope"],
        finished_at=parse_timestamp(run.get("finished_at")),
        contents=contents,
        comments=comments,
    )
