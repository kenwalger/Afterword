# ADR-013: Local-First Now, Hosted Path Preserved

**Status:** Accepted. Local deployment and the one-way-door rules apply now. Hosted or team operation is deferred, with its known implications recorded here.

## Context

V1 is a local, single-author installation. If Afterword succeeds beyond the experiment, two kinds of users are plausible, and they point in different directions:

- **Individual writers**, for whom local-first is the stronger product. Commenters' text never has to leave the author's machine, which is Afterword's most distinctive privacy property.
- **Teams** (DevRel, docs, or content teams triaging comments across an organization's posts), who need a shared queue, shared dispositions, and shared propagation records, and therefore a shared database.

Nothing about a hosted future needs to be built now. But some early choices are cheap today and expensive to reverse later: how records are identified, how time is stored, whether "the author" is assumed to be global, and whether storage is reachable from everywhere. A later migration from local to hosted, or a hybrid of the two, fails on these details rather than on missing features.

## Decision

### Deployment now

- Local, single-user installation.
- SQLite as the store.
- Each user supplies their own DEV API key and their own model (local via Ollama, or their own API key for a remote provider).

### One-way-door rules (apply now)

1. **Stable string identifiers.** Records are identified by source IDs where they exist (for DEV comments, `id_code`) and otherwise by generated UUIDs. Auto-incrementing integers are never used as record identity, since they collide when databases merge or one database serves several authors.
2. **UTC time.** All timestamps are stored in UTC as RFC 3339 with an explicit offset.
3. **No global identity.** The content author, credentials, and settings are attached to a configured platform connection, never to module-level constants. Every stored record can be traced to the connection that produced it.
4. **Portable records.** Stored rows contain no local filesystem paths, hostnames, or operating-system usernames. Paths belong in configuration, not in data.
5. **Storage behind a repository interface.** Only the application service layer (ADR-012) calls the repository. SQLite-specific SQL stays inside the repository implementation.

### Deliberately not built

Authentication, user accounts, tenancy, a server, sync, billing, and hosted inference. Building them now would mean designing for customers that do not exist, around a product whose core value has not yet been measured.

### Known implications of a future hosted or team mode

Recorded so that the decision starts from evidence rather than surprise. Any move toward hosted operation requires its own ADRs.

- **Data processing.** A hosted operator holds other people's comments on behalf of many customers. That brings data-processor obligations, breach exposure, deletion propagation across tenants (ADR-009), and a rewrite of `PRIVACY-AND-BOUNDARIES.md`.
- **Platform terms.** Commercial aggregation of DEV data needs review against DEV's API terms.
- **Storage.** Postgres with row-level security is the likely default, because Afterword's core queries (provenance chains, propagation links, policy and model versions) are relational. Per-tenant SQLite (libSQL-style) is a credible alternative if tenants stay isolated and small.
- **Inference.** Either customers supply their own model keys, or the operator hosts inference, which creates a model boundary per tenant.
- **Team features.** Shared queues, assignment, and shared dispositions are new capabilities, each needing design work against ADR-003 and ADR-004.
- **Hybrid by default.** Local-first remains supported. A hosted tier is additive, not a replacement.

### Trigger for revisiting

Hosted or team operation is considered only after the Stage 3 result exists and there is evidence of demand from people other than the author.

## Consequences

- Moving to a hybrid or hosted model later becomes a matter of adding a repository implementation and a deployment, not migrating identifiers, timestamps, or embedded assumptions.
- The rules cost almost nothing now: string IDs and UTC timestamps are already the natural choice for DEV data.
- The privacy argument for local-first stays intact and explicit, which keeps it available as a product position rather than an accident of V1.
- Some generality (connection references on records) exists before it is needed. That cost is accepted as the price of keeping the hosted path open.