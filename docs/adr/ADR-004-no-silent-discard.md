# ADR-004: Low-Priority Comments Are Collapsed, Not Discarded

**Status:** Accepted for V1

## Context

The highest-cost classifier error is potentially a consequential comment assigned low priority. A filtering system that hides such comments makes the error difficult to detect.

## Decision

No comment is silently removed from the reviewable corpus because of model priority. Low-priority comments may be grouped or collapsed, but the interface must provide an obvious path to inspect all of them.

## Consequences

- The system reduces immediate attention rather than access.
- Users retain the ability to audit false negatives.
- Inbox Zero is not a design goal.
