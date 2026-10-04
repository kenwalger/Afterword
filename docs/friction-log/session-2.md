# Friction log: session 2

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md). Moved here verbatim from `docs/FRICTION-LOG.md` on 2026-10-04 (session 6).

## Session 2: housekeeping, corpus proposal, code standards, labeling tool (2026-10-02)

Curated from the raw session notes. Times are UTC. Evidence lives in git-ignored reports; run IDs are cited.

### 2026-10-02 22:15 - The license NOTICE trips the identity scan

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Add LICENSE and NOTICE, then run the identity scan.

**Expectation:** 0 disallowed matches.

**Observation:** NOTICE must name the copyright holder. The scanner allowed the author's identity only in `pyproject.toml`.

**Evidence:** `scripts/check_committable.py`, counts only.

**Workaround:** NOTICE joins `pyproject.toml` as a file allowed to hold the author's identity. Other commenters' terms are still enforced in both.

**Consequence:** A rule set in session 1 was widened, pending the author's confirmation.

**Follow-up:** Author confirms.

### 2026-10-02 22:30 - Article list items carry no edit time

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Decide when the labeling tool records `context_reconstructed: false` because the post was edited after the comment.

**Expectation:** `edited_at` on every post in a full run.

**Observation:** `/api/articles/me/published` items have no `edited_at`. Only a single-article fetch does, and the full probe makes one.

**Evidence:** `shapes.json`, run `20261002T171152Z`, `article_list_item` versus `article`.

**Workaround:** The condition applies only when the edit time is known. `context_reconstructed: true` means "no known gap" (`LABELING-GUIDE.md`, `lg-v0.2`).

**Consequence:** For most posts the condition cannot be checked. The post body is not shown while labeling, so the effect is limited to title edits.

**Follow-up:** Stage 1 may fetch posts singly if post edits matter.

### 2026-10-02 22:35 - Comments arrive in the first week after a post

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Size a prospective test set for the corpus proposal.

**Expectation:** A long tail of comments on old posts.

**Observation:** 392 of 432 comments from others (90.7%) arrived within 7 days of the post, and 94.6% in the trailing 13 weeks. 39 of the 94 posts published since March have no comments from others.

**Evidence:** `post_age_at_comment_from_others` in the baseline for run `20261002T171152Z`.

**Workaround:** None needed.

**Consequence:** A prospective test set restricted to posts published after preregistration stays post-disjoint from `dev` at a cost of about 5% of volume. Volume depends on continued publishing.

**Follow-up:** `docs/proposals/2026-10-02-corpus-targets.md`.

### 2026-10-02 22:40 - Strict mypy found a latent bug in the probe

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Bring existing code into compliance with the new code standards.

**Expectation:** Annotation-only changes.

**Observation:** `Probe._subtree_ids` could add `None` to its ID set when a descendant had no ID. Every later top-level comment (parent `None`) would then count as part of the subtree, and the single-comment fetch check would report a false mismatch. All 707 real comments have IDs, so no result was affected. The other eight mypy errors needed annotations only.

**Evidence:** `uv run mypy`; regression test `test_subtree_ignores_nodes_without_an_id`.

**Workaround:** Nodes without an ID are never added.

**Consequence:** One real fix. Strict typing earns its place on adapter code that walks untrusted trees.

**Follow-up:** None.

### 2026-10-02 22:42 - No configured linter enforces module-level annotations

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Enforce type hints on module-level variables by tooling.

**Expectation:** A ruff or mypy rule.

**Observation:** ruff ANN covers functions only, and mypy strict infers module variable types.

**Evidence:** 50 unannotated module-level assignments that passed both.

**Workaround:** `tests/test_code_standards.py` fails on any unannotated module-level assignment in `src/` or `scripts/`.

**Consequence:** Enforced by pytest rather than the pre-commit hook.

**Follow-up:** None.

### 2026-10-02 22:55 - Invisible bidi characters written into a test

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Test that display rendering strips terminal and bidi control characters.

**Expectation:** Escapes in the test source.

**Observation:** The file held literal U+202E and U+202C characters, invisible in most editors.

**Evidence:** `ascii()` of the test lines.

**Workaround:** Replaced with escapes. A scan of every committable file found no bidi controls or em-dashes.

**Consequence:** None remaining. Comment text is untrusted (ADR-008), and the display renderer strips these characters before anything reaches the terminal.

**Follow-up:** Consider a bidi check in the pre-commit hook.

### 2026-10-02 23:00 - `uv run --python` rebuilds the project venv

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Run the test suite on Python 3.14 and 3.12.

**Expectation:** A plain `uv run pytest` uses 3.14 after a 3.12 run.

**Observation:** `--python 3.12` replaced the venv, so the next plain run was also 3.12.

**Evidence:** `uv run python --version` printed 3.12.4.

**Workaround:** Both checks name the interpreter, with 3.14 run last (CLAUDE.md). 88 tests pass on 3.14.5 and 3.12.4.

**Consequence:** A two-version claim needs explicit interpreters to be checkable.

**Follow-up:** None.

---

### 2026-10-02 - Session summary (session 2)

**Goal:** Housekeeping, a corpus-targets proposal for the author's decision, code standards enforced by tooling, and a local labeling tool.

**Completed:**
- Apache-2.0 LICENSE and NOTICE; package metadata.
- README status and license; CLAUDE.md stage, code standards, check list.
- Pre-commit hook (`git config core.hooksPath scripts/hooks`) running the identity scan and static checks.
- Identity extraction moved into the DEV adapter.
- Baseline calendar months and post age at comment.
- `docs/proposals/2026-10-02-corpus-targets.md`.
- ruff ANN and D, mypy strict, pydoclint, with all existing code compliant and one latent bug fixed.
- `afterword label`: one batch of at most 40 at a time, resumable, thread context as of each comment, and a chronological timing mode. Built and tested on synthetic fixtures only.
- Label schema gained `snapshot_run_id`, `batch_id`, `duration_seconds` (`fixtures/README.md`, DATA-MODEL v4). The labeling guide is `lg-v0.2` (context reconstruction; parent edits undetectable).

**Friction discovered:**
- NOTICE versus the identity scan.
- No edit time on article list items.
- No linter for module-level annotations.
- Literal bidi characters.
- `--python` rebuilds the venv.

**Delight discovered:** Comments cluster in a post's first week, which makes a post-disjoint prospective test set cheap.

**Claims affected:** None changed. New aggregate views of run `20261002T171152Z` (calendar months, post age) leave C-009's figures as they were.

**ADRs affected:** None changed. Option 2 of the corpus proposal would require an ADR-010 amendment.

**Scope pressure:**
- **Commenter names in the labeling view:** replaced by per-thread pseudonyms.
- **Revealing later replies for the retrospective grade:** not built, because it would leak hindsight into later prospective grades in the same post.
- **Per-post fetches for `edited_at`:** deferred to Stage 1.
- **pytest in the pre-commit hook:** not added, for speed.

**Open questions (recorded, not decided):**
- Corpus targets: Option 1 or Option 2 (proposal open).
- NOTICE as a second file allowed to hold the author's identity.

**Next session:**
1. Apply the corpus decision.
2. Run a fresh full probe, then time the chronological reviews of the weeks of 2026-09-21 and 2026-09-07.
3. Label the historical comments.
4. Recompute the proposal's sizing from the observed consequential share.

---

### Session 2, after review

### 2026-10-02 23:10 - `uv run --isolated` tests 3.12 without touching the project venv

**Platform:** Project

**Type:** DELIGHT

**Class:** ENVIRONMENT

**Task:** Find a 3.12 test command that does not rebuild the project venv (follow-up to the 23:00 entry).

**Expectation:** Unknown.

**Observation:** `uv run --isolated --python 3.12 pytest` ran the suite on 3.12.4 in a temporary environment. Afterwards the project venv still reported 3.14.5, and its `pyvenv.cfg` modification time was unchanged.

**Evidence:** `uv run python --version` and `pyvenv.cfg` timestamps before and after.

**Workaround:** CLAUDE.md check 6 and the README now use `--isolated`. Check 5 is a plain `uv run pytest` again.

**Consequence:** The two-version claim no longer depends on command order.

**Follow-up:** None.

### 2026-10-02 23:15 - Corpus decision applied: prospective test set

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Apply the author's decision (Option 2, amended) to ADR-010 and EVALUATION.md.

**Expectation:** Changes confined to those two files.

**Observation:** The old split names (`test-natural`, `test-enriched`, "test sets first") also appeared in ROADMAP, DATA-MODEL (`corpus_set` values), LABELING-GUIDE, SCOPE, CLAIMS (C-002, C-008), and `fixtures/README.md`. `PROJECT-BRIEF.md` success criterion 2 says the corpus is split into development and sealed test sets "before classifier tuning". Under a prospective test set that is no longer literally true.

**Evidence:** `grep` for the old set names after the ADR and EVALUATION rewrite.

**Workaround:** Updated ROADMAP (Stage 0 items, Stage 3b and 3c), DATA-MODEL `corpus_set`, LABELING-GUIDE blinding and self-agreement lines, SCOPE, and `fixtures/README.md`. Appended dated notes to C-002 and C-008, leaving the original text. Left PROJECT-BRIEF unchanged: it is a success criterion, so the author decides.

**Consequence:** The labeling tool's default `corpus_set` is now `dev`; prospective labels must pass `--set test`.

**Follow-up:** Author decides whether to revise PROJECT-BRIEF success criterion 2.

### 2026-10-02 23:20 - Every post fetched singly in a full run

**Platform:** DEV

**Type:** FRICTION

**Class:** PRODUCT

**Task:** Make `edited_at` known for every post, so `context_reconstructed` can use it (follow-up to the 22:30 entry).

**Expectation:** One extra request per post.

**Observation:** As expected. A full run now sends about 138 more requests, about 2.3 more minutes at 1 request per second, with more exposure to 429s. Adapter version `dev-probe-0.2`.

**Evidence:** `article_fetch` findings (`articles_requested`, `articles_fetched`, `statuses`, `edited_at_present`); test `test_full_probe_fetches_every_article`.

**Workaround:** A failed detail fetch is recorded as a run limitation (the run becomes `PARTIAL`), not a failure.

**Consequence:** Labeling from a `dev-probe-0.2` full run checks post edits for every post. Runs from before then check only the posts they have.

**Follow-up:** The author runs a fresh full probe before labeling.

---

### 2026-10-02 - Session summary addendum (after the author's review)

**Decisions recorded:**
- NOTICE confirmed as the second file allowed to hold the author's identity.
- `lg-v0.2`, DATA-MODEL v4, and the single combined commit accepted.
- Corpus targets: Option 2 with amendments. ADR-010 amended, EVALUATION.md v3, proposal moved to `docs/proposals/accepted/`.

**Completed:**
- ADR-010 and EVALUATION.md rewritten as complete files:
  - `dev` is the full historical corpus.
  - `test` is comments from others on posts published after the preregistration commit, labeled weekly before any shadow-mode output is revealed.
  - Stopping rule: 20 consequential comments or 16 weeks.
  - The accrual estimate is recomputed and recorded before preregistration.
  - Publishing cadence is listed as a risk.
- Downstream references updated: ROADMAP, DATA-MODEL, LABELING-GUIDE, SCOPE, `fixtures/README.md`, and dated notes on C-002 and C-008.
- `replied_before_labeling` derived by the tool (the author's direct reply exists in the snapshot), added to the label schema and EvaluationLabel.
- Full probe runs fetch every post singly (`dev-probe-0.2`), so `context_reconstructed` uses every post's edit time.
- README documents the per-clone hook setup. CLAUDE.md check 6 is `uv run --isolated --python 3.12 pytest`.
- Full check list rerun: ruff, format, mypy, pydoclint, pytest on 3.14 and 3.12 (isolated), and the identity scan.

**Open for the author:**
- `PROJECT-BRIEF.md` success criterion 2 ("split into development and sealed test sets, before classifier tuning") no longer matches a prospective test set.
- A fresh full probe (`dev-probe-0.2`) before labeling and timing.

**Next session:** unchanged, except that item 1 (apply the corpus decision) is done. Start with a fresh full probe, the chronological timing of the weeks of 2026-09-21 and 2026-09-07, and `dev` labeling.

### 2026-10-02 23:30 - Cause of the bidi characters found

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Final scan of the logs for em-dashes and bidi controls.

**Expectation:** Clean.

**Observation:** A session note that mentioned the escape for U+202E contained the literal character instead. Unicode escapes written by the assistant reach files as the characters themselves. This also explains the 22:55 test-file incident and the failed heredoc fix.

**Evidence:** Character scan of `friction-delight-logs/session2.md`.

**Workaround:** Replaced with an escape via code points. A scan for bidi controls and em-dashes now runs before each wrap-up.

**Consequence:** Any file the assistant writes may contain invisible characters it meant as escapes.

**Follow-up:** Add a bidi and em-dash check to the pre-commit hook (proposed, not done).

### 2026-10-02 23:45 - Stopping rule restored to two targets; success criterion revised

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Apply the author's second-round corpus decisions.

**Expectation:** Wording changes only.

**Observation:** The first accepted stopping rule (20 consequential comments or 16 weeks) let accrual end with as few as about 67 test comments if the consequential share is high. Review reduction would then rest on a small set. The author restored the 100-comment target as a second required target.

**Evidence:** The proposal's sizing table; at a 30% share, 20 consequential comments arrive with about 67 total.

**Workaround:**
- ADR-010 and EVALUATION.md now stop accrual when both 20 consequential and 100 total test comments are reached, or at 16 weeks.
- If the cap ends accrual, the report states which targets were met, with counts.
- The proposal's table has a both-targets column, and its amendment note records that the target was dropped and restored the same day.
- PROJECT-BRIEF success criterion 2 was revised, with a dated note that the revision came before any evidence.

**Consequence:** At the mean trailing rate, both targets fit within 16 weeks when the consequential share is about 8% or more.

**Follow-up:** Recompute from the observed `dev` share before preregistration.

### 2026-10-02 23:55 - Character checks moved into git hooks

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Enforce the no-em-dash rule and catch invisible bidi controls by tooling (follow-up to the 23:30 entry).

**Expectation:** A simple grep.

**Observation:**
- `scripts/check_text.py` checks the staged content of each changed file, not the working tree, so an unstaged edit cannot hide or cause a finding. It also checks the commit message, through a new `commit-msg` hook.
- The script and its tests build the forbidden characters from code points, so neither file contains one. Given the 23:30 finding, that also keeps the assistant from writing them by accident.
- `LICENSE` is exempt as verbatim third-party text.
- Output is counts and `file:line` only.

**Evidence:** `tests/test_check_text.py`. The two hook tests commit through real git in a throwaway repository, using copies of the real hooks.

**Workaround:** None needed.

**Consequence:** The CLAUDE.md writing rule is now enforced at commit time.

**Follow-up:** None.

### 2026-10-02 - Session summary addendum (second review)

**Decisions recorded:**
- PROJECT-BRIEF success criterion 2 revised, with a dated note.
- Stopping rule: both 20 consequential and 100 total test comments, or 16 weeks; report which targets were met if the cap ends accrual.
- Em-dash and bidi checks in the `pre-commit` and `commit-msg` hooks.

**Completed:**
- ADR-010, EVALUATION.md, ROADMAP, and the accepted proposal (amendment note and a both-targets estimates table) updated.
- `scripts/check_text.py` and `scripts/hooks/commit-msg` added; `pre-commit` runs the character check first. Seven tests, including two end-to-end hook runs through git.
- Full check list rerun.

**Next session:** unchanged. Start with a fresh full probe (`dev-probe-0.2`), time the weeks of 2026-09-21 and 2026-09-07, then label `dev`.

---

