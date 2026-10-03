# Roadmap

**Version:** 2 (2026-10-02)

Each stage ends at a gate. A gate can return **continue**, **reframe**, or **stop**. Reframe and stop are recorded in `CLAIMS.md` and the friction log, not treated as failure.

## Stage 0: Freeze the experiment

Goal: define the question before implementation changes it.

- [x] Project brief and scope (v2)
- [x] Provisional taxonomy (`tax-v0.1`)
- [x] Provisional priority policy (`pp-v0.1`)
- [x] Labeling guide (`lg-v0.1`)
- [x] ADR-001 to ADR-011 (ADR-012 and ADR-013 added later: the service layer, and local-first with a hosted path preserved)
- [x] Friction log started
- [x] Verify DEV capabilities marked `DOCUMENTED` in the capability matrix (2026-10-02; matrix v3)
- [x] Measure volume baseline: comments per post and per week across the author's DEV history (C-009; 2026-10-02)
- [ ] Time chronological reviews of two weeks, a typical week and a busy week (C-009; `afterword label --mode chronological`)
- [ ] Define fixture format and corpus manifest
- [x] Decide corpus targets (2026-10-02: historical `dev`, prospective `test`; ADR-010 amended, `docs/proposals/accepted/2026-10-02-corpus-targets.md`)
- [ ] Label the `dev` corpus (every historical comment from others) per the labeling guide
- [x] Build the adversarial set, including injection cases (2026-10-03: synthetic, 24 cases, `fixtures/corpus/adversarial.jsonl`; hand-picked hard cases from labeling notes may be added as a new version)

**Gate:** if C-009 shows trivial volume, decide explicitly whether to continue as a methodology study. Otherwise continue.

## Stage 1: DEV ingestion

Goal: reliably obtain real source data.

- Authenticate.
- Fetch a bounded set of authored posts.
- Fetch threaded comments per post.
- Record SyncRuns and SourceRecords with payload hashes.
- Capture sanitized fixtures.
- Record pagination, rate limits, missing fields, and API friction.
- Determine how edits and deletions appear.

**Gate:** a repeatable sync reproduces the corpus, and edit and deletion behavior is known.

## Stage 2: Normalization and local persistence

Goal: separate source evidence from interpretation.

- Source adapter interface.
- HTML-to-text normalization, versioned, preserving code and links.
- Comments, threads, platform identities, author-comment marking.
- Value states and lifecycle states.
- Provenance links.
- Purge path for upstream deletion.

**Gate:** classifier and UI code need no DEV-specific payload knowledge.

## Stage 3: Classification experiment

Goal: determine whether assisted triage is useful before building a large UI.

### 3a: Development

- Implement taxonomy prompt with schema-constrained output.
- Implement priority policy.
- Implement heuristic baseline (B1).
- Iterate on `dev` only.
- Run the adversarial set; fix injection handling.

### 3b: Preregistration

Prerequisite, before preregistration can happen:

- `afterword label --set test` selects only test-set comments (posts published after preregistration).

Then:

- Freeze all versions.
- Recompute the accrual estimate from the observed `dev` consequential share and record it in `EVALUATION.md`.
- Write registered thresholds into `EVALUATION.md`, with the accrual procedure and stopping rule.
- Commit. The commit time starts accrual (ADR-010).

### 3c: Accrual and measurement

- Weekly, until the stopping rule (both 20 consequential and 100 total test comments, or 16 weeks): sync, run B1 and B2 in shadow mode with outputs hashed and hidden, and label new test comments blind.
- When accrual stops, verify the sealed outputs against their hashes, reveal them, and score B1 and B2 once.
- Consequential miss review.
- Labeler self-agreement check (if 14 days have passed).
- Write the evaluation report.

**Gate:**

- *Continue* if B2 meets registered thresholds and beats B1 meaningfully.
- *Reframe* if B1 is close to B2 (the result becomes "heuristics plus policy are enough") or if hindsight dominates consequentiality (C-010).
- *Stop* if consequential misses are common under every condition.

**Portfolio checkpoint:** the evaluation report and public write-up are produced here regardless of gate outcome.

## Stage 4: Review interface

Goal: make the experiment usable in daily operation.

- Tiered review queue.
- Class, flags, tier, rule applied, explanation.
- Human override.
- Collapsed group with `Review all`.
- Thread and article context.
- Disposition tracking, including inferred `REPLIED`.
- Review event instrumentation.
- No autonomous replies.

**Gate:** the author processes real batches and effort is compared with chronological review (C-002, C-004).

## Stage 5: Propagation and continuity

Goal: capture what conversation changes.

- Propagation events.
- Theme clustering across posts.
- Weekly synthesis built from records and human dispositions only.
- Evaluate C-005 (commenter history) for reputation bias before any use.

**Gate:** the application can answer "what happened because of these comments?" (C-007).

## Stage 6: Second-source decision gate

Only after V1 evidence exists, decide whether CoderLegion adds a useful test of the adapter model.

- Verify the CoderLegion matrix.
- Create fixtures.
- Document missing semantics.
- Decide whether limitations still permit useful ingestion.

## Deferred

Cross-platform identity reconciliation, Substack, LinkedIn, additional analytics, and external-user testing. None is promised by this roadmap.

- External interface (ADR-012): a local MCP server first, possibly an HTTP API later, over the application service layer. Gated on the Stage 3 result; see `SCOPE.md` (Future candidates) for its limits.
