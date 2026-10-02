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

**Evidence:** `git status --short` before commit `d76bdea`.

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
