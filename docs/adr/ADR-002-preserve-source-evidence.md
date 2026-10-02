# ADR-002: Preserve Source Evidence Separately from Interpretation

**Status:** Accepted for V1

## Context

Normalization and AI classification can make derived records look authoritative. Reprocessing and debugging require access to what the source actually supplied.

## Decision

Preserve source records separately from normalized records, classifications, human judgments, and dispositions. Derived records reference their evidence and versioned processing rules.

## Consequences

- Reclassification does not rewrite historical source data.
- Source semantics remain inspectable.
- Storage requirements increase modestly.
- Secret and unnecessary fields must be removed or protected according to privacy policy.
