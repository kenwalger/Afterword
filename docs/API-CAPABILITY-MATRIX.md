# API Capability Matrix

**Version:** 4 (2026-10-07)

v4 records that DEV added the AI-disclosure fields to every comment node between runs `20261003T141450Z` and `20261007T224849Z`, deletion placeholders included.

This document records what each platform actually exposes. `UNKNOWN` is a valid state and must not be converted into supported or unsupported without evidence.

## Status values

- `SUPPORTED`: verified by a recorded request
- `DOCUMENTED`: stated in official or reference documentation, not yet verified by request
- `PARTIAL`: verified, with limitations recorded
- `UNSUPPORTED`: verified absent or refused
- `UNKNOWN`: no evidence either way
- `NOT_TESTED`: expected to exist, not yet checked

`DOCUMENTED` becomes `SUPPORTED`, `PARTIAL`, or `UNSUPPORTED` only through the test procedure below.

## DEV (Forem API v1): V1 source

General notes: authenticated requests use an `api-key` header and the `application/vnd.forem.api-v1+json` accept header. Some endpoints are public without authentication. Responses pass through a Varnish CDN.

Verified on 2026-10-02 by `afterword probe` (adapter `dev-probe-0.1`). Full runs `20261002T170711Z` and `20261002T171152Z` covered all 138 published articles and returned identical results. Hand-test runs `20261002T173106Z` through `20261002T174612Z` used one article. Evidence details are in the log below.

| Capability | Status | Notes |
| --- | --- | --- |
| Authenticate personal user | SUPPORTED | `api-key` header. `GET /api/users/me` returns 200 with the key and 401 with an invalid key. |
| Account endpoint contents | SUPPORTED | `/api/users/me` returns personal fields, including `email`, `followers_count`, and `badge_ids`. Only `id` is kept; everything else is dropped before saving. |
| List own published posts | SUPPORTED | `GET /api/articles/me/published?page=&per_page=`. Pagination stops on an empty page. `per_page=10` paging and a single `per_page=1000` page returned the same 138 IDs, with no duplicates. No `Link` or total-count header. `published` is true on all items. |
| Fetch post | SUPPORTED | `GET /api/articles/{id}`. Every field needed for `ContentItem` is present (`id`, `title`, `url`, `canonical_url`, `published_at`, `user`). Also has `edited_at`, `last_comment_at`, `language`, `subforem_id`, and `ai_disclosure_*`. List items lack `edited_at`, so full runs from `dev-probe-0.2` fetch every post singly (one extra request per post). |
| Fetch post by path | SUPPORTED | `GET /api/articles/{username}/{slug}` resolves an article URL to its numeric ID. |
| Fetch comments for a post | SUPPORTED | `GET /api/comments?a_id={article_id}`. Public: an unauthenticated request returned the same comment IDs as an authenticated one. Top-level comments, with replies nested in `children`. |
| Fetch a comment with descendants | SUPPORTED | `GET /api/comments/{id_code}` returns one object whose subtree matched the tree from `a_id` (14 of 14 nodes). |
| Comment body format | SUPPORTED | `body_html` only, HTML on all 707 comments. No Markdown body. |
| Comment identifier | SUPPORTED | `id_code`, string, length 3 to 5, unique across 707 comments. 33 consist only of digits and must never be treated as numbers. Retained when a comment with replies is deleted. |
| Comment created timestamp | SUPPORTED | `created_at`, RFC 3339 with `Z`, on 707 of 707. Unchanged by edits and by deletion. |
| Comment edited timestamp | UNSUPPORTED | No edit-related field on any comment. Editing a comment changed only `body_html`, with no key added. Edits are detectable only by payload hash. Articles do have `edited_at`. |
| Deleted comment representation | PARTIAL | A deleted comment with no replies disappears from the tree. A deleted comment with replies stays as a placeholder: same `id_code`, `created_at`, `type_of`, and `children`, with `body_html` replaced and `user` an empty object `{}`. The placeholder persisted after its last reply was deleted. `comments_count` excludes placeholders. From run `20261007T224849Z` DEV adds `ai_disclosure_label` and `ai_disclosure_level` to every comment node, the placeholder included; they are allowlisted as platform-wide keys (ADR-009, amended 2026-10-07). One sample of each case, author self-deletion only; deletion by others, moderator removal, and account deletion were not tested. Handled per ADR-009 (accepted, provisional); evidence in `docs/proposals/accepted/2026-10-02-deletion-placeholders.md`. |
| Thread parent/child relationships | PARTIAL | Only by nesting in `children`; there is no explicit parent ID field. Nesting reached depth 34. A reply keeps its position under a deleted parent's placeholder. |
| Comment author fields | SUPPORTED | Embedded `user`: `name`, `username`, `user_id` (int, always present), `twitter_username`, `github_username`, `website_url`, `profile_image`, `profile_image_90`. Empty object on deletion placeholders. |
| Comment AI disclosure fields | PARTIAL | Undocumented `ai_disclosure_label` and `ai_disclosure_level` on 179 of 707 comments. The only observed values are `Not Disclosed` / `not_disclosed`, always paired. When they appear is not explained by date. Recorded only; not a V1 priority input. |
| Comment count on post | PARTIAL | `comments_count` on articles excludes deletion placeholders. On 3 of 138 articles it is one higher than the comments returned, for reasons still unknown. |
| Pagination of comments | PARTIAL | With no parameters, every comment is returned. The largest thread (116) matched `comments_count`. If `page`/`per_page` are sent, they page top-level threads (`page=2&per_page=1` returned one thread of 4 comments). No pagination headers. Whether there is a default cap above 116 top-level threads is unknown. Never send these parameters. |
| Rate limits | PARTIAL | No rate-limit headers on any response. At about 1 request per second, two full runs (about 160 requests each) received 5 and 1 responses with status 429, and backoff recovered every time. Retry-After values and 429 bodies were not yet captured (the probe now records them). Limits can be discovered only by hitting them. |
| Response caching | PARTIAL | `cache-control: public, no-cache` on article and comment endpoints, `max-age=0, private, must-revalidate` on `/api/users/me`. `x-cache` showed `MISS, HIT` once, still with current data. Edits and deletions were visible on the first probe run after they were made (runs about 1.5 to 11 minutes apart); no stale response was observed. |
| Webhooks for new comments | UNKNOWN | Not tested: not needed for V1. |
| Reactions: read | UNKNOWN | Not tested: not used for priority in V1. |
| Comment write | UNKNOWN | Not tested: write calls are excluded from V1. |

## Test procedure

For each capability tested, record:

- endpoint
- authentication used
- request date
- relevant parameters
- pagination behavior
- rate-limit evidence
- response fields needed by the application
- whether semantics are documented or inferred
- fixture captured, with secrets removed
- friction log entry if anything was surprising

## Evidence log: DEV, 2026-10-02

Raw responses are in the git-ignored `fixtures/dev-api/source/real/<run>/`. Value-free findings and shapes are in the git-ignored `reports/probe/<run>/`. Committed fixtures are synthetic and listed in `fixtures/dev-api/source/MANIFEST.md`.

| Capability | Endpoint and parameters | Auth | Pagination | Rate-limit evidence | Fields needed | Semantics | Fixture | Friction entry |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Authenticate | `GET /api/users/me` | key; invalid key | n/a | none | `id` | documented | `users-me.json`, `error-401.json` | Account endpoint returns email |
| Account contents | `GET /api/users/me` | key | n/a | none | `id` only | observed | `users-me.json` | Account endpoint returns email |
| List own posts | `GET /api/articles/me/published`, `page`, `per_page` 10 and 1000 | key | page-based, empty page ends | 429s in full runs | `id`, `published_at`, `comments_count`, `user.user_id`, `url` | documented | `articles-me-published.json` | none |
| Fetch post | `GET /api/articles/{id}` | key | n/a | none | `ContentItem` fields | documented | `article.json` | none |
| Fetch post by path | `GET /api/articles/{username}/{slug}` | key | n/a | none | `id` | documented | none (reuses list item) | none |
| Comments for post | `GET /api/comments?a_id=` | key; none | none by default | 429s in full runs | `id_code`, `created_at`, `body_html`, `user`, `children` | documented | `comments-by-article.json` | Comment pagination |
| Comment with descendants | `GET /api/comments/{id_code}` | key | n/a | none | as above | documented | `comment-with-descendants.json` | none |
| Edit timestamp | hand test, `a_id` | key | n/a | none | n/a | observed | none (no new shape) | Edit changes only `body_html` |
| Deletion | hand test, `a_id` | key | n/a | none | `user` emptiness | observed, n=1 per case | `comments-with-deletion-placeholder.json` | Deletion placeholders |
| Parent/child | `a_id` nesting | key | n/a | none | `children` | inferred from nesting | `comments-by-article.json` | No parent ID, depth 34 |
| AI disclosure | `a_id` | key | n/a | none | none (recorded only) | undocumented | values replaced with `synthetic_val` | AI disclosure fields |
| Comment count | list and fetch post | key | n/a | none | `comments_count` | observed | `article.json` | Count mismatches |
| Comment pagination | `a_id` with `page=2&per_page=1` | key | top-level threads | none | n/a | observed, undocumented | none (same shape) | Comment pagination |
| Rate limits | all | all | n/a | 429 without headers | n/a | observed | `error-429.json` (provisional) | Rate limits and CDN |
| Caching | all | all | n/a | n/a | n/a | observed | none | Rate limits and CDN |

## Rule

The canonical model represents capability differences rather than forcing every platform into the richest platform's shape.

---

## Appendix: CoderLegion (deferred, Stage 6 only)

Recorded from a user-provided excerpt of authenticated documentation. Not re-examined in v2 or v3.

| Capability | Status | Notes |
| --- | --- | --- |
| Authenticate personal user | DOCUMENTED | Personal API keys. |
| List own posts | DOCUMENTED | `GET /posts` |
| Search posts | DOCUMENTED | `GET /posts/search` |
| Fetch post | DOCUMENTED | `GET /posts/{id}` |
| Create/edit post | DOCUMENTED | Create/edit endpoints. |
| Fetch comments for a post | UNKNOWN | No explicit read-comments endpoint in the provided list; may be embedded in post payload. |
| Create comment | DOCUMENTED | `POST /posts/{id}/comments` |
| Create reply | DOCUMENTED | `POST /comments/{id}/replies` |
| Edit comment/reply | DOCUMENTED | PUT endpoints. |
| Hide/reshow comment/reply | DOCUMENTED | Documented endpoints. |
| Notifications | DOCUMENTED | `GET /notifications` |
| Reactions: read/write | UNKNOWN | Not in provided list. |
| Followers, following, profile lookup | UNKNOWN | Not established. |
| Creator analytics | UNKNOWN | Not in provided list. |
| Thread relationships, pagination, rate limits, webhooks | UNKNOWN | Must inspect. |

v1 of this matrix marked these as `SUPPORTED`. They are reclassified as `DOCUMENTED` because no request has verified them.
