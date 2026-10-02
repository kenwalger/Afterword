# API Capability Matrix

**Version:** 2 (2026-10-02)

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

General notes from documentation: authenticated requests use an `api-key` header and the `application/vnd.forem.api-v1+json` accept header. Some endpoints are public without authentication.

| Capability | Status | Notes |
| --- | --- | --- |
| Authenticate personal user | DOCUMENTED | `api-key` header; key generated in DEV settings. |
| List own published posts | NOT_TESTED | Expected under the authenticated "my articles" endpoints; confirm path and pagination. |
| Fetch post | NOT_TESTED | Confirm fields needed for `ContentItem`. |
| Fetch comments for a post | DOCUMENTED | `GET /api/comments?a_id={article_id}`. Documented as public, returning top-level comments with nested `children` threads. |
| Fetch a comment with descendants | DOCUMENTED | `GET /api/comments/{id}`. Useful for targeted refresh. |
| Comment body format | DOCUMENTED | `body_html`. No Markdown body observed in docs. Normalization must handle HTML. |
| Comment identifier | DOCUMENTED | `id_code` (string). |
| Comment created timestamp | DOCUMENTED | `created_at`, RFC 3339. |
| Comment edited timestamp | UNKNOWN | Determines whether edits are detectable directly or only by payload hash. |
| Deleted comment representation | UNKNOWN | Absent, placeholder, or flagged? Drives lifecycle rules. |
| Thread parent/child relationships | DOCUMENTED | Implied by nesting in `children`. Explicit parent ID field: UNKNOWN. |
| Comment author fields | DOCUMENTED | Embedded `user` object. Confirm which fields are present. |
| Pagination of comments | UNKNOWN | Docs describe returning all comments; behavior on large threads must be checked. |
| Rate limits | UNKNOWN | Inspect response headers and 429 behavior. |
| Webhooks for new comments | UNKNOWN | Not required for V1. |
| Reactions: read | UNKNOWN | Not used for priority in V1. |
| Comment write | UNKNOWN | Out of V1 scope. |

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

## Rule

The canonical model represents capability differences rather than forcing every platform into the richest platform's shape.

---

## Appendix: CoderLegion (deferred, Stage 6 only)

Recorded from a user-provided excerpt of authenticated documentation. Not re-examined in v2.

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
