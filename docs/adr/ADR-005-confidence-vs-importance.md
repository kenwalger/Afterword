# ADR-005: Classification Confidence Is Not Comment Importance

**Status:** Accepted for V1

## Context

A model can be highly confident that a comment belongs to a class without that confidence establishing how consequential the comment is. Conversely, a short ambiguous correction may be highly important.

## Decision

Store classification confidence, when available, separately from priority/importance. Do not use model confidence as a direct proxy for importance.

## Consequences

- Priority policy must be explicit.
- UI must not visually imply that confidence is value.
- Evaluation can separately inspect classification certainty and consequential recall.
