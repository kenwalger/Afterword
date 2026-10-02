# ADR-006: Keep Platform Credentials Outside Model Context

**Status:** Accepted for V1

## Context

Platform API keys authorize access and potentially write operations. They are unnecessary for comment classification.

## Decision

Credentials remain in the application's secret boundary and are used only by source adapters. They must not be included in model prompts, logs, fixtures, source exports, or client-visible application state unless a platform explicitly requires a client-safe credential model.

## Consequences

- Adapter and classification boundaries remain separate.
- Fixtures must be sanitized.
- Secret handling is part of implementation review.
