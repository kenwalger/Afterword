# ADR-007: Priority Is Computed by Explicit Policy, Not by the Model

**Status:** Accepted for V1

## Context

v1 stored a model-suggested priority with no defined scale or threshold, while the primary metric depended on a review threshold. A model-chosen priority is hard to audit, shifts with prompt changes, and can be manipulated through comment text.

## Decision

The model produces class, flags, optional confidence, and explanation. A versioned, deterministic policy (`PRIORITY-POLICY.md`) maps those plus structural signals to a tier. Overrides may only raise a tier. Each assignment records the rule that produced it.

## Consequences

- The review threshold is explicit and testable.
- Policy can change without reclassifying, and classification can change without changing policy.
- The heuristic baseline and the model share the same policy, so their comparison isolates classification quality.
- Some nuance a model could express directly about importance is deliberately given up in exchange for auditability.
