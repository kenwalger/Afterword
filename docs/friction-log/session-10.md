# Friction log: session 10

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 10: pre-publication fixes (2026-10-08)

Four fixes before the repository is linked from an article: saved-run redaction and retention (ADR-009), a plain-language baseline console, read-only store commands that create nothing, and the README's "How this was built" note. The labeling tools were not touched. No comment text, names, or handles below; the real store and saved runs were not modified in this session (the author runs `ingest`).

### 2026-10-08 - Saved runs are redacted, never deleted; a retention rule bounds how long they keep text

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Close the gap recorded in session 9 ("The deletion purge does not reach saved probe runs"): make ADR-009's "purged from local storage" true of the raw runs under `fixtures/dev-api/source/real/`, and add a retention rule.

**Expectation:** A redaction step at ingest, inside the DEV adapter (the payload field names must not leave it, ADR-001), plus documentation changes.

**Observation:**
- A deleted comment appears in up to three places per run: the post's comment tree and, for the largest thread only, the probe's unauthenticated fetch of the same tree and its single-comment fetch. The redaction walks every payload file of every run rather than relying on file names.
- Marking a redacted node needed care. Removing `user` and the body alone would make the node an "unexpected shape" (ADR-009) the next time the run is loaded, so a reload would report a limitation for every redaction. Each redacted node instead carries an explicit marker; a node redacted as deleted loads as a deletion placeholder (thread structure only), and a node reduced by retention loads as a comment with no text.
- The single-comment endpoint in the test fake did not follow the thread when a comment became a placeholder, so the first idempotency test saw a "new" redaction on every ingest. The fake now changes both, as DEV does.
- Retention as first specified (runs older than the newest 3 are reduced) would have reduced, within two more probes, the run all 302 `dev` labels were made from, and with it the context the calibration and self-agreement passes need. The rule keeps such runs whole (still redacted for deletions) and reports them. It also never reduces a run newer than the one being ingested, which might still need ingesting.
- The retained structure keeps each comment's numeric author ID and each post's `comments_count`, so a reduced run gives the same baseline counts as before. The C-009 baseline run is old enough to be reduced at the next ingest; its counts stay reproducible, its text does not.

**Evidence:** `src/afterword/adapters/dev/redact.py`, `afterword.service.redact_saved_runs`, `tests/test_redact.py` (17 tests: absence and placeholder paths, idempotency, reloading, retention, the label exemption, the newer-run exemption, a reduced comment deleted later, the option's bounds, CLI output).

**Workaround:** None needed.

**Consequence:** ADR-009 amended (2026-10-08, still provisional). `PRIVACY-AND-BOUNDARIES.md` v9, `USING-AFTERWORD-ON-YOUR-ACCOUNT.md` v2, `DATA-MODEL.md` v13, `COMMANDS.md` v2, and `WORKFLOW.md` v6 updated. The pre-commit identity scan reads names from saved runs, so reduced runs no longer feed it; the newest runs and any run kept for labels still do.

**Follow-up:** For the author: the next real `ingest` will reduce the older saved runs (all but the newest three and the run labels were made from). It is one-way. If any older run should keep its text, ingest with a larger `--keep-runs` first.

### 2026-10-08 - Baseline console in plain language; one "Weeks to time" block per distinct window

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Make the `baseline` console readable for a stranger (session 9, smaller findings, item 4).

**Expectation:** Rewording only.

**Observation:** The duplicated block came from the report computing "weeks to time" for the 52-week and the 13-week windows separately; with 13 complete weeks of history or fewer they are the same weeks. The report now lists each distinct window once. The console now prints plain-language headings, one explanation line per figure, and no claim IDs or project terms; it no longer mentions practice timing records. The written report under `reports/` keeps its claim references.

**Evidence:** `afterword.baseline.console_summary`, `tests/test_baseline.py`, `tests/test_timing.py`.

**Workaround:** None.

**Consequence:** The baseline JSON's `weeks_to_time` list has one entry instead of two when the windows coincide.

**Follow-up:** None.

### 2026-10-08 - Read-only store commands no longer create a database

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Session 9, smaller findings, item 3.

**Expectation:** As stated.

**Observation:** `connections`, `store-status`, and `forget` (with or without `--yes`) now open the store only if it exists. Without one they print that there is no local database yet and exit 0; nothing is created. Every other store command is unchanged.

**Evidence:** `afterword.service.open_existing_store`, `NoStoreError`; `tests/test_redact.py`.

**Workaround:** None.

**Consequence:** None for the experiment.

**Follow-up:** None.

### 2026-10-08 - Session summary

**Goal:** Pre-publication fixes: saved-run purge and retention, baseline console for strangers, read-only store commands, and the README's "How this was built" note.

**Completed:** all four. ADR-009 and every document that describes deletion now agree with the code. 17 new tests for redaction, retention, and the store commands, plus baseline console tests.

**Friction discovered:** the retention rule as first specified would have reduced the labeled run; redacted nodes needed an explicit marker to avoid reading as unexpected shapes.

**Delight discovered:** the retained structure keeps the baseline reproducible from a reduced run.

**Claims affected:** none.

**ADRs affected:** ADR-009, amended 2026-10-08 (saved runs and retention), still provisional.

**Scope pressure:** refusing to label from a reduced run would belong in the labeling tools, which were out of bounds this session; documented in `WORKFLOW.md` instead.

**Next smallest useful step:** the author decides whether the older saved runs may be reduced at the next ingest, then ingests.
