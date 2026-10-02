# Proposal: Deletion placeholders (amends ADR-009 and DATA-MODEL lifecycle)

**Status:** ACCEPTED WITH REVISIONS (2026-10-02). Applied to `docs/adr/ADR-009-honor-upstream-deletion.md` (now "Accepted, provisional") and `docs/DATA-MODEL.md` v3. This file is kept as the record of the evidence and the original proposal. Where it differs from the applied text, the ADR and DATA-MODEL win.

Revisions made on acceptance:

1. The status is "Accepted, provisional": it rests on one self-deleted sample per case, and deletion by another user or a moderator is untested.
2. Only the exact observed placeholder shape counts as a placeholder. Any other authorless or unexpected node shape is flagged, recorded as a sync limitation, and gets a friction entry. It is never silently classified.
3. Authorship of a comment first observed as a placeholder is `UNKNOWN`, never inferred. (This proposal originally said `NOT_EXPOSED`.)
4. Placeholders are excluded from triage and all metrics, and remain only as thread structure.

**Date:** 2026-10-02

## Evidence

Hand test on one of the author's own articles (article `62166`), five scoped probe runs, all on 2026-10-02. Three throwaway comments by the author: A (top level, no replies), B (top level), C (reply to B). Field names and presence only; no values were read.

| Run | Action before run | Nodes | `comments_count` | Observation |
| --- | --- | --- | --- | --- |
| `20261002T173106Z` | A, B, C posted | 3 | 3 | Baseline. |
| `20261002T173308Z` | A edited | 3 | 3 | Only A's `body_html` changed. No key added or removed. `created_at` unchanged. |
| `20261002T173436Z` | A and B deleted | 2 | 1 | A absent from the tree. B present with the same `id_code`, `created_at`, `type_of`, and `children` (still holding C); `body_html` replaced by a 16-character placeholder; `user` is an empty object `{}`. |
| `20261002T174523Z` | 10 minutes later | 2 | 1 | Identical to the previous run. Second consecutive observation. |
| `20261002T174612Z` | C deleted | 1 | 0 | C absent. B's placeholder remains, now with `children: []`. |

Findings:

1. **A deleted comment without replies disappears.** This matches ADR-009's absence rule.
2. **A deleted comment with replies stays in the tree as a placeholder.** It keeps its `id_code`, `created_at`, and thread position. Its body is replaced and its `user` becomes `{}`.
3. **The placeholder persisted after its last reply was deleted** (observed for about one minute).
4. **`comments_count` excludes placeholders.** Raw node counts overstate live comments by the number of placeholders.
5. The placeholder carries no author identity, so authorship (and ADR-011's `is_content_author`) cannot be read from it.

Limits: one sample of each case, all deleted by the comment's own author, who is also the article author. Deletion by another commenter, moderator removal, and account deletion were not tested and may look different.

Clean full run `20261002T171152Z` contains no node with an empty `user` object, so the volume baseline is unaffected.

## Proposed ADR-009 amendment

Replace the Decision paragraph with:

> A comment becomes `DELETED_UPSTREAM` when either:
>
> 1. **Absence:** it is absent from two consecutive complete syncs of its post, or
> 2. **Source placeholder:** the source returns it as a deletion placeholder. For DEV, that is a known `id_code` whose `user` is an empty object. One observation is enough, because the source has stated the deletion explicitly.
>
> Its body text and raw payloads are purged from local storage and corpus files at the next sync. Identifiers, thread position, lifecycle history, and non-content judgments may remain. A placeholder is kept as a structural node so that replies under it retain their parent. The placeholder's own payload contains no commenter content and may be stored.

Add to Consequences:

> - Deletion has two representations on DEV. Detection must handle both.
> - A placeholder is not a comment from anyone. It is excluded from counts, classification, priority, and evaluation, like author comments (ADR-011), but for a different reason.
> - Authorship of a deleted comment is known only from earlier observations. `is_content_author` and the `REPLY_TO_AUTHOR` flag on its replies are taken from the last pre-deletion observation, which is non-content and survives the purge.
> - A placeholder first seen without any earlier observation has unknown authorship (`NOT_EXPOSED`).
> - The representation was verified for author self-deletion only. Other deletion paths are `UNKNOWN` until observed.

## Proposed DATA-MODEL changes

### Comment

- Add `deletion_evidence` (value state): `ABSENT_TWICE`, `SOURCE_PLACEHOLDER`, or `NOT_YET_INTERPRETED` while not deleted.
- `author_platform_identity_id`: for a placeholder, retain the last observed value. If none was ever observed, `NOT_EXPOSED`.
- `is_content_author`: retained from the last pre-deletion observation.

### Lifecycle rules

Replace the "Deleted upstream" rule with:

> - **Deleted upstream (absence):** absent from two consecutive complete syncs. `deletion_evidence = ABSENT_TWICE`.
> - **Deleted upstream (placeholder):** the source returns a known comment as a deletion placeholder (DEV: `user` is `{}`). State becomes `DELETED_UPSTREAM` at once, with `deletion_evidence = SOURCE_PLACEHOLDER`. The node stays in the thread so replies keep their parent. The purge rule in `PRIVACY-AND-BOUNDARIES.md` applies.
> - **Placeholder without prior observation:** create the Comment directly in `DELETED_UPSTREAM` with no body stored and authorship `NOT_EXPOSED`.

Add to "Missing":

> When reconciling against a source-reported count, compare live comments only. DEV's `comments_count` excludes placeholders.

### SourceRecord

No change. A placeholder payload is a new SourceRecord because its hash differs. That record contains no commenter content, so it is exempt from the purge. Earlier records for the same comment are purged.

## Not explained by this proposal

The three articles in the full run whose `comments_count` is **one higher** than the returned nodes go the other way: placeholders make the count lower than the node total, not higher. Those three remain unexplained. Candidates include hidden or moderated comments, or comments by suspended accounts. They stay `UNKNOWN`.

## Decision requested

Accept, revise, or reject. If accepted, the ADR and DATA-MODEL edits above are applied verbatim, and the session that applies them records it in `docs/FRICTION-LOG.md`.
