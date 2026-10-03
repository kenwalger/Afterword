# Scope

**Version:** 3 (2026-10-02)

v3 adds the external interface direction (ADR-012): out of current scope, recorded as a future candidate with its limits.

## Scope rule

**We are not building a community management platform.**

V1 exists to test whether assisted comment triage can preserve consequential conversations while reducing review effort, and whether it does so better than simple heuristics.

## In current scope: V1

### Source

- DEV only.
- Personal API access and publicly available records permitted by DEV's API and terms.
- The author's own posts and the comments on those posts.

### Ingestion and sync

- Fetch a bounded set of the author's published posts.
- Fetch all available comments for those posts, preserving thread structure.
- Initial backfill, then repeatable incremental sync.
- Detect comments that are new since the last sync, comments whose content changed, and comments no longer returned by the source.
- Preserve source IDs, timestamps, URLs, author identifiers, and source payloads needed for reproducibility.
- Record every sync run and the API limitations it encountered.

### Normalization

- Keep source records separate from normalized records (ADR-002).
- Normalize posts, comments, thread relationships, and platform identities.
- Convert source comment bodies (DEV supplies HTML) into a versioned plain-text representation for classification, preserving code blocks and links as structure rather than flattening them away. The original body is retained.
- Mark comments authored by the post's author. They are thread context, not triage subjects (ADR-011).
- Represent missing or unavailable fields with explicit value states, never a generic null.

### Classification

- Taxonomy defined in `TAXONOMY.md`: exactly one primary class plus zero or more flags.
- Model output is limited to class, flags, optional confidence, and explanation.
- Comment content is untrusted input (ADR-008).

### Priority

- Priority is computed by the explicit policy in `PRIORITY-POLICY.md`, not chosen by the model (ADR-007).
- Three tiers: `SURFACE`, `QUEUE`, `COLLAPSED`. The review threshold sits between `QUEUE` and `COLLAPSED`.

### Review

- Review queue ordered by tier.
- Suggested class, flags, policy-computed priority, and explanation.
- Human correction of class and priority.
- `Review all` path that exposes every collapsed comment.
- Thread and article context shown with each comment.
- Disposition recording: replied, no reply needed, investigate, save, propagate, defer.
- Review state: unseen, seen, dispositioned.
- Local instrumentation of review events, including expansion of collapsed groups and time spent per batch, for evaluation only.

### Evaluation

- Ground truth produced per `LABELING-GUIDE.md`.
- Development set (the historical corpus) for iteration; a prospective test set, sealed until measurement, for results (ADR-010).
- Three conditions: chronological baseline, heuristic baseline, LLM-assisted.
- Consequential recall, review reduction, qualitative analysis of every consequential miss.
- Separate adversarial set, including prompt-injection attempts.

### Propagation

Allow the human to record that a comment led to:

- reply only
- article correction
- article extension
- future article idea
- experiment
- code change
- specification or architecture change
- product or project opportunity
- investigated, original claim retained
- no further action

## Explicitly out of current scope

- CoderLegion integration.
- Substack integration.
- LinkedIn integration.
- Cross-platform identity resolution.
- Email-based identity matching.
- External identity enrichment or people search.
- Automatic substantive replies.
- Autonomous decisions about whether a person deserves a response.
- Automatic deletion, hiding, moderation, or blocking.
- Automated likes or reactions.
- Commenter history, follower counts, or reactions as priority inputs.
- Full creator analytics.
- Follower-growth forensics.
- CRM functionality.
- Lead scoring or sales qualification.
- Community health scoring.
- Public SaaS operation.
- Multi-tenancy.
- Billing.
- Team roles and permissions.
- Mobile applications.
- Comprehensive sentiment analysis.
- A universal definition of comment quality.
- Replacing platform-native moderation tools.
- Real-time notification. Sync is on demand or scheduled; freshness requirements are not part of V1.
- An HTTP API, MCP server, or any external interface (see ADR-012 and Future candidates).

## Future candidates, not commitments

If V1 produces useful evidence, later stages may investigate:

- CoderLegion as a second adapter.
- Cross-platform normalization of comments and reactions.
- Platform capability discovery.
- Longitudinal commenter context (C-005), evaluated for reputation bias before use.
- Identity reconciliation based only on authorized or voluntarily exposed evidence.
- Clustering repeated themes across posts.
- Lightweight acknowledgment workflows where APIs permit them.
- Validation with a second, higher-volume author.
- An external interface over the application service layer (ADR-012): first a local MCP server (stdio), possibly an HTTP API later. Gated on the Stage 3 result. Candidate first capabilities, in order: propagation queries ("which comments caused a change to one of my projects?"), then the attention queue as computed by the priority policy. Read-only first; writes need per-action human confirmation.
- Person-scoped queries ("what has this commenter said about X?") are explicitly not covered by the external interface above. They depend on C-005, require a reputation-bias evaluation, and need their own ADR. Topic queries implying semantic search also need their own ADR (a new model boundary).

These must not justify V1 architectural complexity unless V1 demonstrably requires it.

## Stop condition

Stop expanding V1 when the primary question can be answered with evidence. Do not add a platform merely because the adapter architecture permits it.

## Scope pressure

Anything that tries to enter V1 during implementation is recorded in the session summary of `FRICTION-LOG.md` under "Scope pressure," with the decision made.
