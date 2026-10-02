# ADR-010: Test Sets Are Sealed Until Preregistration

**Status:** Accepted for V1

## Context

Iterating prompts, policy, or heuristics against the same data used to measure them overstates performance. With one labeler and a small corpus, the effect can be large.

## Decision

The corpus is split by post into a development set and sealed test sets. Test set hashes are committed before any classifier runs on them. All iteration happens on the development set. Thresholds and versions are registered in `EVALUATION.md` before the test sets are opened, and measurement runs once.

## Consequences

- Reported results reflect unseen data.
- Any change after measurement requires new versions and, for a clean result, a new sealed set.
- The development set must be large enough to iterate on, which competes with test set size. Splits are recorded in the corpus manifest.
