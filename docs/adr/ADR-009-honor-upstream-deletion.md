# ADR-009: Upstream Deletion Propagates to Local Data

**Status:** Accepted, provisional (amended 2026-10-02, 2026-10-07, and 2026-10-08)

The 2026-10-02 amendment is based on one self-deleted sample per case (a comment without replies and a comment with a reply, both deleted by their author, who is also the post author). Deletion by another user, moderator removal, and account deletion are untested. Any of them may look different, and this ADR is revisited when one is observed.

The 2026-10-07 amendment changes how the placeholder is matched, after DEV added two keys to every comment node, the placeholder included (run `20261007T224849Z`; `docs/friction-log/session-8.md`). It matches by the placeholder's distinguishing features instead of its exact key set, and ignores an explicit allowlist of platform-wide keys. The evidence base for what a deletion looks like is unchanged, so the status stays provisional.

The 2026-10-08 amendment makes the code and this decision agree about saved probe runs. The purge had covered the store only, while the decision said "local storage"; the raw responses of earlier runs, under `fixtures/dev-api/source/real/`, still held a deleted comment's text and author (`docs/friction-log/session-9.md`). Saved runs are now redacted, never deleted, and a retention rule limits how long any saved run keeps text. What a deletion looks like on DEV is still known from author self-deletion only, so the status stays provisional.

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

**Saved probe runs (amended 2026-10-08).** The ingest that records a deletion also redacts the comment in every saved run that holds it: its text and its author fields are removed, and its ID, creation time, and place in the thread stay, with a marker saying it was redacted as deleted. DEV's own placeholders hold no commenter content and are left as they are. A run is never deleted. Each redaction is recorded (run, comment ID, date) in a git-ignored log, `reports/redactions.jsonl`. A redacted run still loads; the redacted comment reads as a deletion placeholder.

**Retention (amended 2026-10-08).** Saved runs older than the newest N (default 3; `afterword ingest --keep-runs N`) are reduced, at ingest, to IDs, timestamps, counts, and thread structure: every comment's text and author fields go except the numeric author ID, which keeps authorship countable, and posts lose titles, bodies, links, and tags. Two kinds of run are not reduced: a run newer than the run being ingested (it may still need ingesting), and a run that labels were made from (its text is the context those labels, and later calibration and self-agreement passes, depend on). A run kept for labels is still redacted for deletions. A reduced run cannot be ingested, and each reduction is logged.

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
- Re-running a measurement on a reduced run gives the same counts but no text; labeling or classifying from it is not possible. Measurements that need text use a recent run.
- A run that labels were made from keeps its text for as long as those labels exist, apart from deleted comments. Deleting the labels lets the next ingest reduce it.
- The pre-commit identity scan reads names and handles from saved runs, so a reduced run no longer contributes the names it held. The newest runs, and any run kept for labels, still do.
