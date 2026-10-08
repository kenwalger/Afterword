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
