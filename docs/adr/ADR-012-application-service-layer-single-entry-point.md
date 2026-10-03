# ADR-012: The Application Service Layer Is the Single Entry Point

**Status:** Accepted. The service-layer rule applies now. External interfaces (HTTP API, MCP server) are deferred, with constraints recorded here.

## Context

Afterword already isolates source platforms behind adapters (ADR-001). The other direction has no rule yet. Today the CLI is the only frontend, but a review interface (Stage 4) is planned, and an external API or MCP server would allow natural-language questions such as:

- "What comments from this week deserve my attention?"
- "Show me the comments that caused a change to one of my projects."
- "What has a given commenter said about a topic across my recent articles?"

If each frontend reaches into storage and logic directly, every new interface duplicates rules and can drift from the priority policy, the privacy boundaries, or provenance. Retrofitting a single entry point after several frontends exist is expensive. Establishing it while there is only one frontend is cheap.

The three questions also differ sharply in risk. The first is the core triage query. The second queries propagation events (C-007), which are structured and human-recorded. The third is retrieval by person, which is commenter history (C-005, deferred over reputation-bias concerns) combined with topical search, and is the query most likely to turn Afterword into a dossier tool.

## Decision

### Shape

```text
DEV (and future sources)
        |
   adapters (ADR-001)        <- source semantics stop here
        |
   canonical model, policy, classification
        |
   application service layer <- the only entry point
        |
   transports: CLI now; review UI, HTTP API, MCP server later
```

**Adapters inward, Afterword service layer outward.**

### Rules that apply now

1. All frontends call a small set of typed application service functions. No frontend reads storage, calls adapters, or applies policy directly.
2. The CLI is a transport. CLI commands parse arguments, call service functions, and format output. Logic does not live in CLI code.
3. Service functions take explicit filters (time window, tier, content, propagation kind) and return domain objects, never source payloads.
4. Every returned object carries provenance: comment IDs, source links, and the versions (taxonomy, policy, model, prompt) behind any interpretation, so any answer built on it can cite its sources.
5. Read operations and write operations are separate functions. Writes (dispositions, overrides, propagation events, labels) are explicit and auditable.
6. Transport code (argument parsing, HTTP, MCP protocol) never appears in the core.

**Adoption is incremental.** Existing commands (`probe`, `baseline`, `label`) move behind service functions when they are next changed substantively. No standalone refactor is required.

### Constraints on future external interfaces

These apply when an HTTP API or MCP server is built. Neither is in V1 scope (see `SCOPE.md`).

1. **Service layer only.** External interfaces are transports over the same functions the CLI uses.
2. **Read-only first.** The first release of any external interface exposes read operations only.
3. **Human confirmation for writes.** Any write exposed externally requires per-action human confirmation (ADR-003). A client model may propose a disposition; it may not record one unconfirmed.
4. **The policy ranks, not the client.** Attention queries return the priority policy's tiers and `rule_applied`. A client model may summarize the queue; it must not re-rank it. Otherwise model-chosen priority returns through the interface, undoing ADR-007.
5. **Comment text is untrusted for the client model too.** Returned comment text is clearly delimited and labeled as data, because it becomes input to whatever model sits behind the client (ADR-008).
6. **The model boundary applies.** An MCP client typically sends returned content to a model provider. Exposing comment text through any external interface requires the model-boundary record in `PRIVACY-AND-BOUNDARIES.md` to cover that path.
7. **Local first.** The default MCP deployment is a local stdio server reading local storage. Any network-exposed interface requires its own ADR.
8. **Person queries need their own ADR.** Retrieval by commenter identity is not exposed through any interface until C-005 has been evaluated for reputation bias and a dedicated ADR accepts it, including what may be returned and what is excluded.
9. **Semantic search needs its own ADR.** Topic queries implying embeddings introduce a new model boundary and storage of derived representations of other people's text.

## Consequences

- One place enforces policy, privacy, and provenance, regardless of frontend.
- A review UI, HTTP API, or MCP server becomes a thin layer rather than a parallel implementation.
- Propagation queries ("what changed because of these comments?") are the natural first external capability, since they are structured, human-recorded, and distinctive.
- The CLI becomes slightly more formal than a script would be. That cost is accepted.
- External interfaces are the most demo-friendly feature available, which makes them a scope risk. They remain gated on the Stage 3 result.