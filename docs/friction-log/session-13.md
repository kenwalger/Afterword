# Friction log: session 13

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 13: self-agreement diagnosis (2026-10-23)

A diagnosis of the `dev` self-agreement report (80 compared; consequential agreement 53 of 80; class kappa 0.344), at the author's request, changing nothing. All numbers come from a scratch script over `afterword.label_records` (`read_labels`, `read_batches`, `analysis_labels`, `batch_post_orders`, `wilson`), printing counts only. No comment text, reason, note, or ID was printed or read. The draw's strata were reconstructed from the recorded seed and draw time by the library's own rule. No code, label, or report file was changed.

### 2026-10-23 18:30 - The self-agreement check covers 80 of the 112 drawn comments

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Diagnose the self-agreement report before deciding what to do about it.

**Expectation:** The report compares the whole draw.

**Observation:** The draw (2026-10-23 17:19 UTC, seed 20261018) pooled 342 labels and sampled 112: 92 graded 2 or 3, plus 25 at random (5 of them also graded 2 or 3). 80 were labeled, in two browser batches of 40, both in publication order. Labeled: 66 of 92 graded, 14 of the 20 random-only, 2 of the 5 overlap. The 32 not labeled are all shuffled-order labels: 23 `lg-v0.3` (20 graded 2 or 3) and 9 `lg-v0.6` (6 graded 2 or 3). The report says "80 compared" but nothing says the draw was 112; the draw record says so.

**Evidence:** `reports/eval/self-agreement-20261023-s20261018.json` (sample 112); `self_agreement.jsonl` holds 80 records; batch records.

**Workaround:** None (diagnosis only).

**Consequence:** Because the self-agreement batches follow publication order, the labeled 80 are the oldest posts first: 50 publication-order (`lg-v0.2`) originals, 27 shuffled `lg-v0.3`, 3 shuffled `lg-v0.6`. The `lg-v0.6` labels (176 of 478) are almost unmeasured.

**Follow-up:** The report could print "labeled N of the M drawn" from the draw record. Not changed (diagnosis only).

### 2026-10-23 18:35 - Self-agreement: the binary drops in one direction, and class moves out of TECHNICAL_EXTENSION

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Break down the 27 binary disagreements and the class disagreements.

**Expectation:** Disagreements in both directions, near the 1/2 boundary.

**Observation:**
- **Grade transitions (original -> self-agreement, all 80):** 0->0 4, 0->1 3, 1->1 6, 1->2 1, 2->0 1, 2->1 21, 2->2 19, 2->3 13, 3->0 1, 3->1 3, 3->2 2, 3->3 6. Same grade 35 of 80.
- **The 26 downgrades:** 2->1 21, 3->1 3, 2->0 1, 3->0 1. Retained: 40 of 66 originally graded 2 or 3 (60.6%, Wilson 48.5% to 71.5%). Upgrade: 1 of 14 originally graded 0 or 1 (1->2).
- **The original's own hindsight:** of the 16 originals graded 2 or 3 prospectively but below 2 retrospectively, 10 were downgraded now. In 10 of the 26 downgrades the new prospective grade equals the original retrospective grade.
- **Replied before the original label:** downgraded 11 of 15 originals with no reply yet (Wilson 48% to 89%) against 15 of 51 with a reply (19% to 43%).
- **By original order and guide:** publication order (`lg-v0.2`, labeled 2026-10-03 and 2026-10-04) 35 of 50 agree on the binary, retention 25 of 39; shuffled `lg-v0.3` (2026-10-07) 16 of 27, retention 14 of 25; shuffled `lg-v0.6` (2026-10-09) 2 of 3. By date: 10-03 5 of 5, 10-04 30 of 45, 10-05 1 of 1, 10-07 15 of 26, 10-09 2 of 3. All 80 originals are `initial` labels (no calibration exists).
- **By draw stratum:** graded only 39 of 64; random and graded 1 of 2; random only 13 of 14.
- **Class, by original:** `TECHNICAL_EXTENSION` 40 (same class 8, same binary 22, 18 downgraded); `TECHNICAL_QUESTION` 21 (18, 18, 2 down, 1 up); `CONVERSATIONAL` 11 (9, 8, 3 down); 8 other comments across six classes.
- **Largest class transitions (42 changed):** `TECHNICAL_EXTENSION` -> `CONVERSATIONAL` 18, -> `TECHNICAL_QUESTION` 6, -> `CHALLENGE_OR_COUNTEREXAMPLE` 4, -> `OPPORTUNITY` 2; `TECHNICAL_QUESTION` -> `CONVERSATIONAL` 2. Of the 26 downgrades, 14 are `TECHNICAL_EXTENSION` -> `CONVERSATIONAL`, and 20 end in `CONVERSATIONAL` or `LIGHTWEIGHT_ACKNOWLEDGMENT`.
- **Marginals:** originals `TECHNICAL_EXTENSION` 40, `TECHNICAL_QUESTION` 21, `CONVERSATIONAL` 11; self-agreement `CONVERSATIONAL` 30, `TECHNICAL_QUESTION` 25, `TECHNICAL_EXTENSION` 10.

**Evidence:** scratch script over `afterword.label_records`, counts only.

**Workaround:** None.

**Consequence:** The disagreement is one boundary moving: what counted as a technical contribution (and consequential) two to three weeks ago now reads as conversation (and grade 1). That is the boundary the 2026-10-18 relabeling-scope proposal named as confusable, and the one candidate (b), the extension split, would cut.

**Follow-up:** For the author's review of the disagreement list (`...-disagreements.txt`, git-ignored).

### 2026-10-23 18:40 - One sitting, and the second half went faster and downgraded more

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Check whether the self-agreement labels were made in one sitting and whether fatigue shows.

**Expectation:** Several shorter sessions.

**Observation:**
- **One sitting.** Two browser batches, 40 planned and 40 labeled each, ended `complete`, no skips, no notes, post panel available. Batch 1 17:24 to 18:03 UTC (38.6 min), batch 2 18:03:39 to 18:19 UTC (15.8 min): 17 seconds between them, no gap over 10 minutes between consecutive labels. 54 minutes for 80.
- **Speed.** Self-agreement `duration_seconds` median 25.1, mean 40.7; the same comments' originals median 42.2, mean 77.2. By position quarter (20 each), median 43.0, 29.9, 28.9, 17.2 seconds.
- **Grades by position quarter (self-agreement / original):** Q1 {0: 2, 1: 5, 2: 8, 3: 5} / {0: 3, 1: 3, 2: 14}, 2 downgraded; Q2 {0: 2, 1: 10, 2: 4, 3: 4} / {0: 3, 2: 15, 3: 2}, 9; Q3 {0: 2, 1: 7, 2: 4, 3: 7} / {0: 1, 1: 2, 2: 8, 3: 9}, 6; Q4 {1: 11, 2: 6, 3: 3} / {1: 2, 2: 17, 3: 1}, 9.
- **Position is confounded with cohort,** because the batches follow publication order: Q1 and Q2 are 2026-10-03/04 originals, Q4 mostly 2026-10-07. Within one cohort the second half still downgrades more: publication-order originals 4 of 19 then 10 of 20; shuffled `lg-v0.3` 4 of 12 then 7 of 13. Within a cohort, later position is also later posts, so fatigue and post age cannot be separated here.

**Evidence:** `batches.jsonl` start and end records for pass `self_agreement`; label `duration_seconds` and `labeled_at`. Aggregates only.

**Workaround:** None.

**Consequence:** The guide's batch limit (40) was kept, but the two batches ran back to back. The self-agreement labels are faster than the originals and faster still late in the sitting, so they are not obviously the more careful read.

**Follow-up:** None decided.

### 2026-10-23 18:45 - If the self-agreement grades were the standard

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Project the consequential share under the self-agreement grades.

**Expectation:** A small shift.

**Observation:**
- **The 80:** consequential 66 (82.5%) originally, 41 (51.3%) now. The 80 oversample graded comments, so this is not a corpus share.
- **The pool (342), reweighted by stratum:** 92 graded x 0.606 + 250 not graded x 0.071 gives about 74, 21.5%, against 92, 26.9%.
- **All of `dev` (478, 129 consequential):** 129 x 0.606 retained gives about 78 (Wilson range 63 to 92); 349 not consequential x 0.071 upgraded gives about 25, but on 1 of 14 (Wilson 1.3% to 31.5%, so 5 to 110). Point projection about 103 of 478 (21.6%) against 129 (27.0%); without upgrades about 78 (16.3%).
- **Caveats:** retention differs by cohort (publication order 25 of 39, shuffled `lg-v0.3` 14 of 25) and is unmeasured for `lg-v0.6` (1 of 2), which holds 45 of the 129; 37 of those 45 were not even in the pool.

**Evidence:** as above.

**Workaround:** None.

**Consequence:** The consequential count is the denominator of recall and capture and the basis of the thresholds still to be registered against the oracle.

**Follow-up:** Options below.

### 2026-10-23 18:50 - Options set out, none recommended

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Set out the options the author named, with effort and trade-offs.

**Expectation:** n/a.

**Observation:** Effort uses this sitting's mean (40.7 s per label) and the originals' mean on the same comments (77.2 s) as low and high.
- **Before any option:** the 32 unlabeled comments of today's draw (26 graded 2 or 3, all shuffled): 22 to 41 minutes. Completes the measurement as drawn; 26 more graded comments would tighten retention and add shuffled `lg-v0.3` and `lg-v0.6` coverage.
- **(a) Re-grade only the consequential field on labels originally graded 2 or 3.** 129 labels (66 already re-graded today): about 90 minutes at this sitting's pace for all 129, or about 45 for the 63 not yet re-graded; a grade-only read may be faster, unmeasured. No tool supports it: a grade-only pass is new code, tests, and a guide version (which also means reviewing `LABELING-FIELD-GUIDE.md`). It can only move comments down: the 349 graded 0 or 1 are never reread, though the upgrade rate is unknown (1 of 14). The labeler knows every comment shown was graded 2 or 3, which is itself a cue. Class is left as it was, and class is where most disagreement is (kappa 0.344), which the oracle and every ceiling depend on. Mixes grades from two dates on the same record.
- **(b) Relabel the early labels fully.** The 302 labels of 2026-10-03 to 2026-10-07 (`lg-v0.2` and `lg-v0.3`), where 25 of the 26 downgrades are: 3.4 to 6.5 hours, 8 batches. Fixes class and grade together for the cohorts measured. 77 of the 80 compared today are in it, so those get a third read within days. The 176 `lg-v0.6` labels stay, with 3 measured; whether they share the shift is unknown. The corpus would mix labels made under two guides and two weeks apart.
- **(c) Relabel all of `dev`.** 478 labels: 5.4 to 10.2 hours, 12 batches. One guide version and one period for every label. The guide's own text for poor agreement reads this way: "the corpus is relabeled as a new version under a revised guide, and the poor agreement is reported as a finding." Most effort, and the most rereads.
- **Shared by all three:** the guide does not define "poor"; neither read is known to be the right one (the self-agreement read is faster, and later in the sitting downgraded more); the guide says original labels are not changed after the check, so any relabel writes new records (a calibration pass replaces the analysis label but keeps the original on disk; a "new version" is a different directory, which the 2026-10-18 decision to keep every label in `unfrozen` would have to be squared with); the guide asks for a revision first, and the `TECHNICAL_EXTENSION` / `CONVERSATIONAL` boundary is where it moved; a check of the new labels by the same rule needs another 14 days, which moves preregistration; and every `dev` number since 2026-10-07 (oracle ceilings, B1 and B2 recall, the 2026-10-18 decisions' evidence, C-001, C-010) would be recomputed. Model outputs are cached, so rescoring is cheap; the labeling is not.
- **Doing nothing** is also open: the 14-day consequential agreement is 66.3% (Wilson 55.4% to 75.7%), reported as a finding.

**Evidence:** as above; `LABELING-GUIDE.md`, "Self-agreement check"; `docs/proposals/accepted/2026-10-18-relabeling-scope.md`.

**Workaround:** None.

**Consequence:** C-001 and C-011 entries appended (2026-10-23).

**Follow-up:** The author's decision.

### 2026-10-23 18:55 - Session summary

**Goal:** Diagnose the self-agreement result; counts only; change nothing.

**Completed:** Diagnosis of the 80 compared labels from `afterword.label_records`; friction entries; C-001 and C-011 entries. No code, label, or report changed; nothing committed.

**Friction discovered:** The report does not say it covers 80 of 112 drawn. The batches' publication order makes a partial sitting cover the oldest labels first.

**Delight discovered:** The draw is reproducible from its seed and time alone, so the strata could be reconstructed without opening the ID file.

**Claims affected:** C-001 (agreement on class 38 of 80, kappa 0.344); C-011 (the 14-day baseline is 53 of 80 on the binary).

**ADRs affected:** None.

**Scope pressure:** A grade-only pass (option (a)) would be a new tool; not built. A "drawn vs labeled" line in the report; not built.

**Next smallest useful step:** The author's decision among the options, possibly after labeling the 32 remaining comments of the draw.

## Session 13, part B: the check completed, and the author's decisions (2026-10-23)

### 2026-10-23 19:30 - Self-agreement complete: the unhurried sitting agrees far more

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record the completed `dev` self-agreement check, with the pace evidence.

**Expectation:** The remaining 32 would look like the first 80.

**Observation:**
- **All 112 compared** (`self-agreement-report-20261023T191354Z.json`): consequential split 80 of 112 (71.4%, Wilson 62.5% to 79.0%); 31 left consequential (2 to 1: 25, 3 to 1: 4, 2 to 0: 1, 3 to 0: 1), 1 entered (1 to 2); same grade 53; same class 55, kappa 0.358.
- **First sitting (80):** two batches back to back (17:24 to 18:03, 18:03 to 18:19 UTC, 17 seconds apart), median 25.1 seconds per comment, falling by quarter from 43.0 to 17.2; 53 of 80 on the split, kappa 0.344.
- **Second sitting (32):** began 17 minutes after the first ended, one batch 18:36 to 19:13 UTC, median 44.8 seconds (the same comments' originals: 42.5); 27 of 32 (84.4%, Wilson 68.2% to 93.1%), 5 left consequential and none entered; kappa 0.398.
- **Same original group, both sittings:** the shuffled `lg-v0.3` originals agree in 16 of 27 in the first sitting and 19 of 23 in the second. The second sitting holds only shuffled originals (23 `lg-v0.3`, 9 `lg-v0.6`), because the batches follow publication order, so sitting and post order are not fully separable.
- **Class stays low at either pace.** 57 class changes, 23 of them `TECHNICAL_EXTENSION` to `CONVERSATIONAL`; 14 of 55 original extensions stayed extensions. Both classes default to `QUEUE`.

**Evidence:** the report above; `afterword.label_records` (counts only).

**Workaround:** None.

**Consequence:** `EVALUATION.md` v20; C-001 and C-011 entries (2026-10-23, later).

**Follow-up:** Decisions below.

### 2026-10-23 19:40 - lg-v0.7, the first 150 recalibrated, no second cycle

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Apply the author's three decisions.

**Expectation:** Documentation, a version constant, and an ID file.

**Observation:**
- **`lg-v0.7`.** Grade 2 needs a named consequence ("If I saw this two weeks late, ..."), with a list of what does not make a 2 on its own (substance, relevance, a courtesy reply, hindsight), and eight synthetic worked examples on an imagined caching post. A reuse test separates `TECHNICAL_EXTENSION` from `CONVERSATIONAL`: strike opinion, agreement, praise, and general experience; if something technical another reader could use remains, it is an extension. It applies `tax-v0.2` and changes no class. One draft example ("did something similar with an in-memory cache and saw the same speedup") failed its own test, since it names what was done and what happened, like the taxonomy's own extension example; it was rewritten before the guide was saved.
- **`LABELING-FIELD-GUIDE.md` v5:** the named-consequence check, "substance is not consequence", the reuse test, and a fatigue bullet with the pace evidence (take a real break between batches).
- **The tools record `lg-v0.7`:** `LABEL_GUIDE_VERSION` in `src/afterword/labeling.py`, and the test that pins a label record.
- **Calibration list:** `reports/eval/calibration-first150-lg-v0.7.txt` (git-ignored), 150 IDs written from the label records: every analysis label made in publication order, all `lg-v0.2` initial labels, none calibrated yet. It is the same set as the 2026-10-18 list.
- **No second cycle:** recorded in `EVALUATION.md` with the author's reason. The guide sets no numeric bar, so the record says the judgment is the author's, and that the calibration labels enter analysis without a self-agreement check of their own.
- **Runbook and roadmap:** `PREREGISTRATION.md` v4 adds Step 1a with the command; `ROADMAP.md` v13 marks the check done and freezes `lg-v0.7` instead of `lg-v0.6`. `LABELING-GUIDE.md` records how its poor-agreement rule was applied on `dev` (a calibration pass in the same directory, not a new corpus version).

**Evidence:** the files named.

**Workaround:** None.

**Consequence:** After the pass, the analysis labels span `lg-v0.7` (150), `lg-v0.3` (152), and `lg-v0.6` (176), and every `dev` result is recomputed. 50 of the 150 were read in today's check, so they get a third reading within days.

**Follow-up:** The author labels the 150; then a session recomputes the `dev` results.

### 2026-10-23 19:45 - Session summary, part B

**Goal:** Record the completed self-agreement check and apply the author's decisions.

**Completed:** `EVALUATION.md` v20; `LABELING-GUIDE.md` `lg-v0.7`; `LABELING-FIELD-GUIDE.md` v5; `PREREGISTRATION.md` v4; `ROADMAP.md` v13; C-001 and C-011 entries; `LABEL_GUIDE_VERSION` bumped, with its test; the calibration ID list. Check list: ruff, format, mypy, pydoclint clean; 769 tests pass on 3.14 and on 3.12 (isolated). Not committed.

**Friction discovered:** A worked example contradicted the test it illustrated; caught by checking it against the taxonomy's own example.

**Delight discovered:** Holding the original group fixed (`lg-v0.3` in both sittings) gave a pace comparison the confounded sitting split could not.

**Claims affected:** C-001, C-011.

**ADRs affected:** None.

**Scope pressure:** The label tools' `h` help shows `TAXONOMY.md` definitions only, so the reuse test and the named-consequence test are not on screen while labeling; adding them is a tool change, not made. `CLAUDE.md`'s "Current stage" still says the calibration pass is dropped; left for the author.

**Next smallest useful step:** The calibration pass on the 150 (`PREREGISTRATION.md`, Step 1a).

## Session 13, part C: the guide's tests in the help, and CLAUDE.md (2026-10-23)

### 2026-10-23 20:10 - lg-v0.7's two tests in both tools' help

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Show the named-consequence test and the reuse test on `h` in the label UI and the terminal tool, kept in step with `LABELING-GUIDE.md` by the existing sync test; update `CLAUDE.md`'s "Current stage".

**Expectation:** Add two lines to the taxonomy help.

**Observation:**
- **Not in `afterword.taxonomy`.** That module also feeds the classifier prompt, so adding guide text there could change the prompt and its cache key. The tests live in `labeling.GUIDE_TESTS` beside `LABEL_GUIDE_VERSION`, each as (guide heading, phrase quoted from the guide, help line). `labeling.help_text()` is the taxonomy help plus the tests; the UI's taxonomy payload carries `guide_version` and `guide_tests`, and the help page lists them under the flags.
- **Terminal:** `h` now also works at the prospective grade prompt (`[0-3; h = help]`), where the grade test is needed; before, `h` worked only at the class and flag prompts.
- **Sync test (`tests/test_taxonomy.py`):** the guide's version matches `LABEL_GUIDE_VERSION` (no test checked that before), and each help entry's heading exists in the guide and its key phrase appears in both that section and the help line. A renamed heading and a changed phrase were each tried against the test, and it failed both times.
- **Docs:** `LABELING-GUIDE.md` (what `h` lists, no version change: it describes the tool, not the labels) and `WORKFLOW.md` (section 3). `CLAUDE.md`: the self-agreement check is done, and the calibration pass on the 150 under `lg-v0.7` is in progress, no longer dropped.
- A heredoc turned `"\n"` into real line breaks in three places in new code; caught by reading the result before running tests.

**Evidence:** `src/afterword/labeling.py`, `label_ui.py`, `label_ui_page.py`; `tests/test_taxonomy.py`, `test_labeling.py`, `test_label_ui.py`.

**Workaround:** None.

**Consequence:** The two tests are on screen while labeling the calibration pass.

**Follow-up:** None.

### 2026-10-23 20:15 - Session summary, part C

The help change and the `CLAUDE.md` update are done and tested on synthetic fixtures. Check list: ruff, format, mypy, pydoclint clean; 771 tests pass on 3.14 and on 3.12 (isolated). Not committed. Claims affected: none. ADRs affected: none. Scope pressure: none. Next smallest useful step: the calibration pass on the 150 (`PREREGISTRATION.md`, Step 1a).
