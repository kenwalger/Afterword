# Friction log: session 9

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 9: public readiness (2026-10-08)

Documentation and repository presentation only, for a stranger arriving from a DEV article. No behavior changed, and the labeling tools were not touched (the author was labeling in parallel). No comment text, names, or handles below.

### 2026-10-08 - The deletion purge does not reach saved probe runs

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Write the privacy statement for other authors (`docs/USING-AFTERWORD-ON-YOUR-ACCOUNT.md`), including what happens when a commenter deletes a comment.

**Expectation:** ADR-009 and `PRIVACY-AND-BOUNDARIES.md` ("Retention and deletion") say a deleted comment's "body text and raw payloads are purged from local storage, including from corpus files, at the next sync."

**Observation:** The purge runs on ingest and covers the store only: `raw_payload` in `source_records` is set to null and the comment's classifications are purged. The raw responses of earlier probe runs, under `fixtures/dev-api/source/real/<run-id>/`, are files on disk that nothing rewrites, so a run saved before the deletion still holds the comment. No corpus files exist yet (`fixtures/corpus/v*/` is planned).

**Evidence:** `afterword.service` (ingest purge) and `afterword.sqlite_store` (`purge_source_records`, `purge_classifications`); no code removes or rewrites a saved run directory.

**Workaround:** The statement describes the behavior as it is, and tells the reader to delete probe runs they no longer need. No code or ADR changed in this session.

**Consequence:** A gap between ADR-009's wording and the code, for raw probe runs. Whether "local storage" was meant to include saved runs is the author's call.

**Follow-up:** For the author: either amend ADR-009 to say saved probe runs are excluded (and keep the advice to delete old runs), or add a step that purges deleted comments from saved runs, or retires runs once ingested.

### 2026-10-08 - Fresh clone: everything passes, nothing assumes the author's machine

**Platform:** Project

**Type:** DELIGHT

**Class:** ENVIRONMENT

**Task:** Clone from the local path into a temporary directory, run `uv sync` and the full check list, and walk the "Try it" steps as far as possible without a DEV key.

**Expectation:** Something would assume the author's paths, account, or Windows.

**Observation:**
- `uv sync`, ruff, ruff format, mypy, and pydoclint are clean; 662 tests pass on Python 3.14 and on 3.12 (isolated).
- No path, account name, or Windows-only assumption in the code. The probe finds the content author from the key (`/api/users/me`, then `/api/articles/me/published`), so it works for any account. `.gitattributes` keeps every text file LF on every platform.
- Without a key: `probe` exits 2 with `DEV_API_KEY is not set`; with no `.env`, uv's own error names the missing file; with an empty `DEV_API_KEY=` line, the same "not set" message. With a key DEV refuses (simulated), the run is `FAILED` with `/api/users/me returned 401`, exit 1.
- With DEV mocked by the test suite's fake (3 synthetic posts), `probe` then `baseline` complete as the README describes: 14 requests, a `COMPLETE` run, and the report under `reports/`.

**Evidence:** The fresh-clone run in this session; `tests/conftest.py` (`FakeDev`).

**Workaround:** None needed.

**Consequence:** The "Try it" steps hold for another account, as far as can be checked without one.

**Follow-up:** The next entry lists the smaller findings.

### 2026-10-08 - Fresh clone: smaller findings

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** As above.

**Expectation:** As above.

**Observation:**
1. The old README's check list chained commands with `&&`, which Windows PowerShell 5.1 rejects. The new README lists one command per line, as `CLAUDE.md` already did.
2. In a fresh clone the identity scan reads no raw runs, so only the email checks apply (it warns). Expected, since contributors have no real data, but it means the scan protects only the author's own machine fully.
3. `store-status`, `connections`, and `forget` create an empty `data/afterword.sqlite3` when no store exists, although they only read. Not on the "Try it" path.
4. The baseline console output and report use the experiment's internal vocabulary (C-009, "valid review timings", "Weeks to time"), which a stranger running the "Try it" steps will see. With a short history the "Weeks to time" block prints the same basis twice.
5. The only PowerShell-specific guidance in the docs was implicit: how to keep a machine awake during long runs (`WORKFLOW.md`) named no command for any platform. Commands for Windows, macOS, and Linux are added. Every `afterword` command is the same on all three.

**Evidence:** The fresh-clone run; `README.md` before this session.

**Workaround:** 1 and 5 fixed in the docs. 2 to 4 are behavior, out of scope for a documentation session, and left as they are.

**Consequence:** None for the experiment.

**Follow-up:** For the author: whether 3 and 4 are worth changing before the article goes out.

### 2026-10-08 - Session summary

**Goal:** Make the repository readable for a writer arriving from a DEV article, without changing behavior.

**Completed:**
- `README.md` rewritten as a front door: what Afterword is and its boundary, what it has found so far (linking the dev-set evaluation), "Try it on your own account" (read-only, no model), status and expectations, contributors, and a short reading order.
- `docs/USING-AFTERWORD-ON-YOUR-ACCOUNT.md`: the statement `PRIVACY-AND-BOUNDARIES.md` requires before another author uses Afterword (what is collected, where it is stored, what is sent to a model, what the tool can and cannot do, the key, and deletion). `PRIVACY-AND-BOUNDARIES.md` v8 points to it.
- `docs/COMMANDS.md` (the full command reference, moved from the README), `docs/README.md` (the full reading order, moved from the README), and the README's status log moved into `ROADMAP.md` (v9). Nothing dropped.
- `WORKFLOW.md` v5: keep-awake commands for Windows, macOS, and Linux.
- Fresh-clone check, identity scan, and text checks across every tracked file (all clean).

**Friction discovered:** the deletion purge does not reach saved probe runs; the smaller fresh-clone findings above.

**Delight discovered:** a fresh clone passes everything, and nothing in the code assumes the author's machine or account.

**Claims affected:** none.

**ADRs affected:** none changed. ADR-009's wording and the code differ for saved probe runs (first entry), for the author to decide.

**Scope pressure:** fixing the empty store created by read-only commands and the baseline report's wording for strangers (behavior changes, deferred); a "How this was built" note (drafted for the author, not added).

**Next smallest useful step:** the author's decision on saved probe runs and ADR-009, then the pull request policy line in the README.
