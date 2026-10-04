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

## Session 7: between the checkpoint and Part B, then Part B (2026-10-04)

### 2026-10-04 21:55 - Gate decided: continue; the volume question becomes C-012

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Record the author's Stage 0 gate decision.

**Expectation:** A line in the roadmap.

**Observation:** The author decided to continue as planned. The C-009 evidence (cheap typical week, costly busy week) is carried forward as a new claim, C-012: assisted triage delivers most of its value in high-volume weeks. Its test is a secondary analysis in `EVALUATION.md` v8: test-period results split at the trailing-13-week median volume, frozen at preregistration.

**Evidence:** `ROADMAP.md` Stage 0 gate; `CLAIMS.md` C-009 (dated entry; the claim and its status line left as written) and C-012.

**Workaround:** None.

**Consequence:** The C-009 status line still says the gate decision is "not yet recorded"; the dated entry below it supersedes that, as the instruction not to rewrite C-009 requires.

**Follow-up:** None.

### 2026-10-04 22:00 - Oracle ceiling: pp-v0.1 caps review reduction near 18% on these labels

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Apply `pp-v0.1` to the 150 labels themselves: what perfect classification would give.

**Expectation:** Unknown.

**Observation:**
- Class defaults only: 27 of 150 collapsed (18.0%), 39 of 39 consequential surfaced. With the labeled flags: 19 collapsed (12.7%). Without `tax-v0.1` `REFERENCES_SPECIFIC_CLAIM` raises: 20 (13.3%).
- Consequential comments: 16 at `SURFACE`, 23 at `QUEUE`, 0 at `COLLAPSED`. 19 of the 39 are `TECHNICAL_EXTENSION`.
- 8 acknowledgments leave `COLLAPSED` on flags: 5 on `REPLY_TO_AUTHOR`, 2 on `NEEDS_THREAD_CONTEXT`, 1 on `REFERENCES_SPECIFIC_CLAIM`; none is graded consequential.
- Caveats: earliest posts only; 72% labeled after replying.

**Evidence:** `afterword.label_records.oracle_ceiling` and `class_crosstab` (counts only); `EVALUATION.md` v8 and v9, "Provisional observations on `dev`".

**Workaround:** None.

**Consequence:** On these labels recall is not the constraint; reduction is, because only acknowledgments and spam collapse by default. Whether to change the policy is a Stage 3a question for the full `dev` set. Nothing changed.

**Follow-up:** Recompute on the full `dev` set, reporting publication-order and shuffled labels apart.

### 2026-10-04 22:00 - The flaky label UI test did not recur

**Platform:** Project

**Type:** FRICTION

**Class:** UNKNOWN

**Task:** Reproduce and fix the single failure of `test_the_page_is_self_contained_and_inserts_text_safely` on Python 3.14 at the checkpoint.

**Expectation:** A timing or ordering dependency.

**Observation:** The test only inspects the module constant `PAGE` (characters, forbidden markup), with no clock, network, or file system. It passed 50 of 50 runs alone in fresh interpreters, and the whole file passed 15 of 15. No other test or module mutates `PAGE`. The failing run's output was cut to its last two lines, so the failing assertion was not kept. The most likely cause is that `label_ui_page.py` was rewritten while that suite was importing it (the session's edit scripts and a line-ending conversion touched it around then), but this is not established.

**Evidence:** The repeat runs; `grep` for uses of `PAGE`.

**Workaround:** None in code. Full test runs in this session now use `-rf`, so a failure keeps its summary line.

**Consequence:** Tracked, not silent: if it fails again, keep the full output and reopen this entry with a dated follow-up.

**Follow-up:** Open (tracked). Owner: whoever sees it fail next.

### 2026-10-04 22:00 - Partial-label analyses split by post order

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** The author labels with `--posts random --seed N` from now on; report publication-order and shuffled labels apart.

**Expectation:** Batch records say which order each batch used.

**Observation:** They do (`post_order`, absent on the first batch, which predates the option and was publication order). All 150 current labels are publication order.

**Evidence:** `afterword.label_records.batch_post_orders`, `split_by_post_order`, `summarize_by_post_order`; `afterword label status` prints "labels by post order".

**Workaround:** None.

**Consequence:** Provisional figures (consequential share, oracle ceiling) can be recomputed on the shuffled labels alone once there are enough.

**Follow-up:** None.

### 2026-10-04 22:00 - tax-v0.2 renumbers the terminal flag menu

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Make `CONTAINS_CODE` and `CONTAINS_LINK` structural (`tax-v0.2`), set from normalization and shown read-only.

**Expectation:** A taxonomy and labeling-tool change only.

**Observation:**
- The terminal's numbered flag menu lost two entries, so the numbers moved: `REFERENCES_SPECIFIC_CLAIM` is now 2 (was 4) and 4 is now `HOSTILE_TONE`. In the browser the `c` and `l` keys are gone; every other key is unchanged.
- The heuristic used to set the code and link flags itself. They now come from the service's structural flags for B1 and B2 alike, so `hb-v0.1`'s rules are unchanged and keep their version; only the source recorded in `flags_by_source` moves from `heuristic` to `structure`.
- The model can no longer return either flag: they are absent from the `pr-v0.2` prompt and schema, and naming one is `malformed:structural_flag`.

**Evidence:** `tests/test_labeling.py` (menu comment), `tests/test_classify_service.py` (`test_b1_and_b2_receive_the_same_structural_flags`, `test_cached_pr_v0_1_results_are_not_reused_under_pr_v0_2`), `tests/test_classifier.py`.

**Workaround:** WORKFLOW section 3 lists the new terminal numbers.

**Consequence:** Muscle memory from earlier terminal batches is wrong for flag 4.

**Follow-up:** None.

### 2026-10-04 22:00 - REFERENCES_SPECIFIC_CLAIM: post-only, with a test

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Decide whether `REFERENCES_SPECIFIC_CLAIM` should also cover claims in the author's own replies (asked of the author before applying).

**Expectation:** Mirror `CORRECTION`, which covers both.

**Observation:** In the 150 labels the author set the flag on 82, and on 39 of the 64 that reply to the author, where `REPLY_TO_AUTHOR` already gives the same raise. The author chose post-only and tightened it: the flag applies only if one could point to the exact sentence, step, figure, or claim in the post; engaging with the topic or general argument does not qualify.

**Evidence:** `TAXONOMY.md` `tax-v0.2`; synthetic `bench-034` (qualifies) and `bench-035` (does not).

**Workaround:** None.

**Consequence:** `REFERENCES_SPECIFIC_CLAIM` in `tax-v0.1` labels is not comparable with `tax-v0.2` usage; results report the two apart, and calibration labels made under `tax-v0.2` supersede them. The oracle ceiling is reported with and without the `tax-v0.1` raises (1 comment differs).

**Follow-up:** Calibration pass on early labels under `tax-v0.2`.

### 2026-10-04 22:00 - The "Aw" mark arrived as favicon exports

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** B4: wire in brand assets named per `BRAND.md`.

**Expectation:** `img/Afterword_mark.png`, `img/Afterword_logo_mono.png`, and the dark wordmark.

**Observation:** The dark wordmark exists, and the README already had the `<picture>` markup (the author's commit `6ebb744`). The mark exists only as a favicon-generator set (`favicon-16x16.png`, `favicon-32x32.png`, `favicon.ico`, `apple-touch-icon.png`, two `android-chrome` sizes, `site.webmanifest` with empty names), light version only; viewed, it is the bold upright A with the blue italic w. No monochrome wordmark, dark mark, master file, or SVG.

**Evidence:** `img/`; `BRAND.md` v2 variant table.

**Workaround:** The 16 and 32 pixel PNGs are inlined in the label UI as data-URI favicons, with a test that the inlined bytes equal the files. The page's Content-Security-Policy gains `img-src data:`, which still allows nothing to be fetched; the self-containment test now allows exactly those two `<link rel="icon">` elements.

**Consequence:** `BRAND.md` records the actual file names. Its dark-mode colors stay marked "(proposed)": approving them is the author's call.

**Follow-up:** For the author: a monochrome wordmark, a dark mark, a master file or SVG, and the empty `name` fields in `site.webmanifest`.

## Session 7: benchmark rerun and wrap-up (2026-10-04)

### 2026-10-04 23:10 - Removing code and link flags moved the pressure onto the others

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Compare `pr-v0.1` and `pr-v0.2` on the 54 shared synthetic cases (the author ran both models in their own terminal).

**Expectation:** Fewer model-set flags, and no tier change, since `CONTAINS_CODE` and `CONTAINS_LINK` never raised a tier.

**Observation:**
- qwen set `REFERENCES_SPECIFIC_CLAIM` on 43 cases (was 31) and `NEEDS_THREAD_CONTEXT` on 16 (was 7), despite the stricter definition. Flag-caused raises rose from 10 to 16, and its 6 collapsed acknowledgments all went to `QUEUE` (4 by `REFERENCES_SPECIFIC_CLAIM`, 2 by `NEEDS_THREAD_CONTEXT`). It collapsed 0 of 59.
- llama: `REFERENCES_SPECIFIC_CLAIM` 12 to 16, `NEEDS_THREAD_CONTEXT` 15 to 18, raises 1 to 3. Collapsed 12 to 9 on the shared cases: two spam cases raised by `NEEDS_THREAD_CONTEXT`, one spam case reclassed `CONVERSATIONAL`.
- Injection tiers unchanged (8 of 10 each); warm time unchanged within noise (the prompt is about 3% shorter).

**Evidence:** `docs/benchmarks/2026-10-03-synthetic-local-models.md`, 2026-10-04 section; the four `reports/bench/` files (synthetic only).

**Workaround:** None. No policy or prompt change.

**Consequence:** `EVALUATION.md` v10 records the structural point: when model-set flags can only raise priority, each one is a channel for eroding review reduction, and removing some shifts the pressure to others. Two candidate designs are recorded for evaluation on `dev` only: (a) evidence-required flags (for example, `REFERENCES_SPECIFIC_CLAIM` counts only with a verified quote of the referenced span), and (b) model-set `REFERENCES_SPECIFIC_CLAIM` and `NEEDS_THREAD_CONTEXT` as informational, not tier-raising. Informational, no model choice: on synthetic data qwen under `pp-v0.1` would give zero review reduction.

**Follow-up:** Evaluate (a) and (b) on `dev` in Stage 3a.

### 2026-10-04 23:10 - Qwen timed out once, at 350 seconds

**Platform:** Project

**Type:** FRICTION

**Class:** UNKNOWN

**Task:** Find what timed out on adv-102 under `pr-v0.2`.

**Expectation:** A clear cause in the report.

**Observation:** The `httpx` client gave up: the provider's `TIMEOUT_S` is 300 s, and a non-streaming request returns nothing until generation ends. The case ran 350.3 s from about 22:13:33 UTC. The 200-token output cap bounds a runaway generation to about a minute at this run's rates, so "generation that never ended" is unlikely. Leading hypothesis: a stall inside Ollama, most likely in schema-constrained sampling. Under `pr-v0.1` the same case returned in 23.3 s, and the next case returned normally in 16.7 s. The 50 s beyond the read timeout is not explained by anything recorded.

**Evidence:** `src/afterword/providers/ollama.py` (`TIMEOUT_S`, `stream: False`, `num_predict`); the qwen `pr-v0.2` report.

**Workaround:** None. The case failed safe to `SURFACE`.

**Consequence:** Cause not established; hypothesis recorded in the benchmark write-up.

**Follow-up:** For the author: check Ollama's server log around 22:13 to 22:20 UTC, and rerun with `--set adversarial` to see whether it reproduces at temperature 0.

### 2026-10-04 23:10 - Duplicate flags: strict or repaired, decided at preregistration

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Record the choice for model outputs that list a flag twice (qwen: 3 of 59 under `pr-v0.2`, 1 of 54 under `pr-v0.1`).

**Expectation:** Rare enough to ignore.

**Observation:** Each one is `MALFORMED` and surfaced, so it costs review reduction on what may be a readable classification. De-duplicating would save that, at the cost of the parser deciding what the model meant and a validity rate that needs two readings.

**Evidence:** `EVALUATION.md` v10, "Decisions left for preregistration".

**Workaround:** None. Strict stays until the decision.

**Consequence:** Decision at preregistration, frozen with the prompt version, rate reported both ways.

**Follow-up:** Decide at preregistration.

---

### 2026-10-04 - Session summary (session 7)

**Goal:** Part A, labeling-facing work: C-009 timings, a label summary, the save-on-quit fix, a calibration pass, and progress counts; checkpoint. Then Part B, experimental changes: `tax-v0.2`, `pr-v0.2`, a new synthetic set version, brand assets, and the benchmark rerun.

**Completed:**
- **Part A (committed as `acd5823`).** C-009 timings entered (typical week 3.8 min, busy week 17.5 min, re-reads, reading only); the label summary and a provisional accrual estimate (26.0% consequential, about 6 weeks at the mean rate); `q` at `Save?` saves; calibration pass and `lg-v0.3`; `afterword.label_records` behind `label status`, the terminal's closing line, and the UI badge.
- **Between the checkpoint and Part B.** Stage 0 gate: continue as planned (author), C-012 added, and the volume split as a secondary analysis. Class-by-grade cross-tab and oracle ceiling (`pp-v0.1` would collapse 27 of 150 with perfect classes; 39 of 39 consequential surfaced). The flaky test did not recur in 65 runs; tracked. Post-order split in status and summaries.
- **B1, `tax-v0.2`.** No class changes. Self-promotion is spam when promotion is the primary function, with the extension and opportunity boundary. `CONTAINS_CODE` and `CONTAINS_LINK` are structural, from normalization, read-only in both tools. `REFERENCES_SPECIFIC_CLAIM` stays post-only, with the exact-claim test (the author's decision). `tax-v0.1` labels stay valid: deterministic code and link flags for every label, and `tax-v0.1` RSC is reported apart.
- **B2, `pr-v0.2`.** Code and link are out of the prompt and schema; B1 and B2 get the same structural flags; a test confirms `pr-v0.1` cache entries are not reused. `EVALUATION.md` flag precision updated.
- **B3.** `synthetic-bench-v2.jsonl`: the 30 cases unchanged, plus 5 `tax-v0.2` boundary cases; manifest updated; old file kept.
- **B4.** The dark wordmark was already wired in by the author; the "Aw" mark, found as favicon exports, is inlined as the label UI's favicon; `BRAND.md` v2.
- **B5.** The benchmark comparison, the flag shift, the timeout analysis, and the duplicate-flag decision, written up; no model chosen.
- **Checks:** ruff, format, mypy, pydoclint, 625 tests on 3.14 and on 3.12 (isolated), identity scan 0 disallowed.

**Friction discovered:**
- Session summaries carried stale open items.
- Batch records did not name the tool.
- `q` at `Save?` lost labels (fixed).
- The edit scripts wrote CRLF.
- The shell tool mangled escapes in heredocs.
- One unexplained test failure.
- The terminal flag menu was renumbered by `tax-v0.2`.
- Brand assets arrived under other names.
- Qwen's timeout.
- More duplicate flags.

**Delight discovered:** Recomputing the 2026-10-03 counts from the old reports reproduced them exactly, so the new comparison is like for like. The oracle ceiling showed in one table that, on these labels, reduction rather than recall is what `pp-v0.1` limits.

**Claims affected:** C-009 (measured, mixed; gate decided: continue). C-012 added. C-010: early labels agree on the consequential binary in 140 of 147.

**ADRs affected:** None. ADR-007 is the reason flags can only raise tiers; the candidate designs keep to it.

**Scope pressure:**
- **Changing the policy or prompt** after the flag shift: declined. Two designs recorded for `dev`.
- **De-duplicating flags now:** declined; left for preregistration.
- **Raising the Ollama timeout or switching to streaming:** not done; cause not established.
- **Choosing a model:** declined, as instructed.
- **Approving the dark-mode brand colors:** left to the author.
- **Editing `docs/LABELING-AT-SCALE.md`:** the working tree has the author's own calibration-exercise revision; left untouched.

**Open for the author:**
- Commit this session.
- Label with `--posts random --seed N`.
- A calibration pass on early labels under `tax-v0.2`.
- The Ollama log check and adv-102 rerun.
- Brand: monochrome wordmark, dark mark, master or SVG files, `site.webmanifest` names, and the dark colors' approval.
- Still open: the `intended` labels in the synthetic sets.

**Next smallest useful step:** Commit, then label the next `dev` batch with `afterword label-ui --run <run-id> --posts random --seed N`.
