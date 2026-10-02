# ADR-001: Use Source Adapters

**Status:** Accepted for V1

## Context

The first implementation uses DEV, but the experiment is about processing publishing conversations rather than DEV specifically. Future sources may expose different records and capabilities.

## Decision

Implement a source-adapter boundary. DEV-specific API payloads terminate at the adapter/source-record layer. Core application logic consumes canonical records with provenance back to the source.

## Consequences

- DEV does not become the domain model.
- Future sources can expose partial capabilities.
- Adapter complexity is accepted in exchange for preserving source boundaries.
- V1 must not build abstractions for hypothetical platforms beyond what is needed to keep DEV-specific payload logic localized.
