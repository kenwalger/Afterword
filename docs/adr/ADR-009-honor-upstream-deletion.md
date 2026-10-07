# ADR-009: Upstream Deletion Propagates to Local Data

**Status:** Accepted, provisional (amended 2026-10-02 and 2026-10-07)

The 2026-10-02 amendment is based on one self-deleted sample per case (a comment without replies and a comment with a reply, both deleted by their author, who is also the post author). Deletion by another user, moderator removal, and account deletion are untested. Any of them may look different, and this ADR is revisited when one is observed.

The 2026-10-07 amendment changes how the placeholder is matched, after DEV added two keys to every comment node, the placeholder included (run `20261007T224849Z`; `docs/friction-log/session-8.md`). It matches by the placeholder's distinguishing features instead of its exact key set, and ignores an explicit allowlist of platform-wide keys. The evidence base for what a deletion looks like is unchanged, so the status stays provisional.

## Context

A commenter who deletes a comment on DEV has withdrawn it. Keeping its text locally, in a corpus, or in a published dataset would preserve something the author chose to remove.

The original decision assumed deletion appears as absence. A hand test on 2026-10-02 showed DEV has two representations (see `docs/proposals/accepted/2026-10-02-deletion-placeholders.md` and `docs/API-CAPABILITY-MATRIX.md`):

- A deleted comment **without replies** disappears from the thread.
- A deleted comment **with replies** remains as a **placeholder**. It keeps its `id_code`, `created_at`, `type_of`, and `children`; its body is replaced; and its `user` is an empty object. The placeholder persisted after its last reply was deleted. DEV's `comments_count` excludes placeholders.

Between runs `20261003T141450Z` and `20261007T224849Z`, DEV extended `ai_disclosure_label` and `ai_disclosure_level` from 189 of 714 comment nodes (the newer comments) to 750 of 750, including the one known placeholder, whose other fields were unchanged. Under the exact-key-set rule of 2026-10-02 that placeholder became an unexpected shape. DEV's comment schema can change without notice, so a rule that depends on the whole key set breaks on any platform-wide addition, while a rule that ignores unknown keys would let a genuinely new shape pass silently.

## Decision

A comment becomes `DELETED_UPSTREAM` when either:

1. **Absence:** it is absent from two consecutive complete syncs of its post, or
2. **Source placeholder:** the source returns it as a deletion placeholder. One observation is enough, because the source has stated the deletion explicitly.

**Matching the placeholder (DEV).** A node is a deletion placeholder when it has all of the placeholder's distinguishing features:

- `user` is an empty object;
- the body is replaced with the placeholder text (a short body that names the deletion);
- `id_code`, `created_at`, and `children` are kept, and every other key of the first observed placeholder (`type_of`, `body_html`, `user`) is present.

Keys on an explicit **allowlist of platform-wide fields** are ignored when matching. The allowlist starts with `ai_disclosure_label` and `ai_disclosure_level`, with run `20261007T224849Z` as the evidence that DEV now adds them to every comment. Adding a key to the allowlist requires evidence recorded in the friction log that the source adds it platform-wide. Any other key outside the known set still marks the node as an unexpected shape.

Its body text and raw payloads are purged from local storage and corpus files at the next sync. Identifiers, thread position, lifecycle history, and non-content judgments may remain.

**Placeholders are thread structure only.** A placeholder stays as a structural node so that replies under it keep their parent. It is excluded from classification, priority, review queues, evaluation, and every count or metric. It is not a comment from anyone. The placeholder's own payload contains no commenter content and may be stored.

**Unexpected shapes are never classified silently.** A node that is authorless in any other way (null or missing `user`, a `user` without an ID, an empty `user` without the placeholder body or a kept field), or has keys outside the known set and the allowlist, is not treated as a placeholder. It is flagged as an unexpected shape, the sync records a limitation, and a friction entry is written before the run is used. Unknown keys are signals to investigate, not errors that stop ingestion.

**Authorship is never inferred from a placeholder.** For a comment observed before deletion, authorship and `is_content_author` are carried from the last pre-deletion observation, because they are non-content and survive the purge. For a comment first observed as a placeholder, authorship is `UNKNOWN`.

## Consequences

- Evaluation re-runs may lose comments. Prior results stand and re-runs report withdrawals.
- A single missed sync does not trigger a purge; a source placeholder does.
- Deletion detection handles two representations. The placeholder rule stays deliberately narrow: all distinguishing features must be present, and only allowlisted keys are ignored.
- A platform-wide key that DEV adds later makes the placeholder an unexpected shape again until it is allowlisted with evidence. That is the intended failure: visible, recorded, and never silent.
- Count reconciliation against `comments_count` compares live comments only.
- Replies to a deleted author comment keep `REPLY_TO_AUTHOR` only when authorship was known before deletion.
- Deletion paths other than author self-deletion remain `UNKNOWN` until observed. Observing one is a trigger to revisit this ADR.
