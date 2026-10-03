"""Read-only DEV capability probe (Stage 0).

Every request is a GET. Raw responses go to the git-ignored real-fixtures
directory. Findings, shapes, and the comment index go to the git-ignored
reports directory. Findings and shapes contain no comment text and no
commenter names; the comment index contains opaque IDs, timestamps, and
hashes only, and is a local intermediate for lifecycle comparison.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from afterword.adapters.dev import records
from afterword.adapters.dev.client import AuthMode, DevClient, Exchange, is_rate_limit_header
from afterword.adapters.dev.shapes import summarize

ADAPTER_VERSION: str = "dev-probe-0.2"
ARTICLES_ENDPOINT: str = "/api/articles/me/published"
COMMENTS_ENDPOINT: str = "/api/comments"
LARGE_PAGE_SIZE: int = 1000
MAX_PAGES: int = 200

FINDINGS_FILE: str = "probe-findings.json"
SHAPES_FILE: str = "shapes.json"
INDEX_FILE: str = "comment-index.json"

CONTENT_ITEM_FIELDS: tuple[str, ...] = (
    "id",
    "title",
    "url",
    "canonical_url",
    "published_at",
    "user",
)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _type_counts(values: list[Any]) -> dict[str, int]:
    return dict(Counter(type(v).__name__ for v in values))


# Endpoints whose payload is reduced to an allowlist before anything is saved.
# The account endpoint returns personal fields (including email) the experiment
# does not need; only the user ID is kept, to identify the content author.
_KEEP_ONLY: dict[str, tuple[str, ...]] = {"/api/users/me": ("id",)}
_CACHE_HEADERS: tuple[str, ...] = ("cache-control", "x-cache", "via", "warning")


def _redact(path: str, body: Any) -> list[str]:
    """Drop every field not on the endpoint's allowlist. Returns dropped key names."""
    keep = _KEEP_ONLY.get(path)
    if keep is None or not isinstance(body, dict):
        return []
    removed = sorted(k for k in body if k not in keep)
    for name in removed:
        del body[name]
    return removed


class ProbeLockedError(RuntimeError):
    """Raised when another probe holds the lock file."""

    pass


@contextmanager
def probe_lock(path: Path) -> Iterator[None]:
    """Hold an exclusive lock so two probes never run at once and double the request rate.

    :param path: Lock file path. It is created exclusively and removed on exit.
    :raises ProbeLockedError: If the lock file already exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise ProbeLockedError(str(path)) from None
    try:
        info = {"pid": os.getpid(), "started_at": datetime.now(UTC).isoformat(timespec="seconds")}
        os.write(fd, json.dumps(info).encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def _endpoint_template(path: str) -> str:
    if re.fullmatch(r"/api/articles/\d+", path):
        return "/api/articles/{id}"
    if re.fullmatch(r"/api/comments/[^/]+", path):
        return "/api/comments/{id_code}"
    if path.startswith("/api/articles/") and path != ARTICLES_ENDPOINT:
        return "/api/articles/{username}/{slug}"
    return path


class Probe:
    """Read-only capability probe over one DEV account."""

    def __init__(
        self,
        client: DevClient,
        raw_dir: Path,
        report_dir: Path,
        *,
        run_id: str,
        page_size: int = 10,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        progress: Callable[[str, int, int], None] | None = None,
    ) -> None:
        """Create a probe for one run.

        :param client: DEV client to send requests with.
        :param raw_dir: Git-ignored directory for raw responses.
        :param report_dir: Git-ignored directory for findings, shapes, and the comment index.
        :param run_id: Run identifier, normally a UTC timestamp.
        :param page_size: Small page size used to walk the article listing.
        :param now: Clock for run timestamps, injectable for tests.
        :param progress: Called with a step name (``account``, ``listing``,
            ``details``, ``comments``, ``thread checks``), the article number or
            page within the step, and the step's article total (0 when not counted).
            It receives counts only.
        """
        self.client = client
        self.raw_dir = raw_dir
        self.report_dir = report_dir
        self.run_id = run_id
        self.page_size = page_size
        self.now = now
        self._progress = progress
        self.limitations: list[str] = []
        self.requests_sent = 0
        self.responses_429 = 0
        self.backoff_s = 0.0
        self.header_names: set[str] = set()
        self.rate_values: dict[str, set[str]] = defaultdict(set)
        self.error_bodies: dict[int, list[Any]] = defaultdict(list)
        self.http_meta: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        self.retry_log: list[dict[str, Any]] = []
        self.redacted_fields: set[str] = set()
        self.pre_redaction_shapes: dict[str, Any] = {}
        self.findings: dict[str, Any] = {}

    # Requests ---------------------------------------------------------------

    def _step(self, name: str, current: int = 0, total: int = 0) -> None:
        if self._progress is not None:
            self._progress(name, current, total)

    def _get(
        self,
        filename: str,
        path: str,
        params: dict[str, Any] | None = None,
        auth: AuthMode = "key",
    ) -> Exchange:
        ex = self.client.get(path, params, auth=auth)
        if path in _KEEP_ONLY and ex.ok:
            # The shape (key names and types, no values) is evidence; the payload is not kept.
            self.pre_redaction_shapes[path] = summarize([ex.body])
        redacted = _redact(path, ex.body)
        if redacted:
            self.redacted_fields.update(redacted)
        record = ex.to_record()
        record["redacted_fields"] = redacted
        _write_json(self.raw_dir / filename, record)

        template = f"{_endpoint_template(path)} [auth={auth}]"
        self.requests_sent += 1 + len(ex.retries)
        self.responses_429 += sum(1 for r in ex.retries if r["status"] == 429)
        self.responses_429 += 1 if ex.status == 429 else 0
        self.backoff_s += sum(r["waited_s"] for r in ex.retries)
        self.header_names.update(ex.header_names)
        for name, value in ex.headers.items():
            if is_rate_limit_header(name) and len(self.rate_values[name]) < 10:
                self.rate_values[name].add(value)
        meta = self.http_meta[template]
        for name in _CACHE_HEADERS:
            if name in ex.headers and len(meta[name]) < 10:
                meta[name].add(ex.headers[name])
        for retry in ex.retries:
            self.retry_log.append(
                {k: retry[k] for k in ("status", "retry_after", "waited_s", "body")}
                | {"endpoint": template}
            )
            if isinstance(retry.get("body"), dict | list):
                self.error_bodies[retry["status"]].append(retry["body"])
        if ex.status >= 400 and ex.body_is_json:
            self.error_bodies[ex.status].append(ex.body)
        if ex.retries and ex.status in (429, 503):
            # A lookup by path carries the author's username; limitations are printed.
            shown = template if "{username}" in template else path
            self.limitations.append(
                f"{shown}: gave up after {len(ex.retries)} retries ({ex.status})"
            )
        return ex

    # Steps ------------------------------------------------------------------

    def _list_articles(self) -> list[dict[str, Any]]:
        walked: list[dict[str, Any]] = []
        per_page: list[int] = []
        terminated = False
        first_headers: dict[str, str] = {}
        for page in range(1, MAX_PAGES + 1):
            self._step("listing", page)
            ex = self._get(
                f"articles-page-{page:03d}.json",
                ARTICLES_ENDPOINT,
                {"page": page, "per_page": self.page_size},
            )
            first_headers = first_headers or ex.headers
            if not ex.ok or not isinstance(ex.body, list):
                self.limitations.append(f"article listing page {page} returned {ex.status}")
                break
            per_page.append(len(ex.body))
            if not ex.body:
                terminated = True
                break
            walked.extend(a for a in ex.body if isinstance(a, dict))

        large = self._get(
            records.ARTICLES_ALL_FILE, ARTICLES_ENDPOINT, {"page": 1, "per_page": LARGE_PAGE_SIZE}
        )
        large_items = large.body if large.ok and isinstance(large.body, list) else []
        small_ids = [a.get("id") for a in walked]
        large_ids = [a.get("id") for a in large_items if isinstance(a, dict)]

        self.findings["articles"] = {
            "endpoint": ARTICLES_ENDPOINT,
            "small_page_size": self.page_size,
            "items_per_page": per_page,
            "terminates_on_empty_page": terminated,
            "total_via_small_pages": len(set(small_ids)),
            "duplicates_across_pages": len(small_ids) - len(set(small_ids)),
            "large_page_size": LARGE_PAGE_SIZE,
            "large_page_status": large.status,
            "total_via_large_page": len(set(large_ids)),
            "id_sets_equal": set(small_ids) == set(large_ids),
            "pagination_headers": {
                k: v for k, v in first_headers.items() if k in ("link", "x-total-count")
            },
            "published_flag_values": dict(Counter(str(a.get("published")) for a in walked)),
            "id_types": _type_counts(small_ids),
        }
        source = walked or [a for a in large_items if isinstance(a, dict)]
        seen: set[Any] = set()
        unique = []
        for a in source:
            if isinstance(a.get("id"), int) and a["id"] not in seen:
                seen.add(a["id"])
                unique.append(a)
        return unique

    def _fetch_articles(self, article_ids: list[int]) -> list[dict[str, Any]]:
        # Every post is fetched singly: only the detail payload carries `edited_at`,
        # which labeling needs to know whether a post changed after a comment.
        bodies: list[dict[str, Any]] = []
        statuses: Counter[int] = Counter()
        for n, article_id in enumerate(article_ids, start=1):
            self._step("details", n, len(article_ids))
            ex = self._get(records.article_file(article_id), f"/api/articles/{article_id}")
            statuses[ex.status] += 1
            if ex.ok and isinstance(ex.body, dict):
                bodies.append(ex.body)
            else:
                self.limitations.append(f"article {article_id} detail returned {ex.status}")
        keys = set().union(*(set(b) for b in bodies)) if bodies else set()
        self.findings["article_fetch"] = {
            "endpoint": "/api/articles/{id}",
            "articles_requested": len(article_ids),
            "articles_fetched": len(bodies),
            "statuses": {str(k): v for k, v in sorted(statuses.items())},
            "content_item_fields_present": {
                f: bool(bodies) and all(f in b for b in bodies) for f in CONTENT_ITEM_FIELDS
            },
            "edit_key_candidates": records.edit_key_candidates(keys),
            "edited_at_present": sum(1 for b in bodies if b.get("edited_at")),
        }
        return bodies

    def _fetch_comments(
        self, articles: list[dict[str, Any]]
    ) -> dict[int, list[records.CommentNode]]:
        trees: dict[int, list[records.CommentNode]] = {}
        statuses: Counter[int] = Counter()
        for n, article in enumerate(articles, start=1):
            self._step("comments", n, len(articles))
            article_id = article["id"]
            ex = self._get(
                records.comments_file(article_id), COMMENTS_ENDPOINT, {"a_id": article_id}
            )
            statuses[ex.status] += 1
            if ex.ok and isinstance(ex.body, list):
                trees[article_id] = records.flatten_comments(ex.body)
            else:
                self.limitations.append(f"comments for article {article_id} returned {ex.status}")
        self.findings["comment_fetch_statuses"] = {str(k): v for k, v in statuses.items()}
        return trees

    def _comment_findings(
        self, articles: list[dict[str, Any]], trees: dict[int, list[records.CommentNode]]
    ) -> None:
        nodes = [n for ns in trees.values() for n in ns]
        node_keys: set[str] = set()
        user_keys: set[str] = set()
        for n in nodes:
            node_keys.update(n.node)
            if isinstance(n.node.get("user"), dict):
                user_keys.update(n.node["user"])
        id_codes = [n.node.get("id_code") for n in nodes]
        created = [n.node.get("created_at") for n in nodes]
        reported = {a["id"]: a.get("comments_count") for a in articles}
        unexpected = sum(1 for n in nodes if records.is_unexpected_shape(n.node))
        if unexpected:
            # ADR-009: never classify these silently; they need a friction entry.
            self.limitations.append(
                f"{unexpected} comment node(s) with an unexpected shape; "
                "record a friction entry before using this run"
            )
        # `comments_count` excludes deletion placeholders (observed 2026-10-02), so
        # reconcile against live comments and report placeholders alongside.
        live = {
            aid: sum(1 for n in ns if not records.is_deletion_placeholder(n.node))
            for aid, ns in trees.items()
        }
        mismatches = [
            {
                "article_id": aid,
                "counted": live[aid],
                "placeholders": len(trees[aid]) - live[aid],
                "reported": reported.get(aid),
            }
            for aid in sorted(trees)
            if reported.get(aid) != live[aid]
        ]
        self.findings["comments"] = {
            "endpoint": f"{COMMENTS_ENDPOINT}?a_id={{article_id}}",
            "articles_fetched": len(trees),
            "total_nodes": len(nodes),
            "max_depth": max((n.depth for n in nodes), default=None),
            "node_keys": sorted(node_keys),
            "user_keys": sorted(user_keys),
            "id_code": {
                "present": sum(1 for v in id_codes if isinstance(v, str) and v),
                "types": _type_counts(id_codes),
                "unique": len({v for v in id_codes if v}),
            },
            "created_at": {
                "present": sum(1 for v in created if v),
                "parse_with_timezone": sum(1 for v in created if records.parse_timestamp(v)),
                "ends_with_z": sum(1 for v in created if isinstance(v, str) and v.endswith("Z")),
            },
            "edit_key_candidates": records.edit_key_candidates(node_keys),
            "parent_key_candidates": records.parent_key_candidates(node_keys),
            "count_reconciliation": {
                "articles_matching": len(trees) - len(mismatches),
                "mismatches": mismatches,
            },
            "deletion_observation": {
                "placeholder_like_bodies": sum(
                    1 for n in nodes if records.placeholder_like(n.node)
                ),
                "null_or_missing_user": sum(
                    1 for n in nodes if not isinstance(n.node.get("user"), dict)
                ),
                "deletion_placeholders": sum(
                    1 for n in nodes if records.is_deletion_placeholder(n.node)
                ),
                "unexpected_shapes": unexpected,
                "missing_id_code": sum(1 for v in id_codes if not v),
            },
        }

    def _probe_largest_thread(self, trees: dict[int, list[records.CommentNode]]) -> Any:
        """Unauthenticated access, pagination params, and single-comment fetch."""
        if not trees or not any(trees.values()):
            self.limitations.append("no comments found; thread-level checks skipped")
            return None
        self._step("thread checks")
        largest = max(trees, key=lambda aid: len(trees[aid]))
        full_ids = {n.id_code for n in trees[largest]}
        self.findings["largest_thread"] = {"article_id": largest, "nodes": len(full_ids)}

        unauth = self._get(
            records.comments_file(largest, "-unauthenticated"),
            COMMENTS_ENDPOINT,
            {"a_id": largest},
            auth="none",
        )
        unauth_ids = (
            {n.id_code for n in records.flatten_comments(unauth.body)} if unauth.ok else set()
        )
        self.findings["auth"]["unauthenticated_comments_status"] = unauth.status
        self.findings["auth"]["unauthenticated_matches_authenticated"] = unauth_ids == full_ids

        params = {"a_id": largest, "page": 2, "per_page": 1}
        paged = self._get(records.comments_file(largest, "-paged"), COMMENTS_ENDPOINT, params)
        paged_ids = {n.id_code for n in records.flatten_comments(paged.body)} if paged.ok else set()
        self.findings["comment_pagination"] = {
            "article_id": largest,
            "params_sent": params,
            "status": paged.status,
            "nodes_without_params": len(full_ids),
            "nodes_with_params": len(paged_ids),
            "params_ignored": paged.ok and paged_ids == full_ids,
            "pagination_headers": {
                k: v for k, v in paged.headers.items() if k in ("link", "x-total-count")
            },
        }

        roots = [n for n in trees[largest] if n.depth == 0]
        target = next((n for n in roots if n.node.get("children")), roots[0] if roots else None)
        if target is None or not target.id_code:
            return None
        single = self._get(f"comment-{target.id_code}.json", f"/api/comments/{target.id_code}")
        subtree = self._subtree_ids(trees[largest], target.id_code)
        single_nodes = records.flatten_comments(single.body) if single.ok else []
        self.findings["single_comment_fetch"] = {
            "endpoint": "/api/comments/{id_code}",
            "status": single.status,
            "body_type": type(single.body).__name__,
            "target_had_children": bool(target.node.get("children")),
            "nodes_in_response": len(single_nodes),
            "nodes_in_tree_subtree": len(subtree),
            "matches_tree_subtree": {n.id_code for n in single_nodes} == subtree,
        }
        return single.body if single.ok else None

    @staticmethod
    def _subtree_ids(nodes: list[records.CommentNode], root: str) -> set[str]:
        ids = {root}
        for n in nodes:  # depth-first order: parents precede children
            # A node without an ID cannot be anyone's parent. Adding None would make
            # every later top-level node (parent None) look like part of the subtree.
            if n.parent_id_code is not None and n.parent_id_code in ids and n.id_code:
                ids.add(n.id_code)
        return ids

    # Run ----------------------------------------------------------------------

    def _resolve_article(self, article: int | str) -> int | None:
        """Accept a numeric ID, or a DEV article URL or `username/slug` path."""
        if isinstance(article, int) or article.isdigit():
            return int(article)
        parts = urlparse(article).path.strip("/").split("/")
        if len(parts) != 2:
            self.limitations.append("--article is neither an ID nor a username/slug path")
            return None
        ex = self._get("article-by-path.json", f"/api/articles/{parts[0]}/{parts[1]}")
        if ex.ok and isinstance(ex.body, dict) and isinstance(ex.body.get("id"), int):
            resolved: int = ex.body["id"]
            return resolved
        self.limitations.append(f"article path lookup returned {ex.status}")
        return None

    def run(
        self, *, article: int | str | None = None, compare_to: Path | None = None
    ) -> dict[str, Any]:
        """Run the probe and write its outputs.

        :param article: Limit the run to one article, by numeric ID or URL. ``None``
            probes everything.
        :param compare_to: Report directory of an earlier run to diff against.
        :returns: The findings, as also written to ``probe-findings.json``.
        """
        started = self.now()
        self.findings.update(
            run_id=self.run_id,
            adapter_version=ADAPTER_VERSION,
            # A URL holds the author's username; the scope is printed, so it waits
            # for the resolved numeric ID.
            scope="all" if article is None else "article:unresolved",
            started_at=started.isoformat(timespec="seconds"),
        )

        self._step("account")
        me_ex = self._get(records.ME_FILE, "/api/users/me")
        self.findings["auth"] = {"me_endpoint": "/api/users/me", "me_status": me_ex.status}
        if not me_ex.ok or not isinstance(me_ex.body, dict):
            self.limitations.append(f"/api/users/me returned {me_ex.status}")
            return self._finish("FAILED", [], {}, None, compare_to)
        me = records.identity_from_me(me_ex.body)
        self.findings["auth"]["me_has_id"] = me.user_id is not None

        article_id = None
        if article is not None:
            article_id = self._resolve_article(article)
            if article_id is None:
                return self._finish("FAILED", [], {}, None, compare_to)
            self.findings["scope"] = f"article:{article_id}"

        if article_id is None:
            invalid = self._get("auth-invalid-key.json", "/api/users/me", auth="invalid")
            self.findings["auth"]["invalid_key_status"] = invalid.status
            articles = self._list_articles()
            details = self._fetch_articles([a["id"] for a in articles])
        else:
            details = self._fetch_articles([article_id])
            articles = details

        trees = self._fetch_comments(articles)
        self._comment_findings(articles, trees)
        authors = {a["id"]: records.content_author(a, me) for a in articles}
        self.findings["comments"]["by_content_author"] = sum(
            1 for aid, ns in trees.items() for n in ns if records.is_by(authors[aid], n.node)
        )
        self.findings["comments"]["ai_disclosure"] = records.ai_disclosure_distribution(
            trees, authors
        )

        single_body = None
        if article_id is None and trees:
            single_body = self._probe_largest_thread(trees)

        outcome = "COMPLETE" if not self.limitations else "PARTIAL"
        self._write_shapes(me_ex.body, articles, details, trees, single_body)
        index = self._comment_index(articles, trees, authors)
        return self._finish(outcome, articles, index, me_ex.body, compare_to)

    # Outputs ------------------------------------------------------------------

    def _write_shapes(
        self,
        me_body: Any,
        articles: list[dict[str, Any]],
        details: list[dict[str, Any]],
        trees: dict[int, list[records.CommentNode]],
        single_body: Any,
    ) -> None:
        children = frozenset({"children"})
        shapes: dict[str, Any] = {
            "users_me": self.pre_redaction_shapes.get("/api/users/me", summarize([me_body])),
            "article_list_item": summarize(articles),
            "comment_node": summarize(
                [n.node for ns in trees.values() for n in ns], opaque_keys=children
            ),
        }
        if details:
            shapes["article"] = summarize(details)
        if single_body is not None:
            shapes["comment_single"] = summarize([single_body], opaque_keys=children)
        for status, bodies in sorted(self.error_bodies.items()):
            shapes[f"error_{status}"] = summarize(bodies)
        _write_json(self.report_dir / SHAPES_FILE, shapes)

    def _comment_index(
        self,
        articles: list[dict[str, Any]],
        trees: dict[int, list[records.CommentNode]],
        authors: dict[int, records.AuthorIdentity],
    ) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "article_ids": sorted(trees),
            "reported_comment_counts": {
                str(a["id"]): a.get("comments_count") for a in articles if a["id"] in trees
            },
            "comments": [
                {
                    "id_code": n.id_code,
                    "article_id": aid,
                    "parent_id_code": n.parent_id_code,
                    "depth": n.depth,
                    "created_at": n.node.get("created_at"),
                    "keys": sorted(n.node),
                    "field_hashes": records.field_hashes(n.node),
                    "child_ids": records.child_ids(n.node),
                    "is_content_author": records.is_by(authors[aid], n.node),
                    "user_present": isinstance(n.node.get("user"), dict),
                    "placeholder_like": records.placeholder_like(n.node),
                    "is_deletion_placeholder": records.is_deletion_placeholder(n.node),
                }
                for aid, ns in sorted(trees.items())
                for n in ns
            ],
        }

    def _finish(
        self,
        outcome: str,
        articles: list[dict[str, Any]],
        index: dict[str, Any],
        me_body: Any,
        compare_to: Path | None,
    ) -> dict[str, Any]:
        finished = self.now()
        if index and compare_to is not None:
            previous = json.loads((compare_to / INDEX_FILE).read_text(encoding="utf-8"))
            self.findings["lifecycle"] = compare_indexes(previous, index)
        self.findings["rate_limits"] = {
            "requests_sent": self.requests_sent,
            "responses_429": self.responses_429,
            "total_backoff_s": round(self.backoff_s, 3),
            "rate_limit_headers_seen": {k: sorted(v) for k, v in sorted(self.rate_values.items())},
            "retries": self.retry_log,
            "all_header_names_seen": sorted(self.header_names),
        }
        self.findings["http_cache_by_endpoint"] = {
            endpoint: {name: sorted(values) for name, values in sorted(meta.items())}
            for endpoint, meta in sorted(self.http_meta.items())
        }
        self.findings["redacted_before_save"] = sorted(self.redacted_fields)
        self.findings.update(
            outcome=outcome,
            limitations=self.limitations,
            finished_at=finished.isoformat(timespec="seconds"),
        )
        if index:
            _write_json(self.report_dir / INDEX_FILE, index)
        _write_json(
            self.raw_dir / records.RUN_FILE,
            {
                "run_id": self.run_id,
                "scope": self.findings["scope"],
                "adapter_version": ADAPTER_VERSION,
                "outcome": outcome,
                "article_ids": [a["id"] for a in articles],
                "started_at": self.findings["started_at"],
                "finished_at": self.findings["finished_at"],
            },
        )
        _write_json(self.report_dir / FINDINGS_FILE, self.findings)
        return self.findings


def compare_indexes(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Describe lifecycle changes between two runs by ID, key name, and hash only.

    :param previous: Comment index of the earlier run.
    :param current: Comment index of the later run.
    :returns: Added, removed, and changed comments, plus reported counts per article.
    """
    shared = set(previous["article_ids"]) & set(current["article_ids"])
    before = {c["id_code"]: c for c in previous["comments"] if c["article_id"] in shared}
    after = {c["id_code"]: c for c in current["comments"] if c["article_id"] in shared}
    changed = []
    for id_code in sorted(before.keys() & after.keys()):
        a, b = before[id_code], after[id_code]
        ha, hb = a["field_hashes"], b["field_hashes"]
        entry = {
            "id_code": id_code,
            "keys_added": sorted(set(hb) - set(ha)),
            "keys_removed": sorted(set(ha) - set(hb)),
            "values_changed": sorted(k for k in set(ha) & set(hb) if ha[k] != hb[k]),
            "children_before": len(a["child_ids"]),
            "children_after": len(b["child_ids"]),
            "placeholder_like": [a["placeholder_like"], b["placeholder_like"]],
            "user_present": [a["user_present"], b["user_present"]],
        }
        if (
            entry["keys_added"]
            or entry["keys_removed"]
            or entry["values_changed"]
            or a["child_ids"] != b["child_ids"]
        ):
            changed.append(entry)
    return {
        "compared_to": previous["run_id"],
        "articles_compared": sorted(shared),
        "reported_comment_counts": {
            str(aid): [
                previous["reported_comment_counts"].get(str(aid)),
                current["reported_comment_counts"].get(str(aid)),
            ]
            for aid in sorted(shared)
        },
        "added": [
            {"id_code": i, "parent_id_code": after[i]["parent_id_code"]}
            for i in sorted(after.keys() - before.keys())
        ],
        "removed": [
            {"id_code": i, "had_children": len(before[i]["child_ids"])}
            for i in sorted(before.keys() - after.keys())
        ],
        "changed": changed,
        "unchanged": len(before.keys() & after.keys()) - len(changed),
    }
