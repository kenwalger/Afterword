# Friction log: session 15

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 15: calibration result, Part 1 figures, the preregistration session up to the author's decisions (2026-10-26)

All numbers come from `afterword evaluate` and scratch scripts over `afterword.label_records` and the service layer's cached classifications, printing counts only. No comment text, reason, note, or ID was printed or read. No model ran. Nothing under `fixtures/labels/`, `reports/timing/`, `data/`, or the saved runs was opened directly.

### 2026-10-26 21:50 - The calibration pass moved labels up, the reverse of the self-agreement check

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Compare the 150 calibration labels (`lg-v0.7`) with their originals (`lg-v0.2`).

**Expectation:** After the self-agreement check (31 of 112 left consequential, 1 entered), a relabel under a guide with a stricter test for grade 2 ("name the consequence") would move the first 150 down, or leave them about where they were.

**Observation:** 30 entered consequential and 11 left it; the 150 hold 58 consequential labels against 39. Grade 3 went from 5 to 23. Class changed on 75 (kappa 0.392); `TECHNICAL_EXTENSION` fell from 49 to 16, toward `CONVERSATIONAL` (15) and toward the `SURFACE` classes (`CHALLENGE_OR_COUNTEREXAMPLE` 8, `TECHNICAL_QUESTION` 7). The two results do not contradict each other: the self-agreement draw took every originally consequential comment and few others, so it could only see downgrades. On the 50 comments in both, the three readings give 39, 26, and 30 consequential. The other 100, all originally graded 0 or 1 and never drawn, gained 28. The move is not in the fast sittings: conditioned on the original grade, the 2026-10-23 sittings (median 21 to 24 seconds per comment) raised 19 of 66 and the 2026-10-26 sittings (33 to 38 seconds) raised 11 of 45.

**Evidence:** `afterword.label_records.calibration_differences`; grade and class transitions and per-batch counts in `EVALUATION.md` v21.

**Workaround:** None needed.

**Consequence:** The consequential share now depends on the guide version: 38.7% of the 150 under `lg-v0.7` against 25.6% to 29.1% in the older shuffled labels. `dev` mixes three guides. Every oracle-relative number moved (below).

**Follow-up:** Thresholds: decide whether they are relative to the test set's own oracle (same guide) or fixed from `dev` (`docs/proposals/accepted/2026-10-26-registered-thresholds.md`, Decision 1).

### 2026-10-26 21:55 - The oracle collapses a consequential comment

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Recompute the oracle ceiling under `pp-v0.2` on all 494 labels.

**Expectation:** As on every earlier label set, perfect classification surfaces every consequential comment.

**Observation:** 157 of 158. One calibration label is `LIGHTWEIGHT_ACKNOWLEDGMENT` graded 2; that class defaults to `COLLAPSED`. Llama's single miss and B1's three are different comments from it and from each other.

**Evidence:** `afterword.label_records.oracle_ceiling`, `consequential_by_tier`.

**Workaround:** None. A "no consequential miss" threshold would now fail even perfect classification; the draft recall threshold counts misses instead.

**Consequence:** Recall is no longer "free" at the ceiling. It is one comment, but it is the first label that says the class can hide a consequence even when the class is right.

### 2026-10-26 22:05 - The relabel moved the ceiling more than it moved either classifier

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Recompute B1, Llama, and the oracle under `pp-v0.2`.

**Expectation:** Labels change; classifier scores and the oracle change by similar amounts.

**Observation:** B1 and Llama collapse exactly what they did (79 and 39; the classifiers did not change, none of the 17 new comments was collapsed). The oracle's collapses rose from 103 to 118 and its `SURFACE` from 84 to 110, with precision 88 of 110 and capture 88 of 158. Ratios to the oracle on all 494: review reduction 0.67 (B1) and 0.33 (Llama); `SURFACE` size 1.91 and 2.08.

**Evidence:** `reports/eval/20261026T214645Z-b1-hb-v0.2-pp-v0.2.json`, `reports/eval/20261026T214646Z-b2-llama3.1_8b-instruct-q4_K_M-pp-v0.2.json` (git-ignored).

**Workaround:** None.

**Consequence:** "Relative to the oracle" depends on which labels the oracle is computed from. This is why the draft recommends the test set's own oracle.

### 2026-10-26 22:20 - The preregistration record is not drafted in `registry/`

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Step 4, item 3: draft `registry/preregistration.json` with `registered_at` left for the author.

**Expectation:** Write the file with a placeholder time.

**Observation:** Every tool reads the record as soon as the file exists (`afterword.preregistration.load`). A placeholder time does not parse, so `label`, `label-ui`, `classify`, and the corpus export would refuse to run; a plausible time would start assigning later comments to `test` or to neither set.

**Evidence:** `src/afterword/preregistration.py`, `load` and `parse`.

**Workaround:** The draft record is in the proposal, as JSON, and is written to `registry/` when the author gives `registered_at`.

**Consequence:** None, if the runbook's order holds. `PREREGISTRATION.md` says "draft registry/preregistration.json"; the wording could say "draft the record" instead.

### 2026-10-26 22:30 - Part 1's own comments would join `dev`

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** List the posts about Afterword by ID for the registered rules.

**Expectation:** Part 1 is listed, or known to be irrelevant.

**Observation:** Part 1 is not in run `20261026T181641Z` (scheduled 2026-10-27). Published before `registered_at`, it is not a test post (ADR-010). But its comments that arrive before `registered_at` are `dev` comments by ADR-010's decision 1, and join the frozen `dev` corpus, although ADR-010's reason for excluding Afterword posts applies to them too.

**Evidence:** ADR-010, decisions 1 to 3; `afterword.preregistration.corpus_set_of`.

**Workaround:** None. Raised as a question for the author; excluding them from `dev` would need an amendment to ADR-010.

**Consequence:** Open, for the author.

### 2026-10-26 22:35 - Public figures now disagree with the article's

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Prepare the Part 1 figures.

**Expectation:** The article, the README, and the 2026-10-08 write-up quote the same numbers.

**Observation:** The README ("What it has found so far") and the 2026-10-08 write-up quote the 478-label figures (129 consequential; B1 125 of 129; the oracle's `SURFACE` about 18%). After the calibration pass the figures are 494 labels, 158 consequential, B1 155 of 158, Llama 157 of 158, oracle `SURFACE` 22.3%.

**Evidence:** `README.md`; `docs/benchmarks/2026-10-08-dev-set-evaluation.md`; `EVALUATION.md` v21.

**Workaround:** None this session. The write-up is a dated record and stays as written; the README is the author's call.

**Consequence:** Open: update the README before or with Part 1.

## Session summary

**Goal:** The calibration result; the Part 1 figures on the full current `dev` set; the preregistration session (`PREREGISTRATION.md`, Step 4) up to the author's decisions on the thresholds.

**Completed:**

- Calibration result, counts only (`EVALUATION.md` v21).
- Every `dev` result recomputed on 494 labels in run `20261026T181641Z`: label summary, C-010, oracle, B1 and Llama under `pp-v0.2`, the extension and challenge comparison.
- Accrual estimate and volume-split median from run `20261026T181641Z`: the 100-comment target binds; about 5 weeks (replay 3 to 7, median 5); median 19 per week.
- Draft thresholds for all five measures, the rule for B2 meaningfully beating B1, the Afterword-post rule, the freeze list, the draft record, and the corpus export steps: `docs/proposals/accepted/2026-10-26-registered-thresholds.md`.
- Dated entries for C-001, C-002, C-008, and C-010; `PREREGISTRATION.md` v5; `ROADMAP.md` v14.

**Friction discovered:** the draft record cannot live in `registry/` before it is final; public figures diverge from the new ones.

**Delight discovered:** `afterword evaluate` rescored both conditions on the new labels in seconds, from the cache, with no model run, and the counts reconciled exactly with the store (494 scored, 1 purged comment counted as not scored).

**Claims affected:** C-001, C-002, C-008, C-010 (dated entries).

**ADRs affected:** none. A question on ADR-010 (Part 1's `dev` comments) is open for the author.

**Scope pressure:** Step 4's prompt in the runbook also lists a README "Where this is headed" section and a label UI accrual panel. The session prompt asked for the recompute, the thresholds, and the freeze, so neither was started; both wait for the threshold decisions.

**Next smallest useful step:** the author's decisions on the proposal (thresholds, reference oracle, the C-008 rule, the application version, Part 1's `dev` comments), then `registered_at`.

## Session 15, part B: decisions, `preregistration write`, the seal-day sequence (2026-10-26)

### 2026-10-26 22:40 - Decided: test-set oracle, the five thresholds, the C-008 rule, `0.2.0`

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Record the author's decisions on the threshold proposal.

**Expectation:** Numbers chosen from the proposal's options.

**Observation:** The author chose the test-set oracle as the reference, the recommended rules for recall, review reduction (0.50), SURFACE size (both parts), and SURFACE capture (1.0), both conditions for SURFACE precision, the recommended C-008 rule with the SURFACE comparison reported descriptively, and the application at `0.2.0`. On `dev`, B1 meets all five and Llama meets three: the registered bar is one `dev` predicts the registered model may miss on review reduction and SURFACE size.

**Evidence:** `EVALUATION.md` v22; `docs/proposals/accepted/2026-10-26-registered-thresholds.md`.

**Workaround:** None needed.

**Consequence:** The thresholds were chosen for what success means, not to fit Llama. A negative B2 result is now a plausible, registered outcome.

### 2026-10-26 22:45 - Seal first, then Part 1: the open ADR-010 question closes without an amendment

**Platform:** Project

**Type:** DELIGHT

**Class:** DOMAIN

**Task:** Settle whether Part 1's comments would join `dev`.

**Expectation:** An ADR-010 amendment, or labeling Part 1's early comments as `dev`.

**Observation:** The author moved the seal before Part 1's publication. Part 1 is then a test-period post, excluded by amendment before labeling, and its comments belong to neither set. ADR-010's decision covers this as written; its Context had predicted the other order, so a dated note was added under its status, with the decision text unchanged.

**Evidence:** ADR-010 (note of 2026-10-26); `PREREGISTRATION.md` v6, Step 5 and the quick reference.

**Workaround:** None needed.

**Consequence:** Seal day must end with the push before Part 1 goes live.

### 2026-10-26 22:55 - `afterword preregistration write`

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Write the preregistration record on seal day without hand-editing JSON.

**Expectation:** A small command; the risk is overwriting a sealed record.

**Observation:** `preregistration.write_record` creates the file with exclusive mode, so an existing record is never replaced, and refuses a `registered_at` that is not UTC. The service takes the conditions from the application's pins (digest and context size from `afterword.providers.ollama`, the policy from `afterword.policy`), so the record it writes always passes shadow mode's checks; a test asserts exactly that. Tests were written first and failed before the code existed.

**Evidence:** `src/afterword/preregistration.py` (`write_record`), `src/afterword/service.py` (`write_preregistration`), `src/afterword/cli.py` (`cmd_preregistration_write`), four tests in `tests/test_preregistration.py`.

**Workaround:** None needed.

**Consequence:** Closes the earlier friction entry ("The preregistration record is not drafted in `registry/`"): the record is written by a command on seal day, step 6 of the sequence.

### 2026-10-26 22:50 - The review of `preregistration write` was a local advisory, not the cross-vendor panel

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** The audit the author's engineering policy requires before committing a change to what the seal commits (an irreversible step, so a deep audit).

**Expectation:** A cross-vendor panel through the Decision Engine.

**Observation:** The Decision Engine server failed to connect at session start, before any request. The policy's fallback ran instead: one model (the session's own) reviewing five dimensions, recorded as advisory with no audit ID. It found one real gap: a write failing partway would leave a truncated record that every tool then fails to parse and that `preregistration write` refuses to replace. Fixed, with a test written to fail first. Three low findings are documented in Step 5 (the gap between probe and `registered_at`, the commit message's Ollama placeholder, and the identity scan running after `registered_at`, which passes on the current tree).

**Evidence:** local advisory run `local_host_97be365ee59879c8d4aef608` (no audit ID); `tests/test_preregistration.py`, `test_a_record_that_fails_partway_is_not_left_behind`.

**Workaround:** The local advisory, labeled as such.

**Consequence:** The gate is not closed by a cross-vendor review. Whether to rerun it before seal day, or seal on the advisory, is the author's call.

### 2026-10-27 - The 3.12 test run hangs at the pre-commit hook test

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Run the full check list after the `preregistration write` change.

**Expectation:** Both suites pass, as they did earlier the same session (771 on each).

**Observation:** On 3.14, 776 passed in 3:44. On 3.12 (`uv run --isolated --python 3.12 pytest`), three runs stalled at `test_pre_commit_hook_rejects_a_staged_em_dash`, which commits in a throwaway repo whose hook calls `uv run`. The first two stalls happened while two full runs overlapped in the background; the third ran alone. Processes from the stalled runs were left running; stopping them was not permitted from the session.

**Evidence:** the verbose log stops at that test; the 3.12 run was not re-attempted after the leftover processes were found.

**Workaround:** None in session. The 3.12 suite is left for the author's terminal once the leftover processes are stopped.

**Consequence:** Check 6 is unverified for this change. Never run two full test runs at once.

### 2026-10-27 - The seal moves to early November; two commits instead of one

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Prepare the commit messages after the author moved the seal.

**Expectation:** One preregistration commit on seal day holding everything.

**Observation:** The seal moves to early November and Part 1 to 2026-11-10, still after the seal. The work lands first in a preparation commit (thresholds, freeze table, `preregistration write`, version `0.2.0`), whose message states that preregistration has not happened. The seal commit then holds only the record and the corpus manifest; its message is kept in the git-ignored `seal-commit-message.txt` with three placeholders (the registered time, the probe run, the Ollama version) that Step 5 fills.

**Evidence:** `PREREGISTRATION.md` v6, Step 5; `.gitignore`.

**Workaround:** None needed.

**Consequence:** The version bump is no longer in the seal commit, as first decided; the frozen-version table says where it is. The accrual estimate and volume-split median were computed from run `20261026T181641Z`, and the registered text says a later full probe before the commit replaces them; the seal-day probe is such a probe, about two weeks later. Which basis to freeze is open for the author.

### 2026-10-27 - The volume basis is fixed before seal day

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Settle the open question from the previous entry.

**Expectation:** A choice between the 2026-10-26 run and the seal-day probe.

**Observation:** The author kept run `20261026T181641Z`: the accrual estimate and the volume-split median of 19 are the registered values, and the seal-day probe does not replace them. `EVALUATION.md` records the change to the original rule ("the last full probe run before preregistration") as dated and made before registration.

**Evidence:** `EVALUATION.md` v22 (secondary measures, the 2026-10-26 accrual entry, "Registered thresholds").

**Workaround:** None needed.

**Consequence:** Seal day needs no baseline step and no edit to `EVALUATION.md`; the registered median is in the preparation commit.

### 2026-10-27 - The 3.12 suite passes once the leftover processes are gone

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Rerun check 6 after the stalls recorded above.

**Expectation:** The same stall at the pre-commit hook test.

**Observation:** With no Python, pytest, or uv process left from the stalled runs, `uv run --isolated --python 3.12 pytest` passed, 776 tests in 4:02, run alone in the foreground. Consistent with the stalls coming from overlapping runs contending in uv, not from the code; the cause was not isolated further.

**Evidence:** one foreground 3.12 run; the process list empty beforehand.

**Workaround:** Run the two suites one after the other, never two at once.

**Consequence:** Check 6 is verified for this change. This corrects the entry "The 3.12 test run hangs at the pre-commit hook test", which stands as written.

### Part B summary

**Completed:** thresholds and frozen versions in `EVALUATION.md` v22; the proposal accepted and moved; `preregistration write` with tests; application `0.2.0` (`pyproject.toml`, `afterword.__version__`, `uv.lock`); the seal-day sequence in `PREREGISTRATION.md` v6, Step 5; `COMMANDS.md` v6; `DATA-MODEL.md`; the ADR-010 note; the README's findings paragraph and "Where this is headed"; session 14 in the friction-log index; dated entries on C-002 and C-008.

**Scope pressure:** the label UI's accrual panel (Step 4's prompt) stays unbuilt; it is optional before the seal.

**Next smallest useful step:** seal day, `PREREGISTRATION.md` Step 5, in the author's terminal; then Part 1 and its exclusion.
