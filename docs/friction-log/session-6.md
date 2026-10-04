# Friction log: session 6

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 6: documentation housekeeping (2026-10-04)

Curated from the raw session notes. Times are UTC. No comment text, names, or handles. Documentation, repository hygiene, and investigation only: no taxonomy, prompt, policy, heuristic, or normalization version changed, and no application behavior changed.

### 2026-10-04 00:52 - Line endings: 45 working files were CRLF, not 11

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Pin every text file to LF and convert the working files (follow-up to the session 4 entry "Line-ending conversion would change fixture hashes").

**Expectation:** Eleven docs with CRLF endings.

**Observation:**
- `git ls-files --eol` showed 45 working-tree files with CRLF: 16 Markdown files (including `README.md`, `CLAUDE.md`, `fixtures/README.md`, `docs/BRAND.md`, and ADR-012 and ADR-013), `.gitignore`, and 28 Python files in `src/`, `scripts/`, and `tests/`.
- Every blob in the index was already LF. The CRLF came from `core.autocrlf=true` at checkout, so the working tree differed from the committed bytes while the history did not.
- `docs/BRAND.md` is in the index as an empty blob (status `AM`), the same shape as the session 4 and 5 findings for ADR-013 and LABELING-AT-SCALE.

**Evidence:** `git ls-files --eol` before and after; `git diff --stat` after conversion shows content changes only in `.gitattributes` and `docs/BRAND.md`; `sha256sum fixtures/corpus/*.jsonl` matches `fixtures/corpus/MANIFEST.md`.

**Workaround:** `.gitattributes` now starts with `* text=auto eol=lf`, keeps the two fixture rules, and marks images, PDFs, and zip files as binary. The 45 files were converted in place by stripping the carriage return at line ends; the index was not touched. Afterwards every working file is LF.

**Consequence:** No committed content changes. The author runs `git add --renormalize .` before committing. That stages `.gitattributes` and, because `docs/BRAND.md` is already in the index, the full text of `BRAND.md`.

**Follow-up:** None.

### 2026-10-04 00:54 - When the terminal labeling tool writes a label

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Investigate, without changing code, why the label integrity check found 4 records from the terminal tool where the author remembers labeling 6 (session 5 entry "Label integrity check: 27 labels, not 29").

**Expectation:** Labels might be held in memory and written at batch end.

**Observation:** From `src/afterword/labeling.py` (current) and the version at `107a22c`, which wrote the 4 records; both behave the same:
- **Each label is written as soon as it is confirmed**, one comment at a time, never at batch end. After the summary line, the `Save? [Enter = yes, r = redo, s = skip]` prompt decides. Any answer other than `r`, `s`, or `q` saves, including a typo. The record is appended to `initial.jsonl` and flushed with `fsync` before the next comment is shown.
- **The batch record:** `batch_start` is written before the first comment. A hard-to-label note is written after its comment's prompts finish, saved or skipped. `batch_end` is written once at the end, with `labeled`, `skipped`, and `ended_by` (`complete` or `quit`).
- **`q` at any prompt, end of input, or Ctrl+C** stops the batch. All three are caught: labels already saved stay, and `batch_end` is written with `ended_by: quit`. The comment on screen is discarded with its answers and its note, **including when `q` is typed at the `Save?` prompt**, where it can read as "save and quit". `r` restarts the same comment and loses nothing.
- **Not caught:** closing the terminal window, Ctrl+Break on Windows, or an unexpected exception. Saved labels stay, but no `batch_end` is written.
- At most one comment is in progress at any moment, so a quit can lose at most one label.

**Evidence:** `LabelBatch.save`, `_append_jsonl`, `label_one`, `run_labeling`, and `Console.ask` in `src/afterword/labeling.py`; `git show 107a22c:src/afterword/labeling.py`. The session 5 counts: the terminal batch has one start and one end, `ended_by: quit`, `labeled: 4`, `skipped: 0`. No label file was opened this session.

**Workaround:** None. Investigation only.

**Consequence:** The tool's own `batch_end` counter (4 saved, 0 skipped) matches the 4 records in the file, so no confirmed label was lost in writing. The quit can account for at most one of the two missing labels, and only if that comment's prompts were answered before `q`. The other is not explained by the write path. Every terminal batch that reaches its first comment writes `batch_start`, and only one terminal batch exists, so it was not a second run either. Plausible remaining causes, none checkable from code: the count remembered, or a comment answered and then discarded with `q` or `r`.

**Follow-up:** For session 7: make `q` at the `Save?` prompt ask "save this label first? (y/n)" (or save, then quit), say plainly on quit that the comment on screen was not saved, and record in `batch_end` whether a comment was abandoned in progress. A tool change with tests; labels already written stay as they are.

### 2026-10-04 00:56 - Friction log split into one file per session

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Move `docs/FRICTION-LOG.md` (about 104 KB) into per-session files without rewording or dropping any entry.

**Expectation:** 83 entries to move.

**Observation:** The file held 83 `###` headings: two in the templates, and 81 entries, session summaries, and summary addenda. Of those, 68 are entries in the template's form. The pre-code material (one CoderLegion observation, one DEV documentation observation, and the v2 scoping summary) had no session number; it went into `session-1.md`, with a line saying so.

**Evidence:** The original lines 1 to 62 plus the session files, minus the four header lines added to each, are byte-identical to the original file (`cmp`).

**Workaround:** Split by line range at the section headings, so no entry text passed through an editor. `docs/FRICTION-LOG.md` is now an index: purpose, a table of session files with the entries to read first, how to add a session, the classification, and both templates.

**Consequence:** CLAUDE.md now sends curated entries to `docs/friction-log/session-N.md`, with a pointer row in the index. The identity scan already covers the new directory (it reads every tracked and untracked, non-ignored file); the character check covers any staged path, so it applies there without change.

**Follow-up:** Two pointers now reach the moved content only through the index: `docs/PRIVACY-AND-BOUNDARIES.md` (model digests "recorded in `docs/FRICTION-LOG.md`") and the module docstring of `src/afterword/providers/ollama.py`. Left as written; the author decides whether to point them at `docs/friction-log/session-4.md`.

### 2026-10-04 00:58 - The roadmap needed "built" kept apart from "gate passed"

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Record the Stage 1 to 3a groundwork in ROADMAP.md.

**Expectation:** Tick the items that exist.

**Observation:** Checking items alone would make Stages 1 to 3a look nearly complete, while no gate after Stage 0's has been evaluated and no model has classified a real comment. The roadmap still read `lg-v0.1` (the guide has been `lg-v0.2` since session 2) and "ADR-001 to ADR-011" (left as a historical record in session 3).

**Evidence:** `docs/ROADMAP.md` v2; `docs/LABELING-GUIDE.md`.

**Workaround:** ROADMAP v3 states that built is not a passed gate. Each checked item carries its date and what it was tested on, and each of Stages 1 and 2 has a "Gate status: not evaluated" line. Stage 3a's adversarial item stays open: the set has run on the synthetic benchmark, but the known pre-check gaps are not fixed. The fixture item is split into the synthetic manifest (done) and the real corpus manifest (at preregistration). Stage 4 gains the explanation warning from the 2026-10-03 benchmark.

**Consequence:** The roadmap and the README status now say the same thing: Stage 0 open for timing and labeling, with the groundwork ahead of it tested on synthetic data only.

**Follow-up:** None.

---

### 2026-10-04 - Session summary (session 6)

**Goal:** Documentation housekeeping, repository hygiene, and one investigation, with no version or behavior change.

**Completed:**
- **Orientation.** The full check list passed at the start: ruff, format, mypy, pydoclint, 492 tests on 3.14 and on 3.12 (isolated), and the identity scan (0 disallowed).
- **Line endings.** `.gitattributes` pins every text file to LF and marks binaries; 45 working files converted; fixture hashes unchanged.
- **Friction log.** Split verbatim into `docs/friction-log/session-1.md` to `session-5.md`, plus this file; `docs/FRICTION-LOG.md` is an index; CLAUDE.md updated.
- **ROADMAP v3.** Built versus gate passed, `lg-v0.2`, ADR-001 to ADR-013, the fixture and manifest items, and the Stage 4 explanation warning.
- **README.** Status line, the stray blank line in the Done list, `docs/BRAND.md` in the reading order, and the friction log entry pointing at the index and `docs/friction-log/`. The single logo image is kept; the `<picture>` markup waits for the dark variant.
- **PROJECT-BRIEF.** Version header only: 3, for the dated revision of success criterion 2.
- **Investigation.** When the terminal labeling tool writes a label (entry above). No code changed.

**Friction discovered:**
- 45 CRLF working files, not 11, and `BRAND.md` staged as an empty blob.
- 83 headings, not 83 entries, in the old log.
- Two pointers that now reach moved content only through the index.
- `q` at the terminal tool's `Save?` prompt discards the comment on screen.

**Delight discovered:** Splitting by line range made the verbatim claim checkable with one `cmp`.

**Claims affected:** None.

**ADRs affected:** None.

**Scope pressure:**
- **Fixing the terminal tool's quit behavior now:** declined. This session is investigation only; the fix is a session 7 item.
- **Rewriting the two indirect pointers:** declined; one is in a signed-off record and one in `src/`. Left for the author.
- **`docs.zip` at the repository root:** untracked and not ignored. It holds a 35-entry snapshot of `docs/`. Not opened, moved, or deleted; the author decides.
- **The README `<picture>` markup:** deferred until the dark wordmark exists, as `BRAND.md` says.

**Open for session 7 (opening items, in order):**
1. **`tax-v0.2`:** clarify that self-promotion is `LIKELY_SPAM_OR_NOISE` when promotion is the primary function, on-topic or not. Make `CONTAINS_CODE` and `CONTAINS_LINK` deterministic from normalization and remove them from the model's output schema (prompt `pr-v0.2`), keeping B1 and B2 parity. Existing `tax-v0.1` labels stay valid.
2. **The terminal tool's quit behavior** (entry above): `q` at `Save?` asks before discarding, the quit message says what was not saved, and `batch_end` records an abandoned comment.
3. **BRAND assets:** the dark wordmark, the monochrome wordmark, and the "Aw" mark, then the README `<picture>` markup.

**Open for the author:**
- Before committing: `git add --renormalize .` (then stage the new and changed files as usual).
- `docs.zip` at the repository root, and the two indirect pointers above.
- Still open from earlier sessions: `dev` labeling (27 of 438), the two chronological timings, and a review of the `intended` labels in the synthetic sets.

**Next smallest useful step:** Commit this session, then label the next `dev` batch with `afterword label-ui`.
