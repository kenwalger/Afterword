# Friction and Delight Log

Start logging before the first API call. Record what happened at the time rather than reconstructing it later.

## Classification

Use one of:

- `PRODUCT` - platform/API behavior
- `DOMAIN` - comment/community semantics
- `PROJECT` - our own design/implementation
- `ENVIRONMENT` - tooling/runtime/setup
- `UNKNOWN` - cause not established

## Entry template

### YYYY-MM-DD HH:MM - Short title

**Platform:** DEV / CoderLegion / Project

**Type:** FRICTION / DELIGHT / SURPRISE

**Class:** PRODUCT / DOMAIN / PROJECT / ENVIRONMENT / UNKNOWN

**Task:** What was I trying to do?

**Expectation:** What did I expect to happen?

**Observation:** What actually happened? Preserve facts before interpretation.

**Evidence:** Endpoint, response shape, screenshot, fixture, error, or other supporting artifact.

**Workaround:** What did I do, if anything?

**Consequence:** Time cost, architectural change, missing capability, new idea, or no consequence.

**Follow-up:** Question or action, if any.

---

## Session summary template

### YYYY-MM-DD - Session summary

**Goal:**

**Completed:**

**Friction discovered:**

**Delight discovered:**

**Claims affected:**

**ADRs affected:**

**Scope pressure:** Anything that tried to sneak into V1?

**Next smallest useful step:**

---

## Initial observation

### 2026-10-02 - CoderLegion API is authenticated and capability-limited

**Platform:** CoderLegion

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Determine whether CoderLegion could plausibly become a future source adapter.

**Expectation:** Public searching did not clearly reveal API documentation; API availability was uncertain.

**Observation:** `/api-docs` exists behind authentication. Personal API keys are documented for post search/list/fetch/create/edit, feeds/categories/groups, cover uploads, notifications, and comment/reply write/edit/hide/reshow operations. The provided restricted-endpoint list does not explicitly include follower, reaction, analytics, profile lookup, or comment-read endpoints.

**Evidence:** User-provided excerpt from authenticated CoderLegion API documentation.

**Workaround:** None required for V1 because CoderLegion is out of current scope.

**Consequence:** Second-source feasibility is plausible, but actual read capabilities must be tested rather than inferred.

**Follow-up:** Revisit only at the Stage 6 decision gate.

### 2026-10-02 - DEV comment bodies arrive as HTML

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Fill the DEV column of the capability matrix from documentation before any requests.

**Expectation:** Comment bodies available as Markdown, matching how they are written.

**Observation:** Documentation describes `GET /api/comments?a_id=` as public, returning threaded comments with nested `children`, an `id_code` identifier, `created_at`, an embedded `user`, and the body as `body_html`. No Markdown body is described. No edited timestamp or deletion representation is described.

**Evidence:** Forem API v1 reference documentation and published OpenAPI descriptions. Not yet verified by request.

**Workaround:** None yet.

**Consequence:** Normalization needs a versioned HTML-to-text step that preserves code and links. Edit detection may have to rely on payload hashes. Deletion semantics must be discovered empirically.

**Follow-up:** Verify in Stage 0 and capture sanitized fixtures.

---

### 2026-10-02 - Session summary

**Goal:** Review v1 scoping and produce v2.

**Completed:** Renamed project to Afterword. Added taxonomy, priority policy, and labeling guide. Split corpus into dev and sealed test sets. Added heuristic baseline, adversarial and injection set, lifecycle and deletion handling, review instrumentation, and ADR-007 to ADR-011.

**Friction discovered:** v1 defined consequential recall against a review threshold that did not exist. The capability matrix was filled for the deferred platform and empty for the V1 platform.

**Delight discovered:** None recorded.

**Claims affected:** C-001 to C-004 gained measurement notes. C-008, C-009, C-010 added.

**ADRs affected:** ADR-007 to ADR-011 added. ADR-001 to ADR-006 unchanged.

**Scope pressure:** Considered using commenter novelty ("first comment from this identity") as a priority override. Rejected for V1 as a reputation signal under a different name.

**Next smallest useful step:** Measure comment volume across existing DEV posts (C-009).
