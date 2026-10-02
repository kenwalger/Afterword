# ADR-009: Upstream Deletion Propagates to Local Data

**Status:** Accepted for V1

## Context

A commenter who deletes a comment on DEV has withdrawn it. Keeping its text locally, in a corpus, or in a published dataset would preserve something the author chose to remove.

## Decision

A comment absent from two consecutive complete syncs, or marked deleted by the source, becomes `DELETED_UPSTREAM`. Its body text and raw payloads are purged from local storage and corpus files at the next sync. Identifiers, lifecycle history, and non-content judgments may remain.

## Consequences

- Evaluation re-runs may lose comments. Prior results stand and re-runs report withdrawals.
- A single missed sync does not trigger a purge.
- Deletion detection depends on DEV behavior that is still `UNKNOWN` and must be verified in Stage 1.
