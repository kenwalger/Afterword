# Roadmap

**Version:** 3 (2026-10-04)

v3 records the Stage 1, 2, and 3a groundwork built ahead of Stage 0's end, separating "built" from "gate passed"; corrects the labeling guide version to `lg-v0.2` and the ADR range to ADR-001 to ADR-013; splits the fixture item into the synthetic manifest (done) and the real corpus manifest (not yet); and adds the explanation warning to Stage 4.

Each stage ends at a gate. A gate can return **continue**, **reframe**, or **stop**. Reframe and stop are recorded in `CLAIMS.md` and the friction log, not treated as failure.

**Built is not a passed gate.** Stage 1 to 3a groundwork that needs no labels and no real comment data was built ahead, in sessions 4 and 5, while Stage 0 is still open. In those stages a checked item is built and tested; unless it says otherwise, tested on synthetic fixtures only. A gate is passed only when it is evaluated on real data and the result recorded. As of v3, no gate after Stage 0's has been evaluated, and no model has classified a real comment.

## Stage 0: Freeze the experiment

Goal: define the question before implementation changes it.

- [x] Project brief and scope (v2)
- [x] Provisional taxonomy (`tax-v0.1`)
- [x] Provisional priority policy (`pp-v0.1`)
- [x] Labeling guide (`lg-v0.2`)
- [x] ADR-001 to ADR-013 (ADR-001 to ADR-011 with the design; ADR-012, the service layer, and ADR-013, local-first with a hosted path preserved, added 2026-10-03)
- [x] Friction log started
- [x] Verify DEV capabilities marked `DOCUMENTED` in the capability matrix (2026-10-02; matrix v3)
- [x] Measure volume baseline: comments per post and per week across the author's DEV history (C-009; 2026-10-02)
- [ ] Time chronological reviews of two weeks, a typical week and a busy week (C-009; `afterword label --mode chronological`)
- [x] Define the fixture format and the synthetic corpus manifest (2026-10-03: `fixtures/README.md`, `fixtures/corpus/MANIFEST.md`, with hashes checked by a test)
- [ ] Real corpus manifest: `dev` file hashes, committed when `dev` is frozen at preregistration (ADR-010)
- [x] Decide corpus targets (2026-10-02: historical `dev`, prospective `test`; ADR-010 amended, `docs/proposals/accepted/2026-10-02-corpus-targets.md`)
- [ ] Label the `dev` corpus (every historical comment from others) per the labeling guide
- [x] Build the adversarial set, including injection cases (2026-10-03: synthetic, 24 cases, `fixtures/corpus/adversarial.jsonl`; hand-picked hard cases from labeling notes may be added as a new version)

**Gate:** if C-009 shows trivial volume, decide explicitly whether to continue as a methodology study. Otherwise continue.

## Stage 1: DEV ingestion

Goal: reliably obtain real source data.

- [x] Authenticate. (2026-10-02: the read-only probe, against DEV.)
- [x] Fetch a bounded set of authored posts. (2026-10-02: the probe, against DEV.)
- [x] Fetch threaded comments per post. (2026-10-02: the probe, against DEV.)
- [x] Record SyncRuns and SourceRecords with payload hashes. (2026-10-03: the store and `afterword ingest`, tested on synthetic fixtures.)
- [x] Capture sanitized fixtures. (2026-10-02: synthetic payloads in the observed shapes, `fixtures/dev-api/source/MANIFEST.md`.)
- [x] Record pagination, rate limits, missing fields, and API friction. (2026-10-02: capability matrix v3 and the friction log.)
- [x] Determine how edits and deletions appear. (2026-10-02: hand test, one self-deleted sample per case; ADR-009 accepted, provisional.)

**Gate:** a repeatable sync reproduces the corpus, and edit and deletion behavior is known.

Gate status: not evaluated. Two full probe runs returned identical results (2026-10-02), and edit and deletion behavior is known for author self-deletion only. A repeatable sync into the store, run on real data, has not been recorded.

## Stage 2: Normalization and local persistence

Goal: separate source evidence from interpretation.

- [x] Source adapter interface. (2026-10-03: the DEV adapter reads saved runs as sync observations; nothing outside it uses DEV field names.)
- [x] HTML-to-text normalization, versioned, preserving code and links. (2026-10-03: `norm-v0.1`, with edit detection by normalized text.)
- [x] Comments, threads, platform identities, author-comment marking. (2026-10-03: the SQLite store behind a repository interface, ADR-013.)
- [x] Value states and lifecycle states. (2026-10-03: a pure lifecycle planner covering every ADR-009 path.)
- [x] Provenance links. (2026-10-03: SourceRecords with payload hashes; classifications record every version and the input hash.)
- [x] Purge path for upstream deletion. (2026-10-03: the ADR-009 purge on ingest, and `afterword forget` for a whole connection.)

**Gate:** classifier and UI code need no DEV-specific payload knowledge.

Gate status: not evaluated on real data.

## Stage 3: Classification experiment

Goal: determine whether assisted triage is useful before building a large UI.

### 3a: Development

- [x] Implement taxonomy prompt with schema-constrained output. (2026-10-03: classifier `pr-v0.1` with an incremental cache; Ollama provider, path signed off; Anthropic provider, path not signed off, tested against mocked HTTP only.)
- [x] Implement priority policy. (2026-10-03: `pp-v0.1` as pure, tested code, recording `rule_applied` and `rules_fired`.)
- [x] Implement heuristic baseline (B1). (2026-10-03: `hb-v0.1`, a draft until tuned on `dev`.)
- [ ] Iterate on `dev` only. (Needs `dev` labels.)
- [ ] Run the adversarial set; fix injection handling. (2026-10-03: run once on both local models, synthetic sets only, `docs/benchmarks/2026-10-03-synthetic-local-models.md`. The pre-check `pc-v0.1` has two known gaps, adv-109 and adv-110, not yet fixed.)

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
- When POSSIBLE_INSTRUCTION_TEXT fires, the review UI marks the model's explanation as possibly influenced by the comment and shows the policy rule beside it (benchmark 2026-10-03: explanations went along with injections even where the tier was correct).
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
