# Friction log: session 3

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md). Moved here verbatim from `docs/FRICTION-LOG.md` on 2026-10-04 (session 6).

## Session 3: probe progress, timing validity, workflow, service layer (2026-10-03)

Curated from the raw session notes. Times are UTC. No comment text, names, or handles.

### 2026-10-03 05:00 - A practice timing run was nearly recorded as evidence

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Time the chronological review of the typical week (2026-09-21) for C-009.

**Expectation:** Every record written by `--mode chronological` is a measurement.

**Observation:** The tool wrote a timing record for a practice run: 7 comments in 5.3 seconds, under a second per comment. Nothing in the record or the tool marked it as practice, so it sat in `reports/timing/` beside where valid timings would go and could have been reported as the typical week's review time. The 2026-09-21 week has now been re-read twice since its comments first arrived, once in that practice run.

**Evidence:** The author's description of the run. The record was deleted without being opened (`reports/timing/chronological-2026-09-21-20261002T234726Z.json`).

**Workaround:** Chronological mode now asks `Record this as a valid timing? (y/n)` at the end, warning first when the average is under 2 seconds per comment or the review stopped early. Only `y` writes to `reports/timing/`; anything else (including `q`, end of input, or an interrupt) writes to `reports/timing/practice/`. Records carry `valid` and `seconds_per_comment`. `timing.load_valid` counts only top-level records with `"valid": true`, so practice records and older records without the field are ignored.

**Consequence:** Any valid timing of 2026-09-21 is now a third read, a weaker lower bound than intended. `docs/WORKFLOW.md` asks that each report of a historical week's timing state how many times it had been read, and `EVALUATION.md` says the same.

**Follow-up:** The author decides whether to time 2026-09-21 anyway or choose another typical week.

### 2026-10-03 05:05 - No report read timing records

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Make the baseline and C-009 reporting ignore practice records.

**Expectation:** An existing reader to filter.

**Observation:** Nothing read `reports/timing/`. The baseline reported volume only, and review time would have been copied into CLAIMS.md by hand from whatever file was there.

**Evidence:** `grep` for the timing directory across `src/`.

**Workaround:** The baseline report gained a "Chronological review time (C-009)" section, built from `timing.load_valid` only, with the number of practice or unconfirmed records ignored. Per-comment IDs stay in the timing records and never reach the report. `afterword baseline` prints both counts.

**Consequence:** C-009's review time has one sanctioned source, and it cannot include practice.

**Follow-up:** None.

### 2026-10-03 05:10 - The probe console must work both in a terminal and captured

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** A single updating status line for the probe (requests sent, article N of total, 429 waits with a countdown), plus start, end, and elapsed times.

**Expectation:** Redraw one line with carriage returns.

**Observation:** The author runs the probe through Claude Code's `!` prefix, which captures output rather than giving it a terminal. Redrawing on every request and every countdown second would put hundreds of overwritten lines into the captured transcript.

**Evidence:** Design reasoning; `tests/test_progress.py` covers both modes.

**Workaround:** `afterword.progress.StatusLine` redraws in place only on a terminal. When captured, it prints a plain line at each phase change, every 25 articles, and once per wait. The client reports each request (retries included) and hands each retry delay to the status line, which counts it down; neither callback sees the key or the request path. Lines hold counts and times only. The `--article` scope is printed as `article:unresolved` until resolved, and a limitation from the by-path lookup shows the path template, so the author's handle never reaches the console.

**Consequence:** The console remains safe to share in both modes.

**Follow-up:** None.

### 2026-10-03 05:15 - The identity scan caught the author's handle in a README URL

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Add a Quick start to the README.

**Expectation:** A clone URL is harmless.

**Observation:** The assistant wrote the repository's real clone URL, which contains the author's handle. The identity scan reported it as a violation in `README.md` (1 author term).

**Evidence:** `scripts/check_committable.py`, counts only.

**Workaround:** The Quick start uses `git clone <repository-url>`. The scan reports 0 disallowed matches.

**Consequence:** The scanner works as intended on new prose. The README cannot name the repository's own URL under the current rule.

**Follow-up:** The author decides whether the README should carry the URL (which would add README to the files allowed to hold author identity).

### 2026-10-03 05:20 - ADR-012 arrived mid-session and applied to this session's changes

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Probe progress, timing validity, and the baseline review-time section, all of which change the three existing commands.

**Expectation:** Changes inside the existing CLI functions.

**Observation:** `adr/ADR-012-application-service-layer-single-entry-point.md` was added and staged during the session (Accepted). It says existing commands move behind service functions "when they are next changed substantively", and this session changes all three. Its file name first used a four-digit number while the other ADRs use three and its own heading says ADR-012; the author has since renamed it to the three-digit form.

**Evidence:** `git status` showed the file as added; the orientation listing did not include it.

**Workaround:** Added `src/afterword/service.py` with typed functions (`run_probe`, `build_baseline`, `open_for_labeling`, `time_week`, `label_batch`, `labelable_ids`). They raise `ServiceError` with printable messages and suggested exit codes. `cli.py` now only parses arguments, calls the service, and formats output; it no longer imports the adapter. Existing CLI tests pass unchanged.

**Consequence:** The CLI is a transport, per ADR-012. Reading saved runs and writing reports now happen in one place.

**Follow-up:** None (renamed by the author).

### 2026-10-03 05:25 - Escapes again: a shell heredoc turned `\n` into newlines

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Apply an edit to `labeling.py` through a Python script in a shell heredoc.

**Expectation:** `"\\n"` in the script reaches the file as the two characters of an escape.

**Observation:** The text matched for replacement held real newlines, so the replacement failed its own check and wrote nothing.

**Evidence:** The script's assertion output.

**Workaround:** Patch scripts are written to files in the scratchpad and build escapes from a variable. No file was changed by the failed attempt.

**Consequence:** None. The session 2 finding (escapes written by the assistant can arrive as the characters themselves) still holds for heredocs.

**Follow-up:** None.

### 2026-10-03 05:30 - `--set test` cannot select test comments yet

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Write the prospective-period routine in `docs/WORKFLOW.md`.

**Expectation:** `afterword label --set test` labels the week's test comments.

**Observation:** `--set` only sets the label field. The batch is still every unlabeled comment from others in the run, so it would include `dev` comments and comments on posts published before preregistration, which belong to neither set.

**Evidence:** `labeling.run_labeling` builds its queue from `Snapshot.subjects()` with no set filter.

**Workaround:** WORKFLOW.md says `--set test` must not be used until the tool can restrict a batch to posts published after the preregistration commit.

**Consequence:** A tool change is needed before preregistration (Stage 3b).

**Follow-up:** Add test-set selection before the preregistration commit.

### 2026-10-03 05:35 - pydoclint does not see a raise inside a helper

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Document `ServiceError` on the service functions that load a saved run.

**Expectation:** `:raises:` is accepted when a private helper raises.

**Observation:** DOC502: a "Raises" section with no `raise` in the body.

**Evidence:** `uv run pydoclint src scripts`.

**Workaround:** The helper returns the problem as text, and each public function raises the error itself. Callers see the raise where the docstring says it is.

**Consequence:** None.

**Follow-up:** None.

### 2026-10-03 05:40 - External interface direction recorded, out of scope

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record the author's decision on external interfaces (added mid-session).

**Expectation:** Doc changes only.

**Observation:** ADR-012 already sets the constraints. The remaining work was to place the direction in SCOPE, ROADMAP, and CLAUDE.md so no session treats an MCP server or HTTP API as in scope.

**Evidence:** `docs/SCOPE.md` v3, `docs/ROADMAP.md` Deferred, `CLAUDE.md` adapter-boundary section.

**Workaround:**
- SCOPE v3 adds "An HTTP API, MCP server, or any external interface" to out-of-scope. Under future candidates it adds the interface itself: a local stdio MCP server first, gated on Stage 3, propagation queries first, then the policy-computed attention queue, read-only first. It also records that person-scoped and semantic-search queries each need their own ADR.
- ROADMAP lists the external interface under Deferred, gated on the Stage 3 result.
- CLAUDE.md adds the thin-transport rule. README lists `docs/adr/` as a directory, not individual ADRs, so it needed no change.

**Consequence:** The service layer built this session is the base any later interface would use. Nothing beyond it was built.

**Follow-up:** ROADMAP Stage 0 still reads "ADR-001 to ADR-011" as a completed checklist item; left as a historical record.

---

### 2026-10-03 - Session summary (session 3)

**Goal:** Make the probe console informative and safe to share, keep practice timings from becoming evidence, and document the operating protocol. Added mid-session: the external interface direction (ADR-012) in SCOPE, ROADMAP, and CLAUDE.md.

**Completed:**
- **Orientation and checks.** The full check list passed at the start (98 tests on 3.14 and 3.12).
- **Probe progress.** `afterword.progress.StatusLine` prints a start time, a single status line (elapsed time, requests sent, article N of total per step, 429 count, and a countdown during each wait), then an end time and elapsed time. It redraws in place on a terminal and prints occasional plain lines when captured. The client gained `on_request` and `backoff_wait` hooks; the probe gained a `progress` hook. Output holds counts and times only. An unresolved `--article` scope and by-path limitations no longer print the author's handle.
- **Practice record deleted** without being opened.
- **Timing validity.** Chronological mode asks `Record this as a valid timing? (y/n)`, warning first when the average is under 2 seconds per comment or the review stopped early. Only `y` writes to `reports/timing/`; everything else goes to `reports/timing/practice/`. New `afterword.timing` module.
- **Baseline.** New "Chronological review time (C-009)" section from confirmed records only, with the count of ignored practice or unconfirmed records. `afterword baseline` prints both counts.
- **Service layer (ADR-012).** New `afterword.service`. `probe`, `baseline`, and `label` call it; `cli.py` no longer imports the adapter.
- **Docs.**
  - README: Quick start, corrected status (the corpus decision is done), `docs/WORKFLOW.md` in the reading order.
  - New `docs/WORKFLOW.md` (v1): fresh probe first, timing before labeling, labeling sessions, the weekly routine of the test period.
  - LABELING-GUIDE and EVALUATION: the validity step.
  - SCOPE v3: external interface out of scope, recorded as a future candidate with its limits.
  - ROADMAP: external interface under Deferred.
  - CLAUDE.md: the thin-transport rule.
- **Checks.** 116 tests pass on 3.14 and 3.12 (isolated). ruff, format, mypy, pydoclint, the identity scan, and the character check on every changed file are clean.

**Friction discovered:**
- A practice run was nearly recorded as evidence, and the week of 2026-09-21 has now been re-read twice.
- Nothing read timing records.
- The status line has to work captured as well as in a terminal.
- The author's handle got into a README URL (caught by the scan).
- ADR-012 arrived mid-session and applied to this session's changes.
- A heredoc mangled escapes.
- `--set test` cannot select test comments yet.
- pydoclint does not follow raises into helpers.

**Delight discovered:** The identity scan caught a handle in new prose on its first pass. The service-layer move kept every existing CLI test passing unchanged.

**Claims affected:** None changed. C-009 review time is still unmeasured; its only sanctioned source is now confirmed timing records.

**ADRs affected:** ADR-012 (new, added by the author) adopted for the three existing commands. No ADR changed.

**Scope pressure:**
- **External interface (MCP server, HTTP API):** out of current scope; recorded as a future candidate gated on Stage 3. Person-scoped and semantic-search queries each need their own ADR.
- **Service-layer refactor:** done only for the commands this session changed, as ADR-012 directs. No new capability.
- **Review-time section in the baseline:** added, because "ignore practice records" needed a reader to exist.
- **Test-set selection for `--set test`:** not built; needed before preregistration.

**Open for the author:**
- Time 2026-09-21 anyway (a third read) or choose another typical week.
- ADR file name: resolved, the author renamed it to `ADR-012-application-service-layer-single-entry-point.md`.
- Whether README may carry the repository URL (it contains your handle; the scan currently forbids it).
- The heading of `friction-delight-logs/session3.md` reads "Session 2 - X October 2026", and `session2.md` has a duplicated "Claude Code session entries" header. Both are left as written.

**Next smallest useful step:** Run a fresh full probe, then time the week of 2026-09-07 (the busy week) before labeling anything in it.

### Session 3, after review

### 2026-10-03 05:50 - A replacement typical week, chosen by rule

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Replace 2026-09-21 as the typical week to time, since it has been re-read twice (follow-up to the 05:00 entry).

**Expectation:** Pick another week by hand.

**Observation:** A hand-picked week would be a choice made by someone who has seen the comments. The baseline now takes `--exclude-week` (repeatable). With it, the report names the complete week closest to the trailing-13-week median, ties going to the most recent week, never one of the excluded weeks. The median is computed over all 13 weeks before exclusion. For run `20261002T171152Z`, excluding 2026-09-21 and 2026-09-07, the result is 2026-07-27 to 2026-08-02 with 7 comments from others, the same count as the median.

**Evidence:** `uv run afterword baseline --run 20261002T171152Z --exclude-week 2026-09-21 --exclude-week 2026-09-07`, date and count only; tests in `tests/test_baseline.py` and `tests/test_timing.py`.

**Workaround:** None needed.

**Consequence:** WORKFLOW.md names the new typical week. CLAIMS.md C-009 has a dated note; the original week choice stays as written. The new week falls in July 2026, the quiet month, but its count equals the median. It has not been re-read in any recorded session.

**Follow-up:** The author times 2026-07-27 and 2026-09-07 from a fresh run, before labeling either.

### 2026-10-03 05:55 - README allowed to hold the author's identity

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Restore the real clone URL in the README (follow-up to the 05:15 entry).

**Expectation:** A one-line change.

**Observation:** The identity scan allowed author identity only in `pyproject.toml` and `NOTICE`, so the URL was a violation.

**Evidence:** `scripts/check_committable.py`, counts only: README now shows 1 author term, allowed.

**Workaround:** At the author's decision, `README.md` joins the files where the author's own terms are allowed. Commenter terms are still enforced in every file, including these three. A commenter term that is a whole word of the author's identity (a shared first name) counts as author identity, so it is also allowed in README now, as it already was in the other two.

**Consequence:** The README carries the clone URL. 0 disallowed matches.

**Follow-up:** None.

### 2026-10-03 06:00 - ADR-012 renamed; staged copy complete

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Remove remaining references to the four-digit ADR name and confirm the staged ADR (follow-up to the 05:20 entry).

**Expectation:** The file named in the author's message.

**Observation:** The author renamed the file to `docs/adr/ADR-012-application-service-layer-single-entry-point.md`, not to the shorter name their message gave. The staged copy holds the full 66 lines, with no unstaged changes. The only remaining references to the old name were in the friction logs. The author's own pasted messages in their session notes also contain it; those are left as written.

**Evidence:** `git status`, `git show :<path>`, `grep` across the repository.

**Workaround:** The log entries now describe the rename instead of naming the old file.

**Consequence:** None.

**Follow-up:** None.

### 2026-10-03 06:00 - Test-set selection is a Stage 3b prerequisite

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record the gap from the 05:30 entry in the roadmap.

**Expectation:** None.

**Observation:** ROADMAP Stage 3b now lists, before preregistration can happen: `afterword label --set test` selects only test-set comments (posts published after preregistration).

**Evidence:** `docs/ROADMAP.md`.

**Workaround:** None needed.

**Consequence:** Preregistration cannot happen before this is built.

**Follow-up:** Build it in Stage 3b.

---

### 2026-10-03 - Session summary addendum (after the author's review)

**Decisions recorded:**
- ADR-012 file renamed by the author to the three-digit form.
- README may hold the author's identity (clone URL). Commenter terms remain blocked everywhere.
- Test-set selection for `--set test` is a Stage 3b prerequisite.
- The typical week to time is replaced by rule: 2026-07-27 to 2026-08-02 (7 comments from others) replaces 2026-09-21.

**Completed:**
- Friction-log references to the old ADR file name replaced with a description of the rename.
- `scripts/check_committable.py` allows README; README uses the real clone URL.
- ROADMAP Stage 3b prerequisite.
- `afterword baseline --exclude-week` and a "Replacement typical week" line in the report; WORKFLOW.md and a dated C-009 note in CLAIMS.md updated.
- Full check list rerun.

**Next smallest useful step:** Run a fresh full probe, then time the weeks of 2026-07-27 and 2026-09-07 before labeling anything in them.

---

