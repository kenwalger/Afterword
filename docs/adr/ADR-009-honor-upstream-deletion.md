# ADR-009: Upstream Deletion Propagates to Local Data

**Status:** Accepted, provisional (amended 2026-10-02)

The amendment is based on one self-deleted sample per case (a comment without replies and a comment with a reply, both deleted by their author, who is also the post author). Deletion by another user, moderator removal, and account deletion are untested. Any of them may look different, and this ADR is revisited when one is observed.

## Context

A commenter who deletes a comment on DEV has withdrawn it. Keeping its text locally, in a corpus, or in a published dataset would preserve something the author chose to remove.

The original decision assumed deletion appears as absence. A hand test on 2026-10-02 showed DEV has two representations (see `docs/proposals/accepted/2026-10-02-deletion-placeholders.md` and `docs/API-CAPABILITY-MATRIX.md`):

- A deleted comment **without replies** disappears from the thread.
- A deleted comment **with replies** remains as a **placeholder**. It keeps its `id_code`, `created_at`, `type_of`, and `children`; its body is replaced; and its `user` is an empty object. The placeholder persisted after its last reply was deleted. DEV's `comments_count` excludes placeholders.

## Decision

A comment becomes `DELETED_UPSTREAM` when either:

1. **Absence:** it is absent from two consecutive complete syncs of its post, or
2. **Source placeholder:** the source returns it in the exact known placeholder shape. For DEV, that is the observed key set with `user` equal to an empty object. One observation is enough, because the source has stated the deletion explicitly.

Its body text and raw payloads are purged from local storage and corpus files at the next sync. Identifiers, thread position, lifecycle history, and non-content judgments may remain.

**Placeholders are thread structure only.** A placeholder stays as a structural node so that replies under it keep their parent. It is excluded from classification, priority, review queues, evaluation, and every count or metric. It is not a comment from anyone. The placeholder's own payload contains no commenter content and may be stored.

**Unexpected shapes are never classified silently.** A node that is authorless in any other way (null or missing `user`, a `user` without an ID), or has keys outside the known set, is not treated as a placeholder. It is flagged as an unexpected shape, the sync records a limitation, and a friction entry is written before the run is used.

**Authorship is never inferred from a placeholder.** For a comment observed before deletion, authorship and `is_content_author` are carried from the last pre-deletion observation, because they are non-content and survive the purge. For a comment first observed as a placeholder, authorship is `UNKNOWN`.

## Consequences

- Evaluation re-runs may lose comments. Prior results stand and re-runs report withdrawals.
- A single missed sync does not trigger a purge; a source placeholder does.
- Deletion detection handles two representations, and the placeholder rule is deliberately narrow: only the exact observed shape qualifies.
- Count reconciliation against `comments_count` compares live comments only.
- Replies to a deleted author comment keep `REPLY_TO_AUTHOR` only when authorship was known before deletion.
- Deletion paths other than author self-deletion remain `UNKNOWN` until observed. Observing one is a trigger to revisit this ADR.
