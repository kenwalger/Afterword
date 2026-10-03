# Friction and Delight Log

Start logging before the first API call. Record what happened at the time rather than reconstructing it later.

## Classification

Use one of:

- `PRODUCT` - platform/API behavior
- `DOMAIN` - comment/community semantics
- `PROJECT` - our own design/implementation
- `ENVIRONMENT` - tooling/runtime/setup
- `UNKNOWN` - cause not established

## Entry template

### YYYY-MM-DD HH:MM - Short title

**Platform:** DEV / CoderLegion / Project

**Type:** FRICTION / DELIGHT / SURPRISE

**Class:** PRODUCT / DOMAIN / PROJECT / ENVIRONMENT / UNKNOWN

**Task:** What was I trying to do?

**Expectation:** What did I expect to happen?

**Observation:** What actually happened? Preserve facts before interpretation.

**Evidence:** Endpoint, response shape, screenshot, fixture, error, or other supporting artifact.

**Workaround:** What did I do, if anything?

**Consequence:** Time cost, architectural change, missing capability, new idea, or no consequence.

**Follow-up:** Question or action, if any.

---

## Session summary template

### YYYY-MM-DD - Session summary

**Goal:**

**Completed:**

**Friction discovered:**

**Delight discovered:**

**Claims affected:**

**ADRs affected:**

**Scope pressure:** Anything that tried to sneak into V1?

**Next smallest useful step:**

---

## Initial observation

### 2026-10-02 - CoderLegion API is authenticated and capability-limited

**Platform:** CoderLegion

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Determine whether CoderLegion could plausibly become a future source adapter.

**Expectation:** Public searching did not clearly reveal API documentation; API availability was uncertain.

**Observation:** `/api-docs` exists behind authentication. Personal API keys are documented for post search/list/fetch/create/edit, feeds/categories/groups, cover uploads, notifications, and comment/reply write/edit/hide/reshow operations. The provided restricted-endpoint list does not explicitly include follower, reaction, analytics, profile lookup, or comment-read endpoints.

**Evidence:** User-provided excerpt from authenticated CoderLegion API documentation.

**Workaround:** None required for V1 because CoderLegion is out of current scope.

**Consequence:** Second-source feasibility is plausible, but actual read capabilities must be tested rather than inferred.

**Follow-up:** Revisit only at the Stage 6 decision gate.

### 2026-10-02 - DEV comment bodies arrive as HTML

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Fill the DEV column of the capability matrix from documentation before any requests.

**Expectation:** Comment bodies available as Markdown, matching how they are written.

**Observation:** Documentation describes `GET /api/comments?a_id=` as public, returning threaded comments with nested `children`, an `id_code` identifier, `created_at`, an embedded `user`, and the body as `body_html`. No Markdown body is described. No edited timestamp or deletion representation is described.

**Evidence:** Forem API v1 reference documentation and published OpenAPI descriptions. Not yet verified by request.

**Workaround:** None yet.

**Consequence:** Normalization needs a versioned HTML-to-text step that preserves code and links. Edit detection may have to rely on payload hashes. Deletion semantics must be discovered empirically.

**Follow-up:** Verify in Stage 0 and capture sanitized fixtures.

---

### 2026-10-02 - Session summary

**Goal:** Review v1 scoping and produce v2.

**Completed:** Renamed project to Afterword. Added taxonomy, priority policy, and labeling guide. Split corpus into dev and sealed test sets. Added heuristic baseline, adversarial and injection set, lifecycle and deletion handling, review instrumentation, and ADR-007 to ADR-011.

**Friction discovered:** v1 defined consequential recall against a review threshold that did not exist. The capability matrix was filled for the deferred platform and empty for the V1 platform.

**Delight discovered:** None recorded.

**Claims affected:** C-001 to C-004 gained measurement notes. C-008, C-009, C-010 added.

**ADRs affected:** ADR-007 to ADR-011 added. ADR-001 to ADR-006 unchanged.

**Scope pressure:** Considered using commenter novelty ("first comment from this identity") as a priority override. Rejected for V1 as a reputation signal under a different name.

**Next smallest useful step:** Measure comment volume across existing DEV posts (C-009).

---

## Stage 0 implementation (2026-10-02)

Curated from the raw session notes. Times are UTC. Evidence lives in git-ignored probe reports; the run IDs are cited so results can be traced.

### 2026-10-02 16:20 - `.env` was staged before the first commit

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Stage the docs-only commit.

**Expectation:** Only docs staged.

**Observation:** `.env` was already in the git index, and this session had not added it.

**Evidence:** `git status --short` before the docs commit, now `96c2825`. It was first made as `d76bdea` and amended away to remove an attribution trailer, so `d76bdea` is not in the history.

**Workaround:** Removed it from the index without opening it. The commit contains no env file, and `.env` is now ignored.

**Consequence:** No secret was committed. ADR-006 held, but only because the index was checked.

**Follow-up:** None.

### 2026-10-02 17:07 - The account endpoint returns the email address

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Authenticate and get the author's user ID (ADR-011).

**Expectation:** Profile-level fields.

**Observation:** `/api/users/me` includes `email`, `followers_count`, and `badge_ids`. Only `id` is needed.

**Evidence:** `shapes.json`, run `20261002T170711Z`.

**Workaround:** The probe saves only `id` from this endpoint. Email was removed from earlier saved runs in code, without reading the files.

**Consequence:** Raw capture needs per-endpoint allowlists, not just secret stripping.

**Follow-up:** Apply the same rule in the Stage 1 adapter.

### 2026-10-02 17:07 - The comment endpoint pages threads when asked

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Verify comment pagination.

**Expectation:** All comments returned, with `page`/`per_page` ignored.

**Observation:** With no parameters, every comment is returned (largest thread: 116, matching `comments_count`). `page=2&per_page=1` returned one top-level thread (4 comments). No pagination headers.

**Evidence:** `comment_pagination` in runs `20261002T170711Z` and `20261002T171152Z`.

**Workaround:** Never send those parameters, and reconcile against `comments_count`.

**Consequence:** A default cap above 116 top-level threads cannot be ruled out at this volume.

**Follow-up:** Stage 1 records a limitation whenever the counts disagree.

### 2026-10-02 17:33 - No comment edit timestamp; edits change only the body

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Verify the comment edit timestamp, by schema check and by a hand edit.

**Expectation:** Possibly `edited_at`, as articles have.

**Observation:** Comments have no edit or parent field. A hand edit changed only `body_html`; `created_at` and every other field stayed the same, and no key appeared. Threads nest up to 34 levels.

**Evidence:** `node_keys` in the full runs; diff of runs `20261002T173106Z` and `20261002T173308Z`.

**Workaround:** Edits are detected by payload hash; the parent is derived from nesting.

**Consequence:** Edit time is unknowable beyond "between two syncs". Deep threads raise the importance of `NEEDS_THREAD_CONTEXT`.

**Follow-up:** None.

### 2026-10-02 17:34 - Deleting a comment with replies leaves an authorless placeholder

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Hand test of deletion: one comment without replies, one with a reply.

**Expectation:** ADR-009 assumes deletion means absence.

**Observation:**
- The comment without replies disappeared.
- The comment with a reply stayed in the tree: same `id_code`, `created_at`, and `children`, a replaced body, and `user` as an empty object.
- The placeholder persisted after its reply was deleted.
- `comments_count` excludes placeholders.
- Ten minutes later the result was unchanged; the CDN never served stale data.

**Evidence:** Runs `20261002T173436Z`, `20261002T174523Z`, and `20261002T174612Z`.

**Workaround:** The adapter detects placeholders structurally. The baseline excludes them and reports them separately (0 in the clean full run).

**Consequence:** ADR-009 and the DATA-MODEL lifecycle need a placeholder rule. A proposal was drafted (now `docs/proposals/accepted/2026-10-02-deletion-placeholders.md`) and accepted with revisions later in the session; see the session summary. Only author self-deletion was tested.

**Follow-up:** The author decides on the proposal.

### 2026-10-02 17:50 - Three articles report one more comment than they return

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Reconcile counted comments with `comments_count`.

**Expectation:** An exact match.

**Observation:** 135 of 138 match. On three articles the count is one higher than the comments returned, identically in both runs. Placeholders cannot explain this, because they move the difference the other way.

**Evidence:** `count_reconciliation` in both full runs; the hand-test counts.

**Workaround:** None.

**Consequence:** UNKNOWN. Candidates are hidden or moderated comments, or suspended accounts.

**Follow-up:** Stage 1 records the mismatch as a sync limitation.

### 2026-10-02 17:07 - Undocumented AI-disclosure fields

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Record the comment shape.

**Expectation:** Documented fields only.

**Observation:** `ai_disclosure_label` and `ai_disclosure_level` appear on 179 of 707 comments (115 of the 432 from others), always paired. The only values seen are `Not Disclosed` / `not_disclosed`. The rest lack the keys. Presence is not explained by date.

**Evidence:** Enum counts from run `20261002T171152Z`.

**Workaround:** None. Recorded only.

**Consequence:** See Scope pressure below.

**Follow-up:** None in V1.

### 2026-10-02 17:07 - Some comment IDs are all digits

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Verify the `id_code` type.

**Expectation:** Opaque alphanumeric strings.

**Observation:** All are strings, length 3 to 5, but 33 of 707 consist only of digits.

**Evidence:** `shapes.json`, `$.id_code` string formats.

**Workaround:** A digit-only synthetic ID in the test fixtures.

**Consequence:** Any type-inferring step (CSV, spreadsheet, JSON tooling) could corrupt IDs.

**Follow-up:** Keep IDs as strings in the Stage 2 schema.

### 2026-10-02 17:07 - Rate limits without headers, behind a CDN

**Platform:** DEV

**Type:** FRICTION

**Class:** PRODUCT

**Task:** Verify rate-limit behavior.

**Expectation:** Rate-limit headers.

**Observation:** No rate-limit headers. At about 1 request per second, two full runs of about 160 requests received 5 and 1 responses with status 429; backoff recovered every time. Responses carry Varnish cache headers (`cache-control: public, no-cache` on comments).

**Evidence:** `rate_limits` and `http_cache_by_endpoint` in the findings.

**Workaround:** The probe now records Retry-After values and 429 bodies.

**Consequence:** Limits are discovered only by hitting them. Sync must be paced and resumable.

**Follow-up:** Capture a 429 body to finalize `error-429.json`.

### 2026-10-02 17:12 - Overlapping probe runs and implicit run selection

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Run the full probe and compute the baseline.

**Expectation:** One run at a time, and a baseline from a known run.

**Observation:** Two full runs overlapped by about 11 seconds. Their results were identical, but the baseline, which picked the latest run, silently switched to the newer one.

**Evidence:** `run.json` timestamps for runs `20261002T170711Z` and `20261002T171152Z`.

**Workaround:** An exclusive probe lock file. The baseline requires an explicit `--run` and refuses scoped runs.

**Consequence:** The baseline is reproducible from a named run and cannot pick up test comments.

**Follow-up:** None.

### 2026-10-02 17:15 - Weekly statistics distorted by empty history and a partial week

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Name a typical week and a busy week to time (C-009).

**Expectation:** A representative median.

**Observation:** The trailing-52-week median was 0.5 to 1, because volume began in March 2026 and the in-progress week was counted.

**Evidence:** Baseline report for run `20261002T171152Z`.

**Workaround:** Statistics use complete weeks only, and a trailing-13-week basis is added.

**Consequence:** Weeks to time: 2026-09-21 (7 comments from others) and 2026-09-07 (44).

**Follow-up:** Time both weeks.

### 2026-10-02 17:20 - Comments from others are concentrated in a few posts

**Platform:** DEV

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Check whether the corpus targets in `EVALUATION.md` are achievable with a split by post.

**Expectation:** Comments spread across many posts.

**Observation:** Of 432 comments from others, the top 10 articles hold 53.9% and the top 3 hold 34.0%. 74 of 138 articles have none; only 8 have 10 or more.

**Evidence:** `per_article_from_others.concentration` in the baseline for run `20261002T171152Z`.

**Workaround:** None. This is a design decision.

**Consequence:** A small number of posts will dominate any post-level split. `test-natural` at 100 to 150 comments takes a quarter to a third of the pool.

**Follow-up:** Revisit the corpus targets in writing before labeling.

### 2026-10-02 18:10 - Pre-commit identity scan finds package metadata and a shared first name

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Prove that no real handle, name, or email is in any committable file.

**Expectation:** Zero matches.

**Observation:** Matches appeared only in `pyproject.toml`, from the `authors` entry `uv init` copied from git config. After the entry was set to the author's chosen identity, one commenter's short display-name term matched because it is also a whole word of the author's own name.

**Evidence:** `scripts/check_committable.py` (counts per file only, never values).

**Workaround:**
- The author's own identity is allowed in `pyproject.toml` only.
- A commenter term that is a whole word of the author's identity counts as author identity: allowed there, a violation elsewhere.
- Other commenters' terms are enforced in every file.
- Result: 0 disallowed matches.

**Consequence:** Short shared names cannot be told apart by string matching. The rule keeps them a violation everywhere except package metadata.

**Follow-up:** Run the scan as a pre-commit check.

---

### 2026-10-02 - Session summary (Stage 0 implementation)

**Goal:** Repo skeleton, read-only DEV probe, capability verification, C-009 volume baseline.

**Completed:**
- Docs committed before any code (`96c2825`), then code in a second commit after review.
- Python package with the probe, a value-free shape summary, and the baseline. Tests make no live calls and pass on Python 3.12 and 3.14.
- Capability matrix v3 (every DOCUMENTED row verified).
- C-009 volume appended to `CLAIMS.md`.
- ADR-009 amended (accepted, provisional) and DATA-MODEL v3 applied. Only the exact deletion placeholder shape qualifies; other unexpected shapes are flagged, never classified. The proposal is in `docs/proposals/accepted/`.
- `scripts/check_committable.py`: an identity scan over every committable file, printing counts only.

**Friction discovered:**
- Undocumented comment pagination.
- No edit timestamp or parent ID.
- Deletion placeholders.
- Unexplained count mismatches.
- Header-less rate limits.
- Email on the account endpoint.
- Digit-only IDs.

**Delight discovered:** Two full runs were identical; the CDN never served stale data; edit and deletion behavior was established by a 15-minute hand test.

**Claims affected:** C-009 partially measured (spiky recent volume: trailing-13-week median 7, p90 44, max 60).

**ADRs affected:**
- **ADR-009:** amended, "Accepted, provisional". It rests on one self-deleted sample per case; deletion by another user or a moderator is untested.
- **ADR-011:** for deleted comments, authorship comes from earlier observations, or is `UNKNOWN`.
- **ADR-010:** unchanged; see the open questions.

**Scope pressure:**
- **`ai_disclosure_*` fields:** recorded, not a V1 priority input. They describe the commenter's tooling, which is close to the reputation-style inputs the priority policy excludes. Future candidate only.
- **Comment pagination support:** not built.
- **Corpus target changes:** left to the author.

**Open questions (recorded, not decided):**
- **Stage 2 edit detection.** Detect edits by comparing normalized text, not the raw payload hash, so that a DEV renderer change cannot flag every comment as edited. Payload hashes stay for SourceRecord provenance.
- **Corpus targets.** The historical pool (432 comments from others, concentrated in a few posts) cannot support a dev set plus two post-disjoint test sets. Candidate approach under consideration: the full historical corpus as `dev`, and a prospective test set of comments arriving after preregistration, labeled before shadow-mode classifier output is revealed. Not decided; `EVALUATION.md` and ADR-010 are unchanged.

**Next session:**
1. Decide the corpus targets.
2. Time a chronological review of the weeks of 2026-09-21 (7 comments from others) and 2026-09-07 (44). These are re-reads, so the times are a lower bound on first-read cost.
3. Label.
4. Wire `scripts/check_committable.py` in as a pre-commit check.

---

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

## Session 4: Stage 1 to 3a groundwork (2026-10-03)

### 2026-10-03 07:20 - The last commit holds only ADR-012

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Orientation: compare git state with the session 3 summary.

**Expectation:** Commit `cb2eac5` ("Stage 0: probe progress, timing validity, workflow, service layer") contains the session 3 work.

**Observation:** `git show --stat HEAD` lists one file, `docs/adr/ADR-012-application-service-layer-single-entry-point.md`. Everything else its message describes (`service.py`, `progress.py`, `timing.py`, `WORKFLOW.md`, the CLI, baseline, and labeling changes, their tests, and the doc edits) is still uncommitted in the working tree. Separately, `../docs/adr/ADR-013-local-first-hosted-path-preserved.md` is staged as an empty file, its content is unstaged, and its name uses four digits, as ADR-012's did before the author renamed it.

**Evidence:** `git status --short`, `git show --stat HEAD`, `git show :<ADR-0013 path> | wc -c` (0).

**Workaround:** None. Nothing committed or staged by this session.

**Consequence:** Session 4 work would land in the same working tree as uncommitted session 3 work unless the author commits session 3 first.

**Follow-up:** Author: commit the session 3 work (the existing message fits it), and decide on the ADR-013 file name.

### 2026-10-03 07:45 - Policy gaps closed as clarifications, not a new version

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Implement `pp-v0.1` as pure, tested code.

**Expectation:** `PRIORITY-POLICY.md` specifies everything the code needs.

**Observation:** Four things were unspecified: the form of model confidence, the confidence floor ("set during Stage 3a", no value), what "edited since it was last reviewed" means before review records exist, and which rule `rule_applied` names when several apply.

**Evidence:** `docs/PRIORITY-POLICY.md` before this session.

**Workaround:** Recorded as a dated clarification of `pp-v0.1`, since no classification existed and no tier, default, or override changed: confidence is `LOW`/`MEDIUM`/`HIGH` (author's decision); the floor is off in `pp-v0.1` and setting it is `pp-v0.2`; "edited since review" means lifecycle `EDITED` until Stage 4; rules have names, all firing rules are recorded in `rules_fired`, and `rule_applied` is the first in table order that reaches the final tier (the class default only when no override reaches it).

**Consequence:** `DATA-MODEL.md` v5 adds `rules_fired`. `src/afterword/policy.py` tests every class, every override, and, exhaustively, that no combination of flags, confidence, floor, and edit state lowers a tier.

**Follow-up:** Choose the floor on `dev` in Stage 3a (`pp-v0.2`).

### 2026-10-03 07:50 - The cache key covers the whole model input

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Define the classification cache key (incremental classification).

**Expectation:** Key on the comment's normalized-text hash plus provider, model, prompt, and taxonomy versions.

**Observation:** The classifier also receives the post title and, for a reply, the parent's text. Keyed on the comment's text alone, an edited parent would never trigger reclassification.

**Evidence:** `docs/PRIVACY-AND-BOUNDARIES.md`, default context.

**Workaround:** At the author's decision, the key is the SHA-256 of the canonical serialization of everything sent (`input_hash`), plus provider, model ID, model digest, prompt version, and taxonomy version. `MALFORMED` results are cached (deterministic at temperature 0); `FAILED` results are retried.

**Consequence:** `DATA-MODEL.md` v5.

**Follow-up:** Implement in step 8.

### 2026-10-03 07:55 - Local models pulled and pinned by digest

**Platform:** Project

**Type:** DELIGHT

**Class:** ENVIRONMENT

**Task:** Pull the two approved Ollama models after checking the tags exist.

**Expectation:** Tags may have moved or been renamed.

**Observation:** Both tags exist in the Ollama library, and the local digests after pulling match the short digests shown there:

- `qwen3:4b-instruct-2507-q4_K_M`: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0` (2,497,293,803 bytes, Apache-2.0)
- `llama3.1:8b-instruct-q4_K_M`: `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` (4,920,753,328 bytes, Llama 3.1 Community License)

Ollama 0.34.3, CPU only (13th Gen Intel Core i7-1355U, 10 cores, 12 threads, 32 GB RAM).

**Evidence:** ollama.com library tag pages; `ollama list`; `GET /api/tags`.

**Workaround:** None needed.

**Consequence:** These digests are what the Ollama provider will verify before every run. A changed digest under the same tag will be refused.

**Follow-up:** Benchmark on synthetic fixtures after the checkpoint.

### 2026-10-03 08:00 - Anthropic's retention and training terms, checked before drafting

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Draft the model-boundary record for the Anthropic path.

**Expectation:** Write retention from memory.

**Observation:** The published terms were checked instead. Anthropic's privacy center says API inputs and outputs are deleted within 30 days unless another agreement applies, the input is flagged for a Usage Policy violation (up to 2 years), or the law requires it (article dated 2026-07-01). Commercial API data is not used for training by default (article dated 2026-08-18).

**Evidence:** `docs/PRIVACY-AND-BOUNDARIES.md` v3, Path B, with sources.

**Workaround:** None needed.

**Consequence:** The record states that this path sends other people's comment text to a third party that keeps it for up to 30 days. It is a secondary comparison only, with no sign-off yet.

**Follow-up:** The author signs off each path before any real comment goes through it.

### 2026-10-03 08:10 - The first pre-check patterns matched ordinary prose

**Platform:** Project

**Type:** FRICTION

**Class:** DOMAIN

**Task:** Write the deterministic `POSSIBLE_INSTRUCTION_TEXT` pre-check (`pc-v0.1`).

**Expectation:** A list of injection phrases is enough.

**Observation:** Broad first patterns would have surfaced ordinary technical comments: "for the model" (common in AI posts), "attention model", "compiler flags:", "give priority to", "the output should be", "never prioritize". The author writes about AI, so model vocabulary in comments is normal. The patterns were narrowed to forms addressed to an automated system or to this comment's classification. Two injection forms remain known gaps and are in the adversarial set: an instruction with no trigger phrase, and a non-English one.

**Evidence:** `tests/test_precheck.py` (24 flagged forms, 11 ordinary sentences not flagged); `fixtures/corpus/adversarial.jsonl` cases `adv-109` and `adv-110`.

**Workaround:** None needed.

**Consequence:** ADR-008 accepts false positives. They are kept rare so the pre-check is not a reason to ignore `SURFACE`. Writing a taxonomy class name in capitals ("CORRECTION:") is flagged, an accepted false positive.

**Follow-up:** Count pre-check hits on `dev` once the store exists (a count only, no text) to measure the false-positive rate.

### 2026-10-03 08:15 - The draft heuristic collapses short corrections

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Run B1 (`hb-v0.1`) through the policy on the synthetic sets.

**Expectation:** The heuristic would catch at least the explicit corrections.

**Observation:** With a 280-character length threshold, B1 collapses most short synthetic comments, including all three short corrections and both short-correction adversarial cases ("Off by one: limit 10 lets 11 through" has no question mark and no lexicon word). Long praise is queued by length, and "breaks" in a casual remark is a correction. Every injection the pre-check catches surfaces whatever B1 says.

**Evidence:** B1 over `fixtures/corpus/*.jsonl`; `tests/test_synthetic_sets.py`.

**Workaround:** None. The synthetic sets are not for tuning.

**Consequence:** None yet. EVALUATION.md says B1 is finalized on `dev`, and the synthetic results say nothing about real comments. It does show that a length threshold and a six-word lexicon miss the "very short but important correction" case by construction.

**Follow-up:** Tune the threshold and lexicon on `dev`; each change is a new heuristic version.

### 2026-10-03 08:20 - DEV's code-block chrome would leak into normalized text

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Normalize code blocks for classification.

**Expectation:** A code block is a `pre` element.

**Observation:** DEV's rendered HTML (from DEV's public markup, not from any real payload) wraps a highlighted `pre` in a panel with icon buttons whose SVG titles read "Enter fullscreen mode" and "Exit fullscreen mode". A tag-stripping normalizer would add those words to every comment with code.

**Evidence:** `tests/test_normalize.py` (`DEV_CODE_BLOCK`, synthetic).

**Workaround:** `norm-v0.1` drops `svg`, `button`, `script`, `style`, `template`, and `noscript` content, takes the language from the `pre` class, and keeps code whitespace.

**Consequence:** The exact wrapper markup in real comments is not verified, since real payloads are not opened.

**Follow-up:** At ingest, record a value-free count of normalized texts that still contain renderer phrases ("fullscreen mode"), so the gap would show without anyone reading a comment.

### 2026-10-03 08:25 - The tool layer turned `\u` escapes into the characters

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Write tests that use a right-to-left override, an em-dash, and combining characters.

**Expectation:** `"\u202e"` in a Python source file stays an escape.

**Observation:** The literal characters were written instead, including an em-dash and bidi controls, which the pre-commit hook rejects, and a right single quote in a regex. The cause is the tool layer, not one tool: an escape in a shell command was converted too, so a Python replacement whose target and replacement both came from escapes reported success and changed nothing.

**Evidence:** A non-ASCII scan of every touched file found four lines (counts only).

**Workaround:** These strings are now built from code points (`chr(0x202E)`, `chr(92)` for a backslash) or HTML entities (`&#8217;`). Every touched file is free of non-ASCII characters.

**Consequence:** None committed. Session 3 found the same kind of problem with a shell heredoc.

**Follow-up:** Scan touched files for non-ASCII before every checkpoint.

### 2026-10-03 08:30 - Line-ending conversion would change fixture hashes

**Platform:** Project

**Type:** SURPRISE

**Class:** ENVIRONMENT

**Task:** Record SHA-256 hashes for the synthetic sets in `fixtures/corpus/MANIFEST.md`.

**Expectation:** The committed bytes are the bytes everyone gets.

**Observation:** `core.autocrlf=true` checks out text files with CRLF on Windows, so a hash recorded from an LF file would not match a fresh checkout.

**Evidence:** `git config core.autocrlf`; earlier warnings like "LF will be replaced by CRLF".

**Workaround:** A new `.gitattributes` pins `fixtures/corpus/*.jsonl` and `fixtures/dev-api/expected/*.json` to LF. `tests/test_synthetic_sets.py` fails if a hash in the manifest is stale.

**Consequence:** Hashes hold on any checkout. The same rule will matter for the frozen `dev` manifest and the weekly sealed outputs (ADR-010).

**Follow-up:** Hash sealed outputs as bytes written by the application, never after a checkout.

### 2026-10-03 08:35 - One taxonomy module for the labeler, the heuristic, and the prompt

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Add a one-key help screen to the label prompts (the author's request).

**Expectation:** The labeling tool would show definitions already.

**Observation:** It listed class and flag names only, and kept its own copy of the lists. The help screen needed definitions, and the heuristic, policy, and prompt need the same names.

**Evidence:** `src/afterword/labeling.py` before this session.

**Workaround:** New `afterword.taxonomy` holds the classes, flags, and one-line definitions. `tests/test_taxonomy.py` checks it against `TAXONOMY.md` (precedence, flag table order, version). `h` at the class or flag prompt prints every class and flag with its definition. Labels are unchanged.

**Consequence:** A taxonomy change now fails a test until the module matches the document.

**Follow-up:** None.

### 2026-10-03 08:40 - A non-ASCII scan of the session notes printed real comment text

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Check both friction logs for forbidden characters before the checkpoint.

**Expectation:** The session notes hold only the session prompt and Claude's entries.

**Observation:** During the session, the author had added terminal output to `friction-delight-logs/session4.md`, including a chronological timing run that shows comment text. A scan for non-ASCII characters that printed matching lines brought a few of those lines, truncated, into the session. Nothing was copied anywhere. The public log was checked by phrase count (0 matches) and contains none of it.

**Evidence:** Counts only: 0 matches of the printed phrases in `docs/FRICTION-LOG.md`; the public session 4 section has 0 non-ASCII characters.

**Workaround:** Scans of the session notes now print counts or line numbers only, never matched lines.

**Consequence:** The session notes are git-ignored, so nothing is committed. Comment text from the notes reached the model session as tool output. It is not used for anything.

**Follow-up:** For the author: real comment text in the private notes is allowed, but any scan that prints matching lines will surface it. Consider keeping timing output in a separate file.

---

### 2026-10-03 - Session summary, checkpoint 1 (session 4, steps 1 to 6)

**Goal:** Stage 1 to 3a groundwork that needs no labels and no real comment data, in dependency order. The author approved the plan with a checkpoint after steps 1 to 6.

**Completed:**
- **Orientation.** The full check list passed at the start (119 tests on 3.14 and 3.12). Two inconsistencies were reported: the session 3 commit held only the ADR-012 file, and ADR-013 was staged empty under a four-digit name. The author committed session 3 and renamed ADR-013.
- **Author's decisions:**
  - The cache key covers the full model input.
  - Confidence is `LOW`, `MEDIUM`, or `HIGH`.
  - Models approved: `qwen3:4b-instruct-2507-q4_K_M` and `llama3.1:8b-instruct-q4_K_M`.
  - The Anthropic provider is built and tested under respx only, with no live benchmark this session.
- **Step 1, docs:**
  - `DATA-MODEL.md` v5: `PlatformConnection`, `connection_id` on SyncRun and ContentItem, `body_text_hash`, edit detection by normalized text, the Classification fields for kind, digest, pre-check, normalization, input hash, and raw output, the cache rule, and `rules_fired`.
  - `PRIORITY-POLICY.md`: the `pp-v0.1` clarifications.
  - `EVALUATION.md` v4: exactly one model is fixed as B2 at preregistration and the others are secondary; B1 and B2 share the pre-check and structural flags; the versioning list is extended.
  - `PRIVACY-AND-BOUNDARIES.md` v3: model-boundary records for the Ollama and Anthropic paths, neither signed off.
  - `CLAUDE.md`: current stage, `ANTHROPIC_API_KEY` rules, and storage and identity rules (ADR-013).
  - `ROADMAP.md`: the ADR range and the adversarial set.
  - README status, `fixtures/README.md` layout, and the help key in `LABELING-GUIDE.md`.
  - `tests/conftest.py` also removes `ANTHROPIC_API_KEY`.
- **Step 2, `afterword.normalize` (`norm-v0.1`):**
  - Fenced code with its language, inline code, `[text](url)` links, images, embeds, quotes, lists, and tables.
  - Renderer chrome is dropped. Control and format characters are removed. Text is NFC-normalized.
  - Structure counts and links are returned alongside the text.
  - `text_changed` compares normalized text, so a rendering change is not an edit.
  - Expected output is recorded for the synthetic DEV comments.
- **Step 3, `afterword.precheck` (`pc-v0.1`):** ten named rule groups on the normalized text, with a known-gap list.
- **Step 4, `afterword.policy` (`pp-v0.1`):** a pure `assign` that returns the tier, `rule_applied`, and `rules_fired`, with an exhaustive test that no override ever lowers a tier.
- **Step 5, `afterword.heuristic` (`hb-v0.1`):**
  - Only the EVALUATION features, computed on prose with code removed.
  - The explanation names the rule that fired.
  - It is a draft until tuned on `dev`.
- **Step 6, synthetic sets:**
  - `fixtures/corpus/adversarial.jsonl` (24 cases: every EVALUATION category, 10 injections including 2 known gaps, and 1 benign false positive).
  - `fixtures/corpus/synthetic-bench.jsonl` (30 cases, 3 per class, for benchmarks only).
  - `fixtures/corpus/MANIFEST.md` with hashes, and `.gitattributes` pinning LF.
- **Also:** `afterword.taxonomy` as the single source for names and one-line definitions. `h` at the label prompts shows them.
- **Models:** both pulled, and their digests recorded in the 07:55 entry. None has been run.
- **Checks:**
  - ruff, ruff format, mypy, and pydoclint are clean.
  - 408 tests pass on 3.14 and on 3.12 (isolated).
  - The identity scan reports 0 disallowed matches.
  - No em-dash, bidi, or other non-ASCII character in any touched file.

**Friction discovered:**
- Session 3's commit was incomplete (resolved by the author).
- The recursive listing reached `real/` (names only).
- Four policy gaps.
- The cache key had to cover context.
- Pre-check false positives on AI vocabulary.
- The draft B1 collapses short corrections.
- DEV code-block chrome would leak into normalized text.
- The editing tool turns `\u` escapes into characters.
- autocrlf would break fixture hashes.
- A line-printing scan of the session notes surfaced real comment text that the author had pasted there (nothing copied).

**Delight discovered:** Model digests matched the library on the first pull. The taxonomy module now fails a test if it drifts from `TAXONOMY.md`.

**Claims affected:** None. No model has classified anything.

**ADRs affected:**
- ADR-013 is now referenced in CLAUDE.md and ROADMAP, and the data model follows rule 3 (`PlatformConnection`).
- ADR-008 is implemented as `pc-v0.1`.
- ADR-007 is implemented as `pp-v0.1`.
- No ADR changed.

**Scope pressure:**
- **Help screen in the labeling tool:** added at the author's request. Display only; labels are unchanged.
- **`synthetic-bench.jsonl`:** added so the benchmark has class-balanced synthetic input. Marked benchmark-only, never for tuning.
- **`.gitattributes`:** added because the manifest hashes required it.
- **Service functions for the new pure modules:** not added yet. They arrive with their first caller (step 10), as ADR-012's incremental adoption allows.

**Open for the author:**
- Review the `intended` labels in the synthetic sets. They are what Claude wrote each case to be, not ground truth.
- Sign off each model-boundary path before any real comment goes through it.
- Commit this checkpoint (`commit-message.txt`).

**Next:** steps 7 to 11, after the commit: store and ingest, the classifier wrapper, the providers, service functions and CLI, then the synthetic benchmark.

## Session 5: label UI, store, classifier, providers (2026-10-03)

### 2026-10-03 18:40 - The labeling UI became priority 0 mid-session

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Steps 7 to 11 (store, classifier, providers, service and CLI, benchmark).

**Expectation:** Steps 7 to 11 in order.

**Observation:** While the store was being designed, the author made a local browser labeling UI priority 0: labeling is the critical path, and the terminal tool is too slow for the full `dev` corpus.

**Evidence:** The author's message in this session.

**Workaround:** Steps 7 to 11 paused before any code was written. The terminal tool's record building and batch handling were moved into shared pieces (`make_label`, `LabelBatch`, `comment_view`) so both transports write identical records, then `afterword label-ui` was built over new service functions (ADR-012).

**Consequence:** Steps 7 to 11 start after the UI.

**Follow-up:** None.

### 2026-10-03 19:00 - A browser smoke test caught a focus bug the unit tests could not

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Verify the label UI's keyboard flow.

**Expectation:** Python tests of the controller and HTTP endpoints, plus a JavaScript syntax check, would be enough.

**Observation:** Driving the page in headless Chrome over the DevTools protocol (synthetic run only) showed that after Enter saved a label, focus was restored to the reason field for the next comment, so the next shortcuts would have been typed as text.

**Evidence:** Smoke script in the session scratchpad; `focusAfterSave` was `INPUT` before the fix and `BODY` after.

**Workaround:** Typed text and focus now carry over only while the same comment is on screen.

**Consequence:** One smoke run of the real page is worth keeping for UI changes. Not added to the test suite (it needs a browser).

**Follow-up:** None.

### 2026-10-03 19:15 - The LABELING-AT-SCALE text did not arrive with the message

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Add `docs/LABELING-AT-SCALE.md` with the exact content the author provided.

**Expectation:** The content attached to the message.

**Observation:** The message said the content was attached, but no content came through.

**Evidence:** The author's message in this session.

**Workaround:** Every other part of that request was applied (SCOPE, EVALUATION, `sample_kind`, C-011, README). The file itself waits for the text, which was asked for.

**Consequence:** Resolved the same session: the author placed `docs/LABELING-AT-SCALE.md` in the working tree. It is left exactly as written.

**Follow-up:** None.

### 2026-10-03 19:20 - A bash heredoc failed on a Python edit script

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Splice a large replacement into `labeling.py` with an inline script.

**Expectation:** A quoted heredoc passes its body literally.

**Observation:** The shell reported an unexpected end of file while looking for a matching quote, and nothing was changed.

**Evidence:** `unexpected EOF while looking for matching` from the Bash tool.

**Workaround:** Large replacements are written to a scratchpad file and spliced in by a small script.

**Consequence:** A few minutes.

**Follow-up:** None.

### 2026-10-03 19:40 - A purge test failed on a fixture copy, not a leak

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Prove that a purge removes a deleted comment's text from the SQLite file, not only from its rows.

**Expectation:** After the absence-twice purge, the comment's text appears nowhere in the file.

**Observation:** The text was still in the file. A row scan found it in comment `4821`, which the synthetic DEV fixture builds as a copy of the purged comment and which is still live. The purge itself was complete.

**Evidence:** `tests/test_store.py`, `test_absence_twice_deletes_and_purges`.

**Workaround:** The deleted comment gets unique text in that test. The store also runs with `secure_delete` on, so purged and forgotten values are overwritten in the file rather than left in free pages, and `forget` vacuums.

**Consequence:** None in code. Byte-level checks of the file stay in the suite.

**Follow-up:** None.

### 2026-10-03 19:55 - One synthetic case per local model before handing over the benchmark

**Platform:** Project

**Type:** DELIGHT

**Class:** ENVIRONMENT

**Task:** Make sure the author's benchmark run cannot fail on the request shape (JSON-schema `format`, `think: false` on a model without thinking, digest check).

**Expectation:** Mocked tests cover the shape; a live call might still be refused.

**Observation:** `afterword models verify` matched both pins. One synthetic case (`adv-001`) per model returned schema-valid output, classified `CORRECTION`, tier `SURFACE`. Cold, including model load: qwen3 4B 83.2 s (load 12.1 s, 645 input tokens, 77 output); llama3.1 8B 143.7 s (load 17.6 s, 645 input, 48 output). CPU only.

**Evidence:** Console output in this session; synthetic input only, no store involved.

**Workaround:** None needed.

**Consequence:** The full benchmark (57 requests per model) is long on this machine; it is the author's to run.

**Follow-up:** Warm timings from the benchmark.

### 2026-10-03 20:05 - `git add -N` touched the author's index

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Run the identity scan over new files, which reads staged and tracked files.

**Expectation:** An intent-to-add entry is harmless.

**Observation:** It added an intent-to-add entry (the empty blob) for `docs/LABELING-AT-SCALE.md`, which the author had placed in the working tree during the session, and stopped there with a line-ending warning. The other new files stayed untracked.

**Evidence:** `git diff --cached --name-status` showed `A docs/LABELING-AT-SCALE.md` with blob `e69de29`.

**Workaround:** `git reset -- docs/LABELING-AT-SCALE.md` removed the entry; the file on disk was not touched. The index is as the author left it.

**Consequence:** None lasting. The author's text for that file arrived on disk, so it is present verbatim.

**Follow-up:** Do not modify the index; scan working-tree files directly instead.

### 2026-10-03 20:30 - A refused request reset the connection on Windows

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Run the full suite before the checkpoint.

**Expectation:** The label UI's HTTP tests are deterministic.

**Observation:** One full run in five failed in `test_writes_need_json_and_the_token` with `ConnectionAbortedError` (WinError 10053). The server refused a POST (403 or 415) before reading its body; on Windows, closing a socket with unread data resets the connection, so the client got no answer. The browser page would have seen the same failure as "the server did not answer".

**Evidence:** Reproduced by looping the UI tests (failed on the sixth loop).

**Workaround:** The server reads the body (up to 64 KB) before any refusal, and closes the connection for an oversized or invalid length. Fifteen loops passed afterward.

**Consequence:** A real bug in the transport, found only by repetition.

**Follow-up:** None.

### 2026-10-03 20:35 - Two batches in one second shared a batch ID

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Review the label UI's "next batch" path while fixing the reset above.

**Expectation:** Every batch has its own `batch_id`.

**Observation:** `batch_id` is the start time to the second. In the browser, pressing `b` within a second of the previous batch ending would reuse the earlier batch's ID, and two batches' records would merge. The terminal tool's resume test had even asserted the shared ID under a fixed clock.

**Evidence:** `tests/test_labeling.py`, `test_resume_continues_with_the_next_unlabeled_comment`.

**Workaround:** A batch that starts in the same second as an earlier one gets `_2`, `_3`, and so on. The format is otherwise unchanged and documented in `fixtures/README.md`. No real label existed yet.

**Consequence:** Batch records stay separable for fatigue and timing analysis.

**Follow-up:** None.

### 2026-10-03 - Session summary, checkpoint 1 (session 5: label UI, steps 7 to 10, docs)

**Goal:** Steps 7 to 11 of the session 4 plan (store and ingest, classifier wrapper, providers, service functions and CLI, synthetic benchmark). Added by the author mid-session: a local browser labeling UI as priority 0, and a set of documentation additions on labeling at scale. Step 11 (the benchmark) is the author's to run after this checkpoint is committed.

**Completed:**
- **Orientation.** The full check list passed at the start (408 tests on 3.14 and 3.12). Installed Ollama digests matched the session 4 pins.
- **Author's decisions recorded:**
  - The label UI comes first (priority 0).
  - Path A of the model-boundary record (local Ollama) is signed off, dated 2026-10-03, in `PRIVACY-AND-BOUNDARIES.md` v4. Path B (Anthropic) stays unsigned and is tested under respx only.
- **Label UI (`afterword label-ui`):**
  - A second transport over the same service functions as `afterword label` (ADR-012).
  - Record building, batches, and the comment view moved into shared pieces (`make_label`, `LabelBatch`, `comment_view`), so both tools write identical records.
  - Served by stdlib `http.server` on 127.0.0.1 only. Requests need a per-session token and the local `Host`; writes accept JSON only; request logging is off.
  - One self-contained page with no external assets, which inserts all text with `textContent`.
  - Keyboard-first: digits for the class, letters for flags, Shift+0 to 3 for the prospective grade, `g` then 0 to 3 for the retrospective grade (shown only after the prospective one), Enter to save, and `h` for definitions.
  - `--posts random --seed N` on both tools: posts shuffled reproducibly, comments within a post oldest first, the seed recorded in the batch record.
- **Step 7, store:**
  - `Repository` protocol; `SqliteRepository` (stdlib `sqlite3`, the only module with SQL, `secure_delete` on); the store in git-ignored `data/`.
  - String IDs and UTC RFC 3339 timestamps, with a `connection_id` on every record (ADR-013).
  - The DEV adapter reads a saved probe run as sync observations, with reduced payloads.
  - The lifecycle rules as a pure planner (`afterword.lifecycle`): new, unchanged, payload-only change, edit by normalized text, missing, deleted by absence twice or by placeholder, placeholder first seen, unexpected shape.
  - The ADR-009 purge removes body text, raw payloads, and model text derived from the comment.
  - `afterword ingest --run`, `connections`, and `forget --connection [--yes]`.
- **Step 8, classifier `pr-v0.1`:**
  - Fixed instructions and taxonomy in the system text; title, parent, and comment last, each delimited, with marker sequences broken up.
  - A JSON schema that both providers accept, plus a stdlib validator that names each malformed reason (unreadable or semantic).
  - `MALFORMED` is cached and never retried; `FAILED` is retried.
  - An input that may not fit the 2048-token context is not sent and is surfaced.
- **Step 9, providers:**
  - One `Provider` protocol over httpx.
  - Ollama: loopback only, approved models with pinned digests verified before any run, `/api/chat` with a JSON-schema `format`, temperature 0, a fixed seed, `num_ctx` 2048, `num_predict` 200, and `think` false.
  - Anthropic: `claude-haiku-4-5-20251001` with structured outputs (`output_config.format`, checked against current documentation). The key is read in a request header only, from that module only.
- **Step 10, service and CLI:**
  - `classify --condition b1|b2` is incremental by cache key. It refuses an unsigned boundary path or a digest mismatch before sending anything, and records priority assignments under `pp-v0.1`.
  - `models verify`, and `bench --synthetic` (refuses any set not listed as synthetic in the manifest with a matching hash).
- **Label UI documentation:** README Quick start; `docs/WORKFLOW.md` v2, section 3 (which tool to use, how to launch, the URL to open, the screen, a full shortcut table, resuming and stopping, rules for both tools); the usage section of `docs/LABELING-GUIDE.md`. A test keeps the shortcut table in step with the key map.
- **Docs:**
  - DATA-MODEL v6: `sample_kind`, LifecycleEvent, and the store's extra fields.
  - EVALUATION v5: V1 measurement uses researcher labels only; random and targeted samples are never mixed.
  - SCOPE v4: labeling at scale as a future candidate.
  - CLAIMS C-011 (judgment drift).
  - `sample_kind: researcher` in the label schema and in both labeling tools.
  - README commands and reading order; WORKFLOW and LABELING-GUIDE for `label-ui`; CLAUDE.md privacy paths include `data/`.
  - `docs/LABELING-AT-SCALE.md`, as written by the author.
- **Checks:**
  - ruff, ruff format, mypy, and pydoclint are clean.
  - 492 tests pass on 3.14 and on 3.12 (isolated).
  - The identity scan reports 0 disallowed matches.
  - No em-dash or bidi character in any changed file.
- **Live checks, synthetic only:**
  - `models verify` matched both pins.
  - One synthetic case per model went through the real request path and was schema-valid.
  - A headless-browser run of the label UI used a synthetic run.

**Friction discovered:**
- The UI became priority 0 mid-session.
- A browser smoke test caught a focus bug that the Python tests could not.
- The LABELING-AT-SCALE text first seemed missing (resolved).
- A bash heredoc failed on an edit script.
- A purge test tripped on a fixture copy, not a leak.
- `git add -N` touched the author's index (reverted).
- A refused request reset the connection on Windows (fixed: the body is read first).
- Two batches started in one second shared a batch ID (fixed: a suffix).

**Delight discovered:** The real local models accepted the request shape on the first try. The lifecycle planner is pure, so every ADR-009 path is tested without a database.

**Claims affected:** C-011 added (UNTESTED). No evidence on any claim: no model has classified a real comment.

**ADRs affected:**
- ADR-012 applied to `label-ui` and every new command.
- ADR-013 implemented by the store.
- ADR-009 implemented by ingest and purge.
- ADR-008 by the delimited prompt, the validator, and the pre-check in `classify`.
- ADR-007 by priority computed only by the policy.
- No ADR changed.

**Scope pressure:**
- **The label UI:** in scope by the author's decision. It is a transport over existing labeling, with no new label fields.
- **Labeling at scale:** recorded as a future candidate only (SCOPE v4, LABELING-AT-SCALE.md). V1 adds only `sample_kind: researcher`.
- **A "next batch" button in the UI:** kept, as it is equivalent to running `label` again; the page reminds the labeler to stop between batches when attention drops.
- **`connections` command:** added so `forget` has a way to find connection IDs.

**Open for the author:**
- Commit this checkpoint (`commit-message.txt`).
- Run the two benchmark commands and paste the output.
- Review the `intended` labels in the synthetic sets (still open from session 4).

**Next:** the benchmark write-up and the session summary, in a second commit.
