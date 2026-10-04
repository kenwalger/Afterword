# Friction log: session 7

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 7: Part A, labeling-facing work (2026-10-04)

Times are UTC. No comment text, names, or handles: every label and timing figure below is a count or a time, computed by code that printed aggregates only.

### 2026-10-04 20:15 - Open items in session summaries were out of date

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Orientation: list what is still open for the author.

**Expectation:** Session 6's summary lists the two chronological timings as open and `dev` labeling at 27 of 438.

**Observation:**
- `reports/timing/` holds two records, both `valid: true`, both complete, both from run `20261003T141450Z` and dated 2026-10-03: 2026-07-27 (7 comments, 228.4 s) and 2026-09-07 (44 comments, 1051.7 s). `reports/timing/practice/` holds none. Every session summary written after 2026-10-03 still listed the timings as open.
- `fixtures/labels/unfrozen/initial.jsonl` holds 150 labels, one per comment, in 6 batches (3 ended `complete`, 3 `quit`), all from the same run, all `tax-v0.1`. The 27 in session 6's summary was right when written; labeling continued after it.

**Evidence:** `afterword.timing.load_valid` (aggregate fields only); a counts-only read of the label and batch files.

**Workaround:** C-009 entry appended to `CLAIMS.md`, status updated; ROADMAP item ticked; README, WORKFLOW, and CLAUDE.md corrected.

**Consequence:** CLAUDE.md now tells orientation to count timing and label records at their source rather than copy open items forward from earlier summaries.

**Follow-up:** None.

### 2026-10-04 20:20 - C-009: the typical week meets the falsification condition

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Record the two chronological timings against C-009.

**Expectation:** Unknown; the claim names "only a few minutes" for a typical week as the falsifier.

**Observation:** Typical week: 7 comments in 3.8 minutes (32.6 s each). Busy week: 44 comments in 17.5 minutes (23.9 s each). Both are re-reads, so lower bounds; both cover reading only. Both were timed before any comment in them was labeled.

**Evidence:** `CLAIMS.md`, C-009, 2026-10-04 entry.

**Workaround:** None. Recorded as measured and mixed.

**Consequence:** The Stage 0 gate asks for an explicit decision (continue, or continue as a methodology study). Left to the author; noted in `ROADMAP.md` and the C-009 status line.

**Follow-up:** The author records the gate decision.

### 2026-10-04 20:30 - Batch records never named the tool

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Count labels by tool for `afterword label status`.

**Expectation:** Each batch record says whether the terminal or the browser wrote it.

**Observation:** `batch_start` has `mode: label` for both transports and nothing else that tells them apart. All 150 existing labels therefore count as "not recorded". (Session 5's integrity check identified its one terminal batch from session context, not from the record.)

**Evidence:** `batch_start` keys in `batches.jsonl` (keys and counts only).

**Workaround:** `batch_start` now records `tool` (`terminal` or `browser`). Older batches are reported as `not recorded`, never inferred.

**Consequence:** By-tool counts start with the next batch.

**Follow-up:** None.

### 2026-10-04 20:35 - The terminal tool's quit path, fixed

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Fix the loss path found in session 6 ("When the terminal labeling tool writes a label"): `q` at the `Save?` prompt discarded a fully answered comment.

**Expectation:** A small change in `label_one`.

**Observation:** The rule now: `q` or end of input at `Save?` saves the label and its note, then stops. `q` at an earlier prompt, or Ctrl+C anywhere, stops without saving, and the tool says "was NOT saved" when answers had been entered ("was not labeled" when none had). The terminal's `batch_end` gains `abandoned_in_progress`. The prompt reads `Save? [Enter = yes, r = redo, s = skip, q = save and stop]`.

**Evidence:** `tests/test_labeling.py`: `test_q_at_the_save_prompt_saves_the_label_and_its_note_then_stops` reproduces the old loss (it fails on the session 6 code: no label written), plus tests for end of input, quit with answers entered, quit before any answer, and Ctrl+C at `Save?`.

**Workaround:** None needed.

**Consequence:** A quit can still lose the comment on screen when it comes before the summary, but never silently. Labels already written are unchanged.

**Follow-up:** None.

### 2026-10-04 20:45 - Calibration pass: design choices

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Add a calibration pass: re-label early comments from scratch, never overwriting.

**Expectation:** A new pass name.

**Observation:** Three choices were needed beyond the name:
- **What it offers.** A calibration batch offers only comments that already have an initial label (narrowed by `--ids`). Without that, a calibration pass would also offer unlabeled comments.
- **Which label analysis uses.** The latest label from a pass other than `self_agreement`, by `labeled_at`; a tie goes to calibration. The self-agreement check compares against that label.
- **Guide version.** The guide now defines a new pass and an analysis rule, so it becomes `lg-v0.3`. Grades, definitions, tests, and the initial pass are unchanged, so the 150 `lg-v0.2` labels need nothing.

**Evidence:** `LABELING-GUIDE.md` `lg-v0.3`; `DATA-MODEL.md` v7; `afterword.label_records.analysis_labels` and `calibration_differences`, with tests.

**Workaround:** None.

**Consequence:** No calibration labels exist yet, so there is no difference to report.

**Follow-up:** Report calibration differences (counts only) once calibration labels exist.

### 2026-10-04 20:55 - Partial consequential share: 26%, from the earliest posts

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Summarize the `dev` labels (counts only) and recompute the accrual estimate provisionally.

**Expectation:** A share near the proposal's assumed 15%.

**Observation:**
- 150 labels. By class: CORRECTION 2, CHALLENGE_OR_COUNTEREXAMPLE 2, TECHNICAL_QUESTION 23, OPPORTUNITY 0, DIRECT_QUESTION 5, TECHNICAL_EXTENSION 49, CONVERSATIONAL 42, LIGHTWEIGHT_ACKNOWLEDGMENT 19, LIKELY_SPAM_OR_NOISE 8, UNCERTAIN 0.
- Prospective grades: 0: 53, 1: 58, 2: 34, 3: 5. Graded 2 or 3: 39 (26.0%; Wilson 95% interval 19.6% to 33.6%).
- Prospective against retrospective, where both exist (147): same grade 135, same consequential binary 140; 3 consequential only in hindsight, 4 only prospectively.
- `replied_before_labeling` true: 108 of 150 (72%).
- Every batch so far used publication order, so the 150 are the comments on the earliest-published posts, not a random sample.

**Evidence:** `afterword.label_records.summarize` over the analysis labels.

**Workaround:** None.

**Consequence:** `EVALUATION.md` v7 records a provisional estimate: at 26% the 100-comment target binds across the interval, about 6 weeks at the mean rate and 14 at the median, inside the 16-week cap. Marked provisional until `dev` labeling is complete.

**Follow-up:** Recompute on the full `dev` set before preregistration.

### 2026-10-04 21:00 - Heredoc scripts failed to parse in the shell tool

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Apply multi-line edits with a short Python script passed through a quoted bash heredoc.

**Expectation:** A quoted heredoc passes its body through unchanged.

**Observation:** Twice, a heredoc holding Python triple-quoted strings failed with `unexpected EOF while looking for matching ''`, and nothing ran. A third, which did run, turned an escaped `\n` in the script into a real line break in the edited file.

**Evidence:** Shell tool errors during the session.

**Workaround:** Scripts are written to the scratchpad with the file tool and run from there. The broken line break was fixed by hand before any check ran.

**Consequence:** A few minutes.

**Follow-up:** None.

### 2026-10-04 21:40 - Edit scripts wrote CRLF line endings

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Run the full check list at the checkpoint.

**Expectation:** Every working file stays LF (`.gitattributes`, session 6).

**Observation:** 14 changed files had CRLF endings. The scratchpad edit scripts used Python's `Path.write_text`, which on Windows translates each line feed to CRLF. Files that ruff later reformatted came back LF; the docs did not. In the same run, one label UI test failed once on Python 3.14 (`test_the_page_is_self_contained_and_inserts_text_safely`) and passed on rerun; the cause was not established.

**Evidence:** `grep -lU` for carriage returns over the changed files; the test rerun.

**Workaround:** Carriage returns stripped from the 14 files; the full check list rerun: 508 passed on 3.14 and on 3.12 (isolated).

**Consequence:** Later edit scripts write bytes (`Path.write_bytes`), so no line ending is translated. The shell tool also turned an escaped line feed inside this entry into a real line break; fixed by hand.

**Follow-up:** Watch for the label UI test failing again.

### 2026-10-04 21:45 - Checkpoint: Part A complete

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Finish Part A (A0 to A4) and stop for the author to commit.

**Expectation:** The full check list passes.

**Observation:** A0 C-009 recorded; A1 label summary and provisional accrual estimate; A2 save-on-quit fix with a reproducing test; A3 calibration pass in both tools, `lg-v0.3`; A4 one shared counting function (`afterword.label_records.progress`) behind `afterword label status`, the terminal's closing line, and the label UI's badge. Full check list: ruff, format, mypy, pydoclint, 508 tests on 3.14 and on 3.12 (isolated), identity scan 0 disallowed.

**Evidence:** `commit-message.txt`.

**Workaround:** None.

**Consequence:** Part B waits for the author's commit.

**Follow-up:** Part B.
