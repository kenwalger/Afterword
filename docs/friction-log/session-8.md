# Friction log: session 8

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 8: Part A, housekeeping, label summary, post panel (2026-10-07)

Times are UTC. No comment text, names, or handles: every figure below is a count, computed by code that printed aggregates only.

### 2026-10-07 22:55 - Orientation counts, at the source

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Orientation: check timing records, labels, and probe runs directly, as CLAUDE.md asks.

**Expectation:** 302 labels (150 in publication order, the rest shuffled with seed 20261004) and newest run `20261007T224849Z`, as the author stated.

**Observation:**
- Labels: 302 initial, 0 calibration, 0 self-agreement; one per comment. By post order 150 published, 152 random (one seed, 20261004, across 5 batches). `tax-v0.1` 150 and `tax-v0.2` 152; `lg-v0.2` 150 and `lg-v0.3` 152. All 302 were labeled from run `20261003T141450Z`, not the newest run. 11 batches (6 complete, 5 quit), 1 hard-to-label note.
- Timing: 2 valid records, 0 practice.
- Probe runs: 10; the newest, `20261007T224849Z`, has 140 posts, 750 comment nodes (291 by the author, 459 from others), and outcome `PARTIAL` (next entry). All 302 labeled comments are still eligible in it; it has 458 eligible comments, so 156 remain unlabeled against it.
- Check list at the start: all green, 625 tests on 3.14 and on 3.12 (isolated).

**Evidence:** `afterword label status --run 20261007T224849Z`; `afterword.label_records` and `afterword.timing.load_valid` (counts only); `reports/probe/*/probe-findings.json`.

**Workaround:** None needed.

**Consequence:** The author's figures match the records.

**Follow-up:** None.

### 2026-10-07 23:00 - The newest run is PARTIAL: the known deletion placeholder gained two keys

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Read the newest run's limitations before using it (`WORKFLOW.md`, section 1).

**Expectation:** A `COMPLETE` run, like `20261003T141450Z`.

**Observation:**
- `20261007T224849Z` is `PARTIAL` with one limitation: "1 comment node(s) with an unexpected shape; record a friction entry before using this run".
- The unexpected node is the same comment that `20261003T141450Z` recognized as the one deletion placeholder (same ID). Its `user` is still an empty object, and the only fields whose hashes changed are `ai_disclosure_label` and `ai_disclosure_level`, which it now carries.
- DEV appears to have backfilled those two keys onto every comment node: 750 of 750 nodes carry them in the new run, against 189 of 714 (the newer comments only) in `20261003T141450Z`.
- ADR-009's placeholder rule is deliberately exact (the observed key set, `user` equal to `{}`), so the extra keys make the node an unexpected shape. The code behaved as the ADR says: the node is excluded from labeling and classification, and the run is marked `PARTIAL`.
- Count reconciliation: 4 posts differ from DEV's `comments_count` (3 in `20261003T141450Z`), none involving a placeholder.

**Evidence:** `reports/probe/20261007T224849Z/probe-findings.json` (`limitations`, `comments.deletion_observation`, `comments.ai_disclosure`) and `shapes.json`; `comment-index.json` of both runs (keys and field hashes only, no values).

**Workaround:** None yet. The run was not used for labeling (all 302 labels come from `20261003T141450Z`).

**Consequence:** Until the placeholder rule accepts these keys, a deleted comment with replies on DEV now looks like an unexpected shape, so ADR-009's placeholder path never fires. Ingest stores nothing for an unexpected node and records a limitation (`lifecycle.py`), so into an empty store this deletion would not be recorded at all. The node has no remaining replies, as in the earlier run, so no labeled comment's context depends on it.

**Follow-up:** A decision for the author before Part B's ingest: accept `PLACEHOLDER_KEYS` plus the two `ai_disclosure_*` keys as the placeholder shape (an amendment to ADR-009's "observed key set", with this run as the observation), or keep the rule and ingest the node as an unexpected shape. Ingesting `20261003T141450Z` first, then `20261007T224849Z`, would also exercise the lifecycle across two real runs (36 comments are new in the later run, none disappeared).

### 2026-10-07 23:05 - Most of the docs wiring was already done

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** A1: wire `LABELING-FIELD-GUIDE.md` and `FUTURE-FEATURES.md` into the docs.

**Expectation:** The field guide not yet in the reading order, `LABELING-GUIDE.md`, `WORKFLOW.md`, or CLAUDE.md.

**Observation:**
- Commit `530c50e` had already added the field guide to the README reading order (beside the labeling guide), with pointers from `LABELING-GUIDE.md` and `WORKFLOW.md`, and the CLAUDE.md rule on taxonomy and guide version changes. Nothing more was needed there.
- The working tree held the author's uncommitted notes: a to-do list for the future-features wiring at the end of `CLAIMS.md` (asking for C-013 to C-016), a "Parking Lot" section at the end of `ROADMAP.md` (reaction counts), and a parking lot in `FUTURE-FEATURES.md` (Community Gems). `FUTURE-FEATURES.md` had CRLF line endings.

**Evidence:** `git log`, `git diff`.

**Workaround:**
- The `CLAIMS.md` to-do note was replaced by C-013 to C-019, as the session prompt asked (it supersedes the note's C-013 to C-016).
- The reaction-count note moved from `ROADMAP.md` to the `FUTURE-FEATURES.md` parking lot, beside Community Gems.
- `FUTURE-FEATURES.md` was rewritten with LF endings.

**Consequence:** `CLAIMS.md` gains C-013 to C-019 (DEFERRED UNTIL STAGE 3 GATE); `FUTURE-FEATURES.md` v3, `SCOPE.md` v5, `ROADMAP.md` v5, README reading order.

**Follow-up:** `docs/BRAND.md` has the author's own uncommitted edits (the typeface lines, a trailing space); left as they are.

### 2026-10-07 23:20 - Shuffled labels disagree with hindsight more often

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** A2: summarize the 302 labels, the two post orders apart, and recompute the provisional accrual estimate and oracle ceiling.

**Expectation:** Figures close to the 150-label summary of 2026-10-04.

**Observation:**
- Consequential share: 84 of 302, 27.8% (Wilson 23.1% to 33.1%); publication order 39 of 150 (26.0%); shuffled 45 of 152 (29.6%, 22.9% to 37.3%). The 100-comment target binds across every interval: about 6 weeks at the mean rate, 14 at the median.
- Oracle ceiling of `pp-v0.1` on all 302: class defaults 57 collapsed (18.9%), with labeled flags 44 (14.6%), without any `REFERENCES_SPECIFIC_CLAIM` raises 49 (16.2%). 84 of 84 consequential surfaced under every ceiling.
- `REFERENCES_SPECIFIC_CLAIM`: 82 of 150 `tax-v0.1` labels, 18 of 152 `tax-v0.2` labels.
- Prospective against retrospective: publication order agrees on the consequential binary in 140 of 147 (4 consequential only prospectively); shuffled in 122 of 146, with 23 consequential only prospectively. Hindsight rarely raised a grade (4 in all).
- `replied_before_labeling`: 108 of 150 against 84 of 152.

**Evidence:** `afterword.label_records` (`summarize`, `oracle_ceiling`, `class_crosstab`, new `wilson`), counts only.

**Workaround:** None.

**Consequence:** `EVALUATION.md` v11 records the summary and both estimates as provisional; a dated C-010 entry records the agreement split. The shuffled labels differ from the earlier ones in sample, guide and taxonomy version, and labeler experience at once, so the change in hindsight agreement has no single cause on this evidence.

**Follow-up:** Recompute on the full `dev` set. The calibration pass on the first 150 would show whether the agreement difference is the labeler's or the sample's.

### 2026-10-07 23:30 - Post bodies were already in every full run since dev-probe-0.2

**Platform:** DEV

**Type:** DELIGHT

**Class:** PROJECT

**Task:** A3: show the post in the label UI, from the saved run.

**Expectation:** Possibly a probe change to capture post bodies.

**Observation:** Every full run from `dev-probe-0.2` on fetches each post singly, and those responses carry `body_html` (138 of 138 posts in `20261003T141450Z`, 140 of 140 in `20261007T224849Z`). Only the `dev-probe-0.1` runs lack them. No probe change was needed.

**Evidence:** `shapes.json` of each run (`article.paths.$.body_html.seen`).

**Workaround:** None needed.

**Consequence:** `afterword label-ui` gains a collapsible post panel (`p`): the post as plain text (the display rendering, scripts and styles dropped, links shown as text, never live), with a warning when the post was edited after the comment, and a message when the run has no body. Each batch record carries `post_panel`. The labeling guide becomes `lg-v0.4` (what the labeler may see changed; grades and definitions did not), and the field guide v2.

**Follow-up:** None.

### 2026-10-07 23:35 - The shell tool mangled escapes in an edit script again

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Apply code edits with short Python scripts.

**Expectation:** Backslash escapes in a quoted heredoc pass through unchanged.

**Observation:** One heredoc script wrote a regular expression with `\b` and `\1` turned into a backspace and a 0x01 control character; a later heredoc failed to parse at all (`unexpected EOF while looking for matching`), as in session 7.

**Evidence:** `cat -A` of the edited line; the shell tool error.

**Workaround:** Scripts written to the scratchpad with the file tool, and the control characters replaced from Python with `chr(92)`. Checked for control characters afterward: none.

**Consequence:** A few minutes. Session 7's workaround (scripts via the file tool) is the rule from here on.

**Follow-up:** None.

### 2026-10-07 23:50 - Checkpoint: Part A complete

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Close Part A: full check list, both logs, commit message.

**Expectation:** All checks green.

**Observation:** ruff, ruff format, mypy (strict), and pydoclint clean; 630 tests pass on Python 3.14 and on 3.12 (isolated), up from 625 (post panel, Wilson interval, the fourth oracle ceiling). The text scan of every changed file finds no em-dash, bidi control, or carriage return.

**Evidence:** The check list in CLAUDE.md.

**Workaround:** None.

**Consequence:** `commit-message.txt` holds the Part A message. Stopped for the author to commit, and to decide the placeholder question before ingest.

**Follow-up:** Part B after the commit.

## Session 8: Part B, first real data (2026-10-07)

### 2026-10-08 00:05 - DEV's comment schema changed without notice

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Decide how ingestion treats the two keys DEV added (Part A entry "The newest run is PARTIAL").

**Expectation:** A comment node's key set is stable between runs four days apart.

**Observation:** Between runs `20261003T141450Z` and `20261007T224849Z`, DEV extended `ai_disclosure_label` and `ai_disclosure_level` from 189 of 714 comment nodes (the newer comments only) to 750 of 750, deletion placeholder included. Nothing announced it, and the API version did not change. Every older comment's payload changed as a result: 524 comments (the 525 that lacked the keys, less the placeholder) stored a new source record with unchanged text.

**Evidence:** `probe-findings.json` (`comments.ai_disclosure`) and `shapes.json` of both runs; `afterword ingest` counts (`payload_changed 524`).

**Workaround:** The author's decision: amend ADR-009 so the placeholder is matched by its distinguishing features (`user` empty, the body replaced with the placeholder text, `id_code`, `created_at`, and `children` kept), ignoring an explicit allowlist of platform-wide keys, starting with these two, with this run as the evidence.

**Consequence:** Finding: DEV's comment schema can change without notice. Ingestion keeps treating unknown keys as signals, not errors: any key outside the known set and the allowlist still marks the node as an unexpected shape, records a sync limitation, and asks for a friction entry, and ingestion continues. Adding a key to the allowlist requires evidence recorded in this log. ADR-009 amended (status still provisional), DATA-MODEL v9, capability matrix v4; tests cover an allowlisted key, an unknown key, and an empty `user` without the placeholder body.

**Follow-up:** A payload hash that changes on every comment at once is the visible signature of such a change; worth watching for in later syncs.

### 2026-10-08 00:10 - The placeholder body text is matched by its features, not its value

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Implement "the body is replaced with the placeholder text" as part of the placeholder match.

**Expectation:** The placeholder text recorded somewhere it could be compared against.

**Observation:** The 2026-10-02 hand test recorded only its length (16 characters), and the real payloads are not to be opened. The adapter already has `placeholder_like` (a body of at most 60 characters, after tags, that mentions deletion, removal, or hiding), which both runs' comment indexes report as true for the placeholder, and false for every other node.

**Evidence:** `comment-index.json` of both runs (`placeholder_like`, keys, and field hashes only); `afterword.adapters.dev.records`.

**Workaround:** The placeholder match uses `placeholder_like` for the body feature. Counted with the amended rule: 1 placeholder and 0 unexpected shapes in each run.

**Consequence:** A placeholder whose text DEV rewords beyond those words would become an unexpected shape, which is the intended, visible failure.

**Follow-up:** None.

### 2026-10-08 00:20 - First real ingest: two runs, in order

**Platform:** DEV

**Type:** DELIGHT

**Class:** PROJECT

**Task:** B1: ingest `20261003T141450Z` then `20261007T224849Z` into the empty store; confirm lifecycle, placeholder, and purge behavior; ingest the second again.

**Expectation:** The lifecycle rules behave on real data as on synthetic fixtures.

**Observation:**
- First run: 713 new comments, 1 placeholder first seen. Limitations: 3 posts where `comments_count` is one higher than the live comments observed; earlier full runs also showed 3 such posts.
- Second run: 36 new, 524 payload changed with text unchanged, 190 unchanged. Edited 0, missing 0, deleted by absence 0. The placeholder was recognized again and stayed `DELETED_UPSTREAM`.
- Store: 140 posts; 458 live comments from others (the same count the labeling tools give as eligible), 291 by the author, 1 placeholder with authorship `UNKNOWN` and no text. Lifecycle events: 713 and 36 `first_observed`, 1 `source_placeholder`.
- Purge: no comment went from live to deleted, so the purge path did not run; the check finds 0 deleted comments holding text.
- Ingesting `20261007T224849Z` a second time was refused ("already ingested", exit 2) and left the store unchanged.

**Evidence:** `afterword ingest`, `afterword connections`, and the new `afterword store-status` (counts only).

**Workaround:** None needed. `store-status` was added so the lifecycle report comes from tested service code rather than an ad hoc query.

**Consequence:** Stage 1 gate evidence recorded in `ROADMAP.md`, with what it does not cover (a real edit, deletion by absence, other deletion paths). The gate decision is the author's.

**Follow-up:** A later probe run would exercise absence and edits on real data.

### 2026-10-08 00:35 - B1 collapses as much as the oracle, but surfaces far more

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** B2: score B1 (`hb-v0.1`) on `dev`, then tune its length threshold as `hb-v0.2`.

**Expectation:** A heuristic well below the oracle ceiling on review reduction.

**Observation:**
- `hb-v0.1` under `pp-v0.1`: 81 of 84 consequential surfaced, 44 of 302 collapsed (14.6%), the same reduction as the oracle with labeled class and flags. But 126 comments land at `SURFACE` against the oracle's 55: the lexicon rule calls 83 comments `CORRECTION`, of which 2 agree with the labels.
- All 3 misses are in the publication-order labels; shuffled labels: 45 of 45 surfaced.
- Tuning rule fixed before the sweep (largest reduction with no more than 3 misses; ties to the smaller threshold) chose 281: one more collapse, the same 3 misses. The threshold barely matters; the lexicon does.
- `pp-v0.2` changes nothing for B1, which sets no judgment flags. At the oracle, `pp-v0.2` collapses 51 of 302 instead of 44, with 84 of 84 still surfaced.

**Evidence:** `afterword evaluate` reports under `reports/eval/` (git-ignored, counts only); `afterword.service.tune_b1_threshold`.

**Workaround:** None.

**Consequence:** `EVALUATION.md` v12 records it as provisional tuning, not measurement. B1's weak point for the C-008 comparison is `SURFACE` size, not recall or reduction; a "worth seeing first" digest (spike insurance) would depend on exactly that.

**Follow-up:** Lexicon changes would be a new heuristic version, tuned on `dev`; not done this session.

### 2026-10-08 00:40 - pp-v0.2 and offline re-scoring

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** B3: a candidate `pp-v0.2` (model-set `REFERENCES_SPECIFIC_CLAIM` and `NEEDS_THREAD_CONTEXT` informational), comparable on any cached classification without rerunning a model.

**Expectation:** Re-scoring needs the stored priority assignments, which are written under `pp-v0.1` only.

**Observation:** The policy is pure and every classification records its full cache key, so scoring needs neither: each labeled comment's classification is found by its current input hash and the classifier's identity, and any policy version is applied in memory. A test confirms no model call happens while scoring or switching policy.

**Evidence:** `afterword evaluate`; `tests/test_evaluation.py`.

**Workaround:** None.

**Consequence:** `pp-v0.2` is in `policy.py` as a selectable version and documented in `PRIORITY-POLICY.md` as a candidate, not adopted; `classify` still applies `pp-v0.1`.

**Follow-up:** Score B2 under both once the author's model runs finish (Part C).

### 2026-10-08 00:45 - Miss lists, IDs only

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** B4: a local list of consequential comments a condition collapsed.

**Expectation:** None.

**Observation:** `afterword evaluate --misses` writes the IDs, one per line, to `reports/eval/` (git-ignored). For B1 the lists hold 3 IDs, the same 3 for `hb-v0.1` and `hb-v0.2`. Their text was not read. There is no read-only local view of single comments yet; the calibration pass with `--ids` shows them, but saving there writes a calibration label.

**Evidence:** The two miss files (IDs compared by set, not printed).

**Workaround:** None.

**Consequence:** The author reviews the misses locally.

**Follow-up:** A read-only "show these IDs" view in the label UI would make miss review safer; not built (scope).

### 2026-10-08 00:55 - Checkpoint: Part B complete

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Close Part B: full check list, both logs, commit message.

**Expectation:** All checks green.

**Observation:** ruff, ruff format, mypy (strict), and pydoclint clean; 643 tests pass on Python 3.14 and on 3.12 (isolated), up from 630 (placeholder matching, store status, scoring, `pp-v0.2`, heuristic versions, offline evaluation). The text and identity scans are clean. Part A was not yet committed, so `commit-message.txt` covers both parts.

**Evidence:** The check list in CLAUDE.md.

**Workaround:** None.

**Consequence:** Stopped for the author to commit before Part C. No model has classified a real comment.

**Follow-up:** Part C: the commands for the author's model runs.

## Session 8: decisions after Part B, and Part C1 (2026-10-08)

### 2026-10-08 01:10 - Recall and reduction miss what SURFACE holds

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** The author's reading of the B1 results, before preregistration: whether the primary measures can tell a useful "review first" tier from a noisy one.

**Expectation:** The primary measures (consequential recall, review reduction) separate a weak heuristic from the oracle ceiling.

**Observation:**
- B1 (`hb-v0.1`, `pp-v0.1`) matches the oracle on review reduction (44 of 302 collapsed, as with perfect classes and flags) and comes within 3 on recall (81 of 84 against 84 of 84).
- Its `SURFACE` tier holds 126 comments against the oracle's 55. SURFACE precision, the share of `SURFACE` comments graded 2 or 3: B1 50 of 126 (39.7%; Wilson 31.6% to 48.4%), oracle 30 of 55 (54.5%; 41.5% to 67.0%).
- The oracle's own precision is far from 100%, because every `TECHNICAL_QUESTION` defaults to `SURFACE` and 22 of the 46 labeled are graded 1. And B1 holds more consequential comments at `SURFACE` (50) than the oracle (30), because it surfaces more of everything, so precision alone would mislead too.

**Evidence:** `afterword evaluate` reports (counts only); `afterword.scoring` now reports `surface_precision` for every condition, and `oracle_ceiling` the same for the oracle.

**Workaround:** None.

**Consequence:** A proposal (`docs/proposals/2026-10-08-surface-co-primary.md`) would make SURFACE size and SURFACE precision co-primary with recall and reduction, each read against the oracle. Not applied until the author approves. A dated C-008 entry notes that on recall and reduction alone the room for B2 to beat B1 on `dev` is at most 3 consequential comments. C2 reports SURFACE size and precision for every condition, the author's instruction.

**Follow-up:** The author's decision on the proposal, before preregistration.

### 2026-10-08 01:15 - Decisions recorded: Stage 1 gate, ingestion rule, backlog

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Record the author's decisions after the Part B commit.

**Expectation:** None.

**Observation:**
- Stage 1 gate: passed, with a caveat. Repeatable sync and idempotent ingest are shown on two real runs; deletion behavior is known only for author self-deletion, so ADR-009 stays provisional. `ROADMAP.md` v6.
- CLAUDE.md: Claude may ingest saved probe runs into the local store when a session prompt asks; Claude never reads real comment text and reports counts and aggregates only. The dev subset selector, listed as out of scope "until labels exist", is now in scope.
- Backlog (`ROADMAP.md`, Stage 3a): a read-only viewer that opens the comments of an ID list in the label UI, with no labeling controls and no records written.

**Evidence:** `ROADMAP.md`, CLAUDE.md.

**Workaround:** None.

**Consequence:** None beyond the records.

**Follow-up:** None.

### 2026-10-08 01:25 - A fixed dev subset for the first real model runs

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** C1: a seeded, class-balanced subset of 40 to 60 labeled comments, so both models can be compared quickly before full passes.

**Expectation:** None.

**Observation:**
- Selection (`afterword dev-subset --size 50 --seed 20261008`): the labeled comments that are live in the store, grouped by analysis-label class; quotas filled evenly across classes, with classes smaller than their share giving all they have; within a class, sorted IDs shuffled by one `random.Random(20261008)` taken through the classes in taxonomy order. Deterministic for the same labels, store, size, and seed.
- Result: 50 comments. By class: `CORRECTION` 2, `CHALLENGE_OR_COUNTEREXAMPLE` 4, `TECHNICAL_QUESTION` 8, `OPPORTUNITY` 1, `DIRECT_QUESTION` 5, `TECHNICAL_EXTENSION` 8, `CONVERSATIONAL` 7, `LIGHTWEIGHT_ACKNOWLEDGMENT` 7, `LIKELY_SPAM_OR_NOISE` 7, `UNCERTAIN` 1. Graded 2 or 3: 16. Post order: 25 publication order, 25 shuffled.
- The ID list is git-ignored (`reports/eval/dev-subset-s20261008-n50.txt`).

**Evidence:** `afterword dev-subset` output (counts only).

**Workaround:** None.

**Consequence:** The subset is class-balanced, not natural-rate, so its recall and reduction are not estimates of the full set's: it is for comparing the two models' behavior and speed, and for catching problems before the overnight passes. `classify` and `evaluate` take `--ids`.

**Follow-up:** The author runs both models on it, then the full passes (Part C1 commands).

## Session 8: subset runs, before the overnight passes (2026-10-08)

### 2026-10-08 02:20 - input_too_long came from the guard's margin, not the context

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Explain the 2 `failed:input_too_long` outcomes, which were the same 2 comments for both models on the 50-comment subset, and fit the full model input without truncating comment text.

**Expectation:** Real comments fit the 2048-token context, as every synthetic case did.

**Observation:**
- Full model input (system prompt, 2,469 characters, plus the rendered title, parent, and comment) across all 458 stored comments from others: median 3,438 characters, p90 4,259, p99 5,407, max 5,953.
- Tokens are estimated, not counted: no tokenizer runs offline, and calling Ollama on real comments is the author's to do. At the guard's conservative 3 characters per token, the longest is about 1,984 tokens; at the 4.4 measured on the synthetic sets, about 1,353. Inputs over 2048 tokens: 0 at either estimate; over 4096 and over 8192: 0.
- The guard refuses any input over (2048 - 200) x 3 = 5,544 characters, which 3 of the 458 exceed, including the 2 in the subset. Ollama itself would probably have fit them; the guard exists so nothing is ever silently cut.

**Evidence:** `afterword.service._subjects` and `classifier.render_user` over the store, lengths only.

**Workaround:** `num_ctx` raised to 4096 (`ollama.NUM_CTX`): at the conservative estimate, the guard now admits about 11,688 characters, about twice the longest input. No comment text is truncated.

**Consequence:**
- The generation options are now part of the cache key: `model_options`, such as `num_ctx=4096;num_predict=200;seed=20261003;temperature=0`. Store schema 2 adds the column, and the migration records the options earlier Ollama rows ran with (2048). `evaluate --num-ctx 2048` scores those earlier runs. DATA-MODEL v10, PRIVACY-AND-BOUNDARIES v5 (path A's context size; nothing else changes), EVALUATION v13 (versioning).
- Run time: the context size changes memory, not the work per token, which is set by the input length. The subset took about 30 s per comment sent for qwen and 44 s for llama (more than the synthetic 23 and 26, since real inputs are longer). The new key means the full pass reclassifies all 458, the subset included: about 5.6 hours for llama, 3.8 for qwen. The 3 long inputs add a few minutes, and Ollama reloads the model once for the new context size.
- Synthetic benchmarks now also run at 4096, so a future benchmark is not like for like with the 2026-10-03 and 2026-10-04 runs on this option.

**Follow-up:** Record measured input tokens per classification (Ollama returns them), so the next estimate is a count; not done this session.

### 2026-10-08 02:30 - First model runs on real comments: the 50-comment subset

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Score both models on the subset against the author's labels, under `pp-v0.1` and `pp-v0.2`, beside B1 and the oracle on the same 50.

**Expectation:** None fixed. The subset is class-balanced, so its tier shares are not natural rates.

**Observation (all 50; the 2 failed comments count as `SURFACE`, as the policy assigns them):**

| Condition | Outcomes | Consequential surfaced | Collapsed | SURFACE | SURFACE precision | SURFACE capture | Flag-caused raises (graded 0 or 1) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B1 `hb-v0.2`, either policy | 50 OK | 14 of 16 | 11 | 23 | 10 of 23 | 10 of 16 | 0 |
| qwen, `pp-v0.1` | 45 OK, 3 malformed, 2 failed | 16 of 16 | 0 | 30 | 9 of 30 | 9 of 16 | 8 (8) |
| qwen, `pp-v0.2` | same | 16 of 16 | 3 | 30 | 9 of 30 | 9 of 16 | 5 (5) |
| llama, `pp-v0.1` | 48 OK, 2 failed | 16 of 16 | 4 | 23 | 9 of 23 | 9 of 16 | 3 (3) |
| llama, `pp-v0.2` | same | 16 of 16 | 7 | 23 | 9 of 23 | 9 of 16 | 0 |
| Oracle, class and flags, `pp-v0.1` | | 16 of 16 | 10 | 16 | 10 of 16 | 10 of 16 | |
| Oracle, class and flags, `pp-v0.2` | | 16 of 16 | 11 | 16 | 10 of 16 | 10 of 16 | |

- Excluding the 2 comments both models failed (48 left, still 16 consequential): B1 collapses 11 with SURFACE 21 (10 of 21); qwen 0 and 3 collapsed, SURFACE 28 (9 of 28); llama 4 and 7, SURFACE 21 (9 of 21); oracle 10 (`pp-v0.1`) and 11 (`pp-v0.2`), SURFACE 15.
- Model flag precision against the labels (set, agreeing): qwen `REFERENCES_SPECIFIC_CLAIM` 35, 13; `NEEDS_THREAD_CONTEXT` 20, 3; `ADDRESSED_TO_OTHER_COMMENTER` 15, 0; `POSSIBLE_INSTRUCTION_TEXT` 5, 0; `HOSTILE_TONE` 4, 1. llama `REFERENCES_SPECIFIC_CLAIM` 26, 11; `NEEDS_THREAD_CONTEXT` 29, 7; `HOSTILE_TONE` 1, 0. Every flag-caused raise was of a comment graded 0 or 1.
- Both models surface every consequential comment on the subset; B1 misses 2. Neither model puts more consequential comments at `SURFACE` than B1 (9 against 10).

**Evidence:** `afterword.service.evaluate_condition` with `--ids` and `--num-ctx 2048` (counts only); git-ignored `reports/eval/subset-preview.json`.

**Workaround:** None.

**Consequence:** Informational; 50 class-balanced comments decide nothing. `pp-v0.2` removed every flag-caused raise for llama, costing no consequential comment here.

**Follow-up:** The full llama pass, then the C2 write-up.

### 2026-10-08 02:35 - Qwen on the subset: informational

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record qwen's subset result, as the author asked.

**Expectation:** None.

**Observation:** Qwen (`qwen3:4b-instruct-2507-q4_K_M`, 2048 context) collapsed 0 of 50 under `pp-v0.1`, with 3 malformed outputs (`duplicate_flag`) and 2 failed (`input_too_long`). That matches the synthetic benchmark under `pr-v0.2` (0 of 59 collapsed, `duplicate_flag` 3 of 59): it sets judgment flags on most comments, and `ADDRESSED_TO_OTHER_COMMENTER` 15 times with no label agreeing.

**Evidence:** The author's run output; the scores above.

**Workaround:** None.

**Consequence:** Qwen's full pass is optional, as a secondary comparison only (`EVALUATION.md`, "Which model is B2").

**Follow-up:** The author decides whether to run it.

### 2026-10-08 02:40 - SURFACE measures accepted; class is a weak proxy for consequence

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Apply the author's decisions on the SURFACE proposal and the class-to-tier finding.

**Expectation:** None.

**Observation:**
- Proposal accepted with one addition, SURFACE capture (the share of consequential comments at `SURFACE`): on 302 labels the oracle gives 30 of 84, B1 50 of 84. Moved to `docs/proposals/accepted/`; `EVALUATION.md` v13 makes SURFACE size, precision, and capture co-primary with recall and reduction.
- Finding: under `pp-v0.1` even perfect classification places 54 of 84 consequential comments at `QUEUE`. Consequential comments are mostly `TECHNICAL_EXTENSION` (49) and `CONVERSATIONAL` (4), which default to `QUEUE`, while `TECHNICAL_QUESTION` defaults to `SURFACE` although 22 of its 46 labeled comments are graded 1. Class is a weak proxy for consequence.

**Evidence:** `EVALUATION.md` (label summary, oracle ceiling); `afterword evaluate` reports.

**Workaround:** None. The policy is unchanged.

**Consequence:** Dated entries on C-001, C-002, and C-008. "How should consequence reach the tier?" is recorded in `EVALUATION.md` as the open design question for session 9, with its tension with ADR-007: a model-reported importance would bring back model-chosen priority and the manipulation risk ADR-007 and ADR-008 removed.

**Follow-up:** Session 9.

## Session 8: Part C2, dev-set evaluation and small items (2026-10-08)

Times are UTC. No comment text, names, or handles: every figure below is a count, computed by code that printed aggregates only.

### 2026-10-08 13:20 - Orientation for C2, at the source

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Orientation: check labels, timing records, the store, and stored classifications directly.

**Expectation:** 302 labels; 458 Llama classifications at a 4096-token context, all `OK`; Part C1's tail uncommitted.

**Observation:**
- Labels: 302 initial, 0 calibration, 0 self-agreement; 150 publication order, 152 shuffled (seed 20261004); all from run `20261003T141450Z`. Timing: 2 valid records.
- Store: 458 live comments from others, 291 by the author, 1 placeholder. Classifications: B1 `hb-v0.1` and `hb-v0.2` 458 each; Llama at `num_ctx=4096` 458 `OK`; Llama at 2048 48 `OK` and 2 `FAILED` (the subset); qwen at 2048 45 `OK`, 3 `MALFORMED`, 2 `FAILED`. Every cached input hash matches the current input.
- Uncommitted: the C1 tail (context size 4096, `model_options` in the cache key, store schema 2, SURFACE capture, the accepted proposal's move, and their docs). Check list green: 646 tests on 3.14 and on 3.12 (isolated).
- `CLAIMS.md` still ends with the author's to-do note "Future features (docs only, no code)", which Part A's entry says was replaced by C-013 to C-019. The claims were added; the note itself is still in the committed file.

**Evidence:** `afterword store-status`; `afterword.label_records` and `afterword.timing.load_valid` (counts only); a counts-only pass over the store's cache keys.

**Workaround:** None. The note was left in place, and C-020 was inserted before it so the claims stay in sequence.

**Consequence:** The author's figures match the records.

**Follow-up:** The author decides whether to delete the stale to-do note.

### 2026-10-08 13:50 - The pre-check fired on 3 of 458 real comments

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** C2.1: count which rule decided each tier, and whether ordinary comments about prompts and models trip `pc-v0.1` on posts that are largely about AI.

**Expectation:** Possibly many false positives, since the author writes about AI.

**Observation:**
- `pc-v0.1` fired on 3 of 458 comments from others: rule `system_prompt` 2, `taxonomy_name` 1. 2 are labeled, graded 0 and 1; none consequential.
- The pre-check alone raised 1 comment to `SURFACE` under B1 and 2 under Llama; its other firings were on comments already at `SURFACE` by class.
- Llama set `POSSIBLE_INSTRUCTION_TEXT` itself on 7 other comments (3 labeled, none consequential): the model is the larger source of instruction flags.
- Decided-by counts mislead on their own: an override is recorded as `rule_applied` whenever it reaches the final tier, even when the class default gives the same tier. The raises were counted separately.

**Evidence:** `afterword dev-analysis` (`afterword.service.analyze_dev`), report in `reports/eval/` (git-ignored, counts only).

**Workaround:** None.

**Consequence:** The hypothesis holds in kind (the `system_prompt` rule matches ordinary AI discussion) but costs at most 2 `SURFACE` places of 458. Recorded in the dev-set evaluation, section 1.

**Follow-up:** None.

### 2026-10-08 13:55 - Llama's SURFACE inflation is class assignment, mostly "challenge"

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** C2.2: Llama's predicted class against the labels, to see whether its large `SURFACE` comes from classes or overrides.

**Expectation:** Unknown; on the 50-comment subset Llama's `SURFACE` matched B1's.

**Observation:**
- Class agreement: 84 of 302 (B1: 77).
- Llama predicts `CHALLENGE_OR_COUNTEREXAMPLE` for 96 labeled comments, 4 of them labeled so: 49 are labeled `TECHNICAL_EXTENSION`, 23 `CONVERSATIONAL`, 16 `TECHNICAL_QUESTION`. 137 of its 142 labeled `SURFACE` comments are there by class default; the other 5 by `POSSIBLE_INSTRUCTION_TEXT`, none consequential.
- The same error lifts capture: of Llama's 55 consequential comments at `SURFACE`, 41 were predicted challenge. Of the 49 labeled extensions it called a challenge, 28 are graded 2 or 3, against 21 of the other 51 labeled extensions.
- It predicts 26 acknowledgments and 8 spam against 40 and 17 labeled, which is where review reduction goes.

**Evidence:** `afterword dev-analysis` (confusion matrix, counts only).

**Workaround:** None.

**Consequence:** Recorded in the dev-set evaluation, section 2. The extension-called-challenge cell is an input to session 9's question (how consequence reaches the tier), not evidence for a design.

**Follow-up:** Session 9.

### 2026-10-08 14:00 - No condition is near the oracle on all five measures

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** C2.3: the five primary measures for B1 `hb-v0.2` and Llama under `pp-v0.1` and `pp-v0.2`, beside the oracle.

**Expectation:** None fixed.

**Observation:**
- B1: recall 81 of 84, collapsed 45, SURFACE 126, precision 50 of 126, capture 50 of 84 (either policy).
- Llama `pp-v0.1`: 84 of 84, 17, 142, 55 of 142, 55 of 84. `pp-v0.2`: 25 collapsed, the rest unchanged; its 8 extra collapses are all graded below 2.
- Oracle `pp-v0.1`: 84 of 84, 44, 55, 30 of 55, 30 of 84 (`pp-v0.2`: 51 collapsed).
- Capture above the oracle's comes with a `SURFACE` more than twice the oracle's size, so it is not better classification.

**Evidence:** `afterword evaluate` reports (`reports/eval/`, counts only); the miss lists for Llama are empty under both policies.

**Workaround:** None.

**Consequence:** `docs/benchmarks/2026-10-08-dev-set-evaluation.md`, with the caveats first; `EVALUATION.md` v14; a dated C-008 entry. Nothing chosen.

**Follow-up:** The B2 and policy choices, before preregistration.

### 2026-10-08 14:00 - pc-v0.1 is English-only

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** C2.6: record the known language gap of the deterministic pre-check.

**Expectation:** Already known from the synthetic set.

**Observation:** Every `pc-v0.1` pattern is English, so instruction-like text in another language bypasses the check. `adv-110` (a Spanish instruction to call the comment thanks) is the known case: in the 2026-10-03 synthetic benchmark neither model flagged it, and it reached `QUEUE` or `COLLAPSED`. On `dev`, the 2 comments detected as non-English did not trip the check.

**Evidence:** `src/afterword/precheck.py`; `fixtures/corpus/adversarial.jsonl` (`adv-110`, `expect_precheck: false`); `docs/benchmarks/2026-10-03-synthetic-local-models.md`.

**Workaround:** None. Recorded in `EVALUATION.md` v14.

**Consequence:** A gap in ADR-008's defence, not a change to it. Extending the check is proposed in `FUTURE-FEATURES.md` ("Multilingual comments").

**Follow-up:** A new pre-check version for the languages actually observed, after the Stage 3 gate.

### 2026-10-08 14:00 - Language detection: a dependency, two guardrails, counts only

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** C2.6: count stored comments from others by detected language with a local, deterministic detector.

**Expectation:** A new dependency needs the author's approval.

**Observation:**
- The author chose `py3langid` (0.4.0) as an analysis dependency group only, with two guardrails: under 40 characters of prose is "too short to classify"; a normalized confidence under a stated threshold is "uncertain". The threshold, 0.80, was set on six synthetic sentences before any real comment was counted (a Spanish sentence scored 0.898, so 0.90 would have called it uncertain).
- Detection runs on normalized prose with code and link targets removed. Result: 435 English, 2 non-English (both detected as Vietnamese, neither labeled; Llama put both at `SURFACE`), 5 uncertain (3 labeled, all spam, grade 0), 16 too short (9 labeled, all grade 0).
- `uv run` syncs the analysis group by default (`[tool.uv] default-groups`), so the check list and the isolated 3.12 run both have it; it is not a runtime dependency.

**Evidence:** `afterword dev-analysis` (language section, counts only); `src/afterword/language.py`; `pyproject.toml`.

**Workaround:** None.

**Consequence:** If language detection later becomes a runtime structural field, the detector is chosen again then; `lingua` is the stronger candidate for short texts. Recorded in `FUTURE-FEATURES.md`.

**Follow-up:** None now.

### 2026-10-08 14:00 - What DEV says the AI-disclosure fields mean

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Report `ai_disclosure_label` and `ai_disclosure_level` across stored comments, cross-tabulated with the labels, and record what DEV documents about them.

**Expectation:** Undocumented fields (capability matrix, 2026-10-02).

**Observation:**
- Values: one pair only, `Not Disclosed` / `not_disclosed`, on 750 of 750 nodes in the run behind every stored comment. All 302 labeled comments have it, so the cross-tab with class and grade is the label distribution itself.
- DEV's announcement of AI disclosure describes author self-disclosure on posts (Hand Written, AI-Assisted, Fully Autonomous), chosen from a dropdown, with no detection described. Forem's OpenAPI description gives article values `not_disclosed`, `no_ai`, `some_ai`, `fully_autonomous`. Forem pull request #23895, merged 2026-10-05, made the v1 comments API emit both fields, which the v0 serializer and the schema already had. Afterword requests v1, and the merge falls between the two runs, which fits the jump from 189 to 750 nodes; why 189 had the keys before is not explained.
- How a commenter sets a comment's disclosure is not documented anywhere found.

**Evidence:** `probe-findings.json` of both runs (`comments.ai_disclosure`); the DEV announcement post; `forem/forem` `swagger/v1/api_v1.json`; `forem/forem` pull request #23895.

**Workaround:** None.

**Consequence:** Session 8 Part B's "schema changed without notice" now has a likely cause: an upstream change to the v1 comment template, public but unannounced to API users. Capability matrix v5; a proposal for a structural, informational `AI_AUTHORSHIP_DISCLOSED` flag (`docs/proposals/2026-10-08-ai-authorship-disclosed-flag.md`, not accepted); `PRIVACY-AND-BOUNDARIES.md` v6 adds the rule that AI authorship is never inferred from writing style; a parking-lot note on counting human and disclosed-AI comments separately.

**Follow-up:** The author's decision on the flag. Watching Forem's repository is a cheap early warning for payload changes.

### 2026-10-08 14:05 - The classify progress line counted comments as articles

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** C2.5: fix the `classify` progress label.

**Expectation:** None.

**Observation:** The status line was written for the probe and always said "article N of M"; `classify` passes comments through the same step.

**Evidence:** `src/afterword/progress.py`.

**Workaround:** The unit now depends on the step: "comment N of M (classify)", "article" for the probe. A test covers it.

**Consequence:** None beyond the fix.

**Follow-up:** None.

### 2026-10-08 14:05 - read_via_translation: which key, and where in the terminal

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** C2.6: add `read_via_translation` to the label schema and both tools.

**Expectation:** A free key in the label UI and one more terminal prompt.

**Observation:**
- `l` was free, but it was `CONTAINS_LINK`'s key before `tax-v0.2`; a labeler's old habit would set the new field silently. `v` was used instead.
- A new terminal prompt would shift every scripted answer sequence in the labeling tests (about 70) and lengthen every label. The field is set at the existing `Save?` prompt instead: `v` saves with `read_via_translation: true`; Enter still saves with `false`.
- Labels made before the field existed lack it; analysis treats a missing value as "not recorded", never as `false`.

**Evidence:** `src/afterword/labeling.py`, `label_ui.py`, `label_ui_page.py`; tests in `test_labeling.py` and `test_label_ui.py`.

**Workaround:** None needed.

**Consequence:** `lg-v0.5` (what is recorded changed; grades did not), field guide v3, `DATA-MODEL` v11, `fixtures/README.md`, `WORKFLOW.md` shortcuts.

**Follow-up:** None.

### 2026-10-08 14:05 - The shell tool broke a heredoc again

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Insert the analysis functions into `service.py` with a Python script.

**Expectation:** Session 8 Part A's rule (scripts through the file tool) would prevent this.

**Observation:** A script passed through a bash heredoc inside a longer command failed with "unexpected EOF while looking for matching" quote. The rule was not followed for that one script.

**Evidence:** The shell tool error.

**Workaround:** The script and the inserted block were written to the scratchpad with the file tool and run from there.

**Consequence:** A few minutes.

**Follow-up:** None; the rule stands.

### 2026-10-08 14:15 - Checkpoint: Part C2 complete

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Close Part C2: full check list, both logs, commit message.

**Expectation:** All checks green.

**Observation:** ruff, ruff format, mypy (strict), and pydoclint clean; 658 tests pass on Python 3.14 and on 3.12 (isolated), up from 646 (dev analysis, language detection, the progress unit, `read_via_translation`). The identity scan finds no disallowed match, and a scan of every changed and new file finds no em-dash, bidi control, or carriage return.

**Evidence:** The check list in CLAUDE.md.

**Workaround:** None.

**Consequence:** `commit-message.txt` covers the uncommitted C1 tail and C2. Not committed.

**Follow-up:** The author commits.

### 2026-10-08 - Session summary (session 8, Parts A to C2)

**Goal:** Label summary and post panel (A); first real data and offline scoring (B); decisions, a dev subset, and the first model runs on real comments (C1); score and write the dev-set evaluation, plus small items (C2).

**Completed:**
- A: label summary for 302 labels and the provisional accrual estimate; the label UI's post panel (`lg-v0.4`).
- B: ADR-009 amended for platform-wide keys; both real runs ingested; B1 scored on `dev`; `pp-v0.2` as a candidate; offline re-scoring.
- C1: SURFACE size, precision, and capture made co-primary; class-as-proxy finding; a seeded 50-comment subset; the context size raised to 4096 with options in the cache key.
- C2: tier causes, pre-check firings, class confusion, and the five measures for B1 and Llama under both policies (`docs/benchmarks/2026-10-08-dev-set-evaluation.md`); a counts-only language measurement; AI-disclosure values and documentation; the progress label; `read_via_translation` (`lg-v0.5`); the multilingual future feature and C-020; the AI-authorship proposal and privacy rule.

**Friction discovered:** DEV changed the comment payload without notice (now traced to a merged Forem change); the guard's margin refused 3 long inputs at 2048 tokens; heredocs in the shell tool; the classify progress label.

**Delight discovered:** offline re-scoring of any cached run under any policy; the pre-check is quiet on real comments (3 of 458).

**Claims affected:** C-001, C-002, C-008 (dated entries, provisional, from `dev`); C-010 (the post-order split); C-020 added, DEFERRED UNTIL STAGE 3 GATE.

**ADRs affected:** ADR-009 amended (platform-wide key allowlist). ADR-007 and ADR-008 unchanged; the pre-check's English-only gap is recorded against ADR-008.

**Scope pressure:**
- A `dev-analysis` command was added rather than an ad hoc script, so the counts come from tested service code (ADR-012). Kept to counts only.
- Language detection stayed an analysis aid: no stored field, no policy input, analysis dependency group only.
- `AI_AUTHORSHIP_DISCLOSED` was written as a proposal, not implemented: a new flag is a taxonomy change and needs the author's approval.
- Translation and the multilingual pre-check stayed in `FUTURE-FEATURES.md`, gated on Stage 3.
- Choosing B2 or a policy: not done, as agreed.

**Next smallest useful step:** Session 9: how consequence should reach the tier, weighed against ADR-007, using section 2's evidence; then the B2 and policy choices before preregistration. The author: finish labeling `dev` (156 left) and decide on the AI-authorship proposal.

## Session 8: decisions after Part C2 (2026-10-08)

### 2026-10-08 14:40 - AI-authorship proposal accepted, amended: a label field, not a flag

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Apply the author's decision on the `AI_AUTHORSHIP_DISCLOSED` proposal.

**Expectation:** A structural flag from the platform's disclosure fields.

**Observation:** DEV's disclosure fields describe posts, and every stored comment reads `not_disclosed`, so a structural flag would have no source. The author's amendment:
- `ai_self_disclosed` (boolean) on the label record, set by the labeler in either tool only when a comment says explicitly that an AI wrote it (`a` in the label UI; `a`, or `va` with a translation, at the terminal's `Save?` prompt). Not a taxonomy flag, no tier effect.
- Automated detection is deferred, including detection of explicit self-disclosure text. The never-infer rule stands.
- The platform fields stay wired as a dormant source: the DEV adapter maps `ai_disclosure_level` to a source-neutral `platform_ai_disclosure` on each observed comment, with `UNEXPECTED` for an undocumented value. Nothing stores, shows, or uses it.

**Evidence:** `docs/proposals/accepted/2026-10-08-ai-authorship-disclosed-flag.md` (amendment at the top, the original kept below); tests in `test_records.py`, `test_labeling.py`, `test_label_ui.py`.

**Workaround:** None.

**Consequence:** `lg-v0.6`, field guide v4, `PRIVACY-AND-BOUNDARIES.md` v7, `DATA-MODEL` v12, `fixtures/README.md`, `WORKFLOW.md`. The proposal moved to `docs/proposals/accepted/`; the friction entries above that name its earlier path are left as recorded.

**Follow-up:** Revisit the structural flag if a platform starts returning disclosure values other than `not_disclosed` for comments.

### 2026-10-08 14:40 - The pre-check hypothesis is refuted

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Record the outcome of the author's hypothesis that comments about prompts and models trip `pc-v0.1` and inflate `SURFACE`.

**Expectation:** The hypothesis, stated before C2.

**Observation:** `pc-v0.1` fired on 3 of 458 real comments; on its own it raised at most 2 to `SURFACE`. `SURFACE` inflation comes from class assignment: 137 of Llama's 142 labeled `SURFACE` comments are there by class default, and 124 of B1's 126.

**Evidence:** The 13:50 and 13:55 entries above; `docs/benchmarks/2026-10-08-dev-set-evaluation.md`, sections 1 and 2.

**Workaround:** None.

**Consequence:** Recorded as refuted in `EVALUATION.md` v15.

**Follow-up:** None.

### 2026-10-08 14:45 - Session 9 input: TECHNICAL_EXTENSION may mix substantive and passing comments

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Record the extension-called-challenge observation for the session 9 design question.

**Expectation:** None.

**Observation:** Of 100 labeled extensions, the 49 Llama called a challenge hold 28 consequential (57%; Wilson 43.3% to 70.0%), the other 51 hold 21 (41%; 28.8% to 54.8%). The intervals overlap.

**Evidence:** `afterword dev-analysis` (counts only).

**Workaround:** None.

**Consequence:** `EVALUATION.md` v15 records it as an observation, with the directions it points at (a split of `TECHNICAL_EXTENSION`, or an auditable "pushes on a claim" signal) and why it is not evidence for a design.

**Follow-up:** Session 9.

### 2026-10-08 14:45 - The stale to-do note in CLAIMS.md is gone

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Delete the author's old "Future features (docs only, no code)" note at the end of `CLAIMS.md`, as the author asked.

**Expectation:** A note, not a claim.

**Observation:** The block held no claim heading; it was removed whole. C-001 to C-020 are unchanged.

**Evidence:** `git diff docs/CLAIMS.md`.

**Workaround:** None.

**Consequence:** None beyond the file.

**Follow-up:** None.

### 2026-10-08 14:50 - Checkpoint: decisions applied

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Close the round: full check list, both logs, commit message.

**Expectation:** All checks green.

**Observation:** ruff, ruff format, mypy (strict), and pydoclint clean; 662 tests pass on Python 3.14 and on 3.12 (isolated), up from 658 (the dormant disclosure mapping, `ai_self_disclosed` in both tools). Identity scan: no disallowed match; no em-dash, bidi control, or carriage return in any changed file. Moving the proposal with `git mv` staged the rename; it was unstaged, so the index matches HEAD and the move shows as a delete plus a new file.

**Evidence:** The check list in CLAUDE.md.

**Workaround:** None.

**Consequence:** `commit-message.txt` holds this round's message. Not committed.

**Follow-up:** The author commits.

### 2026-10-08 - Session summary addendum (decisions after Part C2)

**Completed:** the AI-authorship proposal accepted as amended (`ai_self_disclosed` label field in both tools, platform fields as a dormant source, automated detection deferred); the pre-check hypothesis recorded as refuted; the session 9 observation on `TECHNICAL_EXTENSION`; the stale `CLAIMS.md` note deleted.

**Claims affected:** none (C-020 unchanged).

**ADRs affected:** none.

**Scope pressure:** the dormant platform mapping is code, but it stays on the observation only: not stored, shown, or used, as the author asked. No detection of self-disclosure text was written.

**Next smallest useful step:** unchanged: session 9, how consequence reaches the tier.
