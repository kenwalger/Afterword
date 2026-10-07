# Roadmap

**Version:** 5 (2026-10-07)

v5 lists the future features (`FUTURE-FEATURES.md`) under Deferred in their suggested order, moves the parking-lot note on reaction counts to `FUTURE-FEATURES.md`, and records `lg-v0.4` (the label UI's post panel).

v4 adds the labeler calibration exercise to Deferred (`LABELING-AT-SCALE.md`) and removes a stale "not yet recorded" note from the Stage 0 gate input, since the gate decision is recorded below it.

v3 records the Stage 1, 2, and 3a groundwork built ahead of Stage 0's end, separating "built" from "gate passed"; corrects the labeling guide version to `lg-v0.2` and the ADR range to ADR-001 to ADR-013; splits the fixture item into the synthetic manifest (done) and the real corpus manifest (not yet); and adds the explanation warning to Stage 4.

Each stage ends at a gate. A gate can return **continue**, **reframe**, or **stop**. Reframe and stop are recorded in `CLAIMS.md` and the friction log, not treated as failure.

**Built is not a passed gate.** Stage 1 to 3a groundwork that needs no labels and no real comment data was built ahead, in sessions 4 and 5, while Stage 0 is still open. In those stages a checked item is built and tested; unless it says otherwise, tested on synthetic fixtures only. A gate is passed only when it is evaluated on real data and the result recorded. As of v3, no gate after Stage 0's has been evaluated, and no model has classified a real comment.

## Stage 0: Freeze the experiment

Goal: define the question before implementation changes it.

- [x] Project brief and scope (v2)
- [x] Provisional taxonomy (`tax-v0.1`; `tax-v0.2` from 2026-10-04, no class changes)
- [x] Provisional priority policy (`pp-v0.1`)
- [x] Labeling guide (`lg-v0.2`; `lg-v0.3` from 2026-10-04 adds the calibration pass and the analysis-label rule; `lg-v0.4` from 2026-10-07 adds the label UI's post panel)
- [x] ADR-001 to ADR-013 (ADR-001 to ADR-011 with the design; ADR-012, the service layer, and ADR-013, local-first with a hosted path preserved, added 2026-10-03)
- [x] Friction log started
- [x] Verify DEV capabilities marked `DOCUMENTED` in the capability matrix (2026-10-02; matrix v3)
- [x] Measure volume baseline: comments per post and per week across the author's DEV history (C-009; 2026-10-02)
- [x] Time chronological reviews of two weeks, a typical week and a busy week (C-009; `afterword label --mode chronological`; timed 2026-10-03, recorded in `CLAIMS.md` 2026-10-04: typical week 3.8 minutes, busy week 17.5 minutes, both re-reads)
- [x] Define the fixture format and the synthetic corpus manifest (2026-10-03: `fixtures/README.md`, `fixtures/corpus/MANIFEST.md`, with hashes checked by a test)
- [ ] Real corpus manifest: `dev` file hashes, committed when `dev` is frozen at preregistration (ADR-010)
- [x] Decide corpus targets (2026-10-02: historical `dev`, prospective `test`; ADR-010 amended, `docs/proposals/accepted/2026-10-02-corpus-targets.md`)
- [ ] Label the `dev` corpus (every historical comment from others) per the labeling guide
- [x] Build the adversarial set, including injection cases (2026-10-03: synthetic, 24 cases, `fixtures/corpus/adversarial.jsonl`; hand-picked hard cases from labeling notes may be added as a new version)

**Gate:** if C-009 shows trivial volume, decide explicitly whether to continue as a methodology study. Otherwise continue.

Gate input (2026-10-04): the typical week's read took under 4 minutes, which meets C-009's falsification condition; the busy week's took about 17.5 minutes, which does not. The decision is the author's.

Gate decision (2026-10-04, the author): **continue as planned.** The cost of chronological review is concentrated in busy weeks; whether assisted triage pays off mainly there is recorded as C-012 and measured on the test period.

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

Gate evidence (2026-10-07, session 8; built on 2026-10-03, first run on real data now; counts from `afterword ingest` and `afterword store-status`):

- **Two real runs ingested in order** into an empty store: `20261003T141450Z` (713 comments new, 1 deletion placeholder first seen), then `20261007T224849Z` (36 new, 524 payload changed with text unchanged, 190 unchanged). Store after both: 140 posts, 458 live comments from others (the same 458 the labeling tools count as eligible), 291 by the author, 1 placeholder.
- **Lifecycle transitions across the two runs:** new 36; edited 0; missing 0; deleted by absence 0; placeholder 1, first seen in the first run (`DELETED_UPSTREAM`, `SOURCE_PLACEHOLDER`, authorship `UNKNOWN`, no text stored) and unchanged in the second. The 524 payload changes are DEV's AI-disclosure keys, added to every older comment between the runs; no normalized text changed, so nothing became `EDITED` or needed reclassification.
- **Placeholder handling:** recognized in both runs once ADR-009 was amended (2026-10-07) to ignore the allowlisted platform-wide keys; before the amendment the second run's placeholder was an unexpected shape (`docs/friction-log/session-8.md`).
- **Purge:** no comment went from live to deleted between the runs, so the purge path itself did not run on real data. Check: 0 deleted or purged comments hold text.
- **Repeatability:** ingesting `20261007T224849Z` a second time was refused ("already ingested") and left the store unchanged (2 runs, 750 comments). Count reconciliation leaves the same 3 posts unexplained in both runs (`comments_count` one higher than the live comments observed).
- **Not covered:** an edit observed on real data, deletion by absence, and every deletion path other than author self-deletion.

Gate decision: not recorded; the author's.

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

- [x] Implement taxonomy prompt with schema-constrained output. (2026-10-03: classifier `pr-v0.1` with an incremental cache, `pr-v0.2` from 2026-10-04 without the code and link flags; Ollama provider, path signed off; Anthropic provider, path not signed off, tested against mocked HTTP only.)
- [x] Implement priority policy. (2026-10-03: `pp-v0.1` as pure, tested code, recording `rule_applied` and `rules_fired`.)
- [x] Implement heuristic baseline (B1). (2026-10-03: `hb-v0.1`, a draft until tuned on `dev`.)
- [ ] Iterate on `dev` only. (Needs `dev` labels.)
- [ ] Run the adversarial set; fix injection handling. (2026-10-03: run once on both local models, synthetic sets only, `docs/benchmarks/2026-10-03-synthetic-local-models.md`. Rerun 2026-10-04 under `pr-v0.2`: injection tiers unchanged, 8 of 10 for both. The pre-check `pc-v0.1` has two known gaps, adv-109 and adv-110, not yet fixed.)

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

- Labeler calibration exercise (`LABELING-AT-SCALE.md`, Labeler onboarding): about 20 synthetic comments with researcher-approved reference labels and rationales, covering the boundaries that change a tier or proved hard in V1 labeling; reveal-after-answer in the label UI; agreement summarized per boundary; answers recorded as `sample_kind: calibration_exercise` and excluded from every measure. Gated on the Stage 3 result, except that a minimal version may be built earlier as an optional refresher for the author's calibration pass.
- External interface (ADR-012): a local MCP server first, possibly an HTTP API later, over the application service layer. Gated on the Stage 3 result; see `SCOPE.md` (Future candidates) for its limits.
- Future features (`FUTURE-FEATURES.md`), each gated on the Stage 3 result, with proposed claims C-013 to C-019 (`CLAIMS.md`). Grouping by commenter stays excluded without the C-005 evaluation and its own ADR. In the suggested order, for the author:
  1. Spike insurance (C-012).
  2. Propagation ledger with assisted suggestions (C-013).
  3. Rediscovery, cheap version: no new model work (C-014).
  4. Reply context, excerpts only: keyword retrieval over the author's own words (C-015).
  5. Topical rediscovery and semantic reply context, after the semantic-search ADR.
  6. Position summaries, last, and only with the grounding rules (C-016).
- For high-volume and team accounts, after discovery conversations confirm the need (`FUTURE-FEATURES.md`):
  1. Unanswered-questions queue (C-018).
  2. Duplicate-question clustering, after the semantic-search ADR (C-017).
  3. Feedback extraction: one output adapter first, plus the taxonomy-extension design (C-019).
  4. Cross-platform aggregation, after one platform works well (Stage 6).
