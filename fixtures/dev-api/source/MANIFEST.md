# DEV source fixtures

Committed fixtures in this directory are **synthetic**. Every name, ID, URL, timestamp, and body is invented. Source field names are preserved so adapter tests exercise the real shape.

Real payloads captured by `afterword probe` live in `real/`, which is git-ignored and never committed.

| File | Provenance | Shape | Endpoint |
| --- | --- | --- | --- |
| `users-me.json` | synthetic | object | `GET /api/users/me` |
| `articles-me-published.json` | synthetic | array of article list items | `GET /api/articles/me/published` |
| `article.json` | synthetic | object | `GET /api/articles/{id}` |
| `comments-by-article.json` | synthetic | array of comment trees (nested `children`) | `GET /api/comments?a_id={id}` |
| `comment-with-descendants.json` | synthetic | single comment tree | `GET /api/comments/{id_code}` |
| `comments-with-deletion-placeholder.json` | synthetic | comment tree whose root is a deletion placeholder | `GET /api/comments?a_id={id}` |
| `error-401.json` | synthetic | error object | any authenticated endpoint, bad key |
| `error-429.json` | synthetic | error object | any endpoint, rate limited |

## Status

**Reconciled (2026-10-02)** against the key paths and types in `shapes.json` from probe run `20261002T170711Z`, and the hand-test runs `20261002T173106Z` to `20261002T174612Z`. Values were never copied.

- `users-me.json` includes a synthetic `email` so tests can prove the probe drops it. The probe keeps only `id` from this endpoint.
- `ai_disclosure_label` and `ai_disclosure_level` use the placeholder value `synthetic_val`. Real values are recorded as enum counts in the session friction log.
- One comment in the tests uses a digit-only `id_code` (`4821`) because 33 real IDs are all digits.
- In the deletion placeholder, `user: {}` and the retained `id_code`, `created_at`, and `children` match the observed structure. The body `<p>[deleted]</p>` is a guess that only matches the observed length (16 characters). The real placeholder text was not read, and nothing depends on it.
- `error-429.json` is still **provisional**. No 429 body has been captured yet; the probe now records one when it happens.
- Optional fields seen in real article list items (`flare_tag`, `organization`) are not represented.
