# ADR-008: Comment Content Is Untrusted Model Input

**Status:** Accepted for V1

## Context

Comments are written by people outside the author's control and passed to a model. The system's costliest failure is a consequential comment being deprioritized, and comment text could be written to cause exactly that.

## Decision

Comment text is delimited and labeled as data in prompts. Model output is schema-constrained; anything else is treated as a failed classification and surfaced. A deterministic pre-check flags instruction-like text and forces `SURFACE`. The model has no tools or write access. Injection cases are part of the adversarial evaluation set.

## Consequences

- Manipulation can at most raise attention, not suppress it, within the limits of policy.
- Some benign comments will be surfaced unnecessarily by the pre-check. This is an accepted false-positive cost.
- Injection resistance is measured, not assumed.
