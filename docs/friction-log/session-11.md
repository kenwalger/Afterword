# Friction log: session 11

Part of the public friction log. The index, the classification, and the entry template are in [`../FRICTION-LOG.md`](../FRICTION-LOG.md).

## Session 11: Part A, the store brought up to date, final label summary (2026-10-18)

`dev` labeling finished before the session (478 of 478 eligible in run `20261018T173927Z`). Part A ingests that run, runs B1 over every stored comment, and records the final label summary, accrual estimate, and oracle ceilings. Part B (design analysis) follows the checkpoint. No comment text, names, or handles below; every figure is a count.

### 2026-10-18 18:40 - The session prompt named this session 9

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Orientation: read the docs and logs, then follow the session prompt.

**Expectation:** The prompt's session number matches the next free number.

**Observation:** The prompt said "This is session 9" and asked for entries in `session9.md` and `docs/friction-log/session-9.md`. Sessions 9 and 10 are already recorded and committed (`8d561a9`, `29eca0a`), and recorded entries are never reworded.

**Evidence:** `git log`; `docs/FRICTION-LOG.md` index rows 9 and 10.

**Workaround:** This session is numbered 11: `friction-delight-logs/session11.md` and this file. The prompt's "session 9 design question" is the open question recorded in `EVALUATION.md` ("Class is a weak proxy for consequence"); the name is kept where earlier documents use it.

**Consequence:** None for the experiment.

**Follow-up:** None.

### 2026-10-18 18:54 - Third real ingest: retention reduced eight old runs; the redaction ran on real data for the first time

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Ingest run `20261018T173927Z` with default retention (newest 3 kept whole), as the author accepted.

**Expectation:** The runs older than the newest three are reduced; runs labels were made from stay whole; nothing is redacted for deletions, since the store knew of one placeholder only.

**Observation:**
- **Lifecycle:** new 28 (20 from others, 8 by the author, on 2 new posts), payload changed with text unchanged 1, placeholder first seen 2, unchanged 749. Nothing became `EDITED` or missing. Store after: 142 posts, 478 live comments from others, 299 by the author, 3 placeholders.
- **Retention reduced eight runs:** `20261002T170711Z`, `20261002T171152Z`, `20261002T173106Z`, `20261002T173308Z`, `20261002T173436Z`, `20261002T174523Z`, `20261002T174612Z`, `20261002T233757Z` (2,533 comment nodes reduced in all). Labels were made from `20261003T141450Z` (302), `20261007T224849Z` (80), and `20261018T173927Z` (96), the newest three runs, so the label exemption was not needed.
- **Redaction:** 2 redactions, both of the single comment self-deleted in the 2026-10-02 hand test, removed from the two hand-test runs (`20261002T173106Z`, `20261002T173308Z`) that still held it live. It is the first time the saved-run redaction ran on real data.
- **The C-009 baseline run `20261002T171152Z` is now reduced:** its counts stay reproducible, its text is gone (ADR-009, as designed).
- **The identity scan** now reads names from the newest three runs only.
- The same 3 posts as before still show `comments_count` one above the live comments observed; a fourth is in the next entry.

**Evidence:** `afterword ingest` and `afterword store-status` output; `reports/redactions.jsonl` (git-ignored; run IDs and counts only read).

**Workaround:** None needed.

**Consequence:** Retention works as specified on real data. The older runs cannot be ingested or labeled from again.

**Follow-up:** None.

### 2026-10-18 18:54 - Two deletion placeholders first seen as placeholders

**Platform:** DEV

**Type:** SURPRISE

**Class:** UNKNOWN

**Task:** As above.

**Expectation:** New placeholders would replace comments the store had seen live.

**Observation:** Both new placeholders were never observed live in any saved run: their creation times (2026-10-09 and 2026-10-10) fall after run `20261007T224849Z` finished, so they were posted and deleted between the two runs. Both are top-level comments on one post, and **neither has a reply in this run**; the post's only other comment is one live top-level comment from someone else. They matched the placeholder rule (0 unexpected shapes, no limitation), so they are `DELETED_UPSTREAM` by `SOURCE_PLACEHOLDER` with authorship `UNKNOWN`, as ADR-009 prescribes for a comment first observed as a placeholder. Nothing could be redacted, since no saved run held them live. On that post DEV's `comments_count` is 3: 1 live comment plus the 2 placeholders.

Against the 2026-10-02 hand test (author self-deletion): there, a deleted comment without replies disappeared, a placeholder outlived its last reply once, and `comments_count` excluded placeholders. These two are placeholders without replies, and the count includes them. Either their replies were posted and deleted between runs too, or these deletions look different from self-deletion. One post cannot tell which.

**Evidence:** Run `20261018T173927Z` `probe-findings.json` (`deletion_observation`, `count_reconciliation`); ingest limitation for post 4802040.

**Workaround:** None.

**Consequence:** Who deleted the two comments (the commenter, a moderator, an account deletion) is unknown. The placeholder rule held, and placeholders are excluded from every count and metric (ADR-009), so nothing downstream changes. But the observation does not fit ADR-009's description of how DEV represents a deletion without replies, or `comments_count`'s treatment of placeholders.

**Follow-up:** For the author: whether this is the trigger ADR-009 names ("deletion paths other than author self-deletion remain `UNKNOWN` until observed"). It does not establish another path, but it is the first deletion observed outside the 2026-10-02 hand test. No ADR or capability-matrix row was changed.

### 2026-10-18 18:55 - B1 over all stored comments; B2 left to the author

**Platform:** Project

**Type:** DELIGHT

**Class:** PROJECT

**Task:** Run B1 (`hb-v0.2`) over all stored comments from others; prepare the incremental B2 command.

**Expectation:** B1 classifies only the new comments, from the cache.

**Observation:** 478 comments: 20 classified, 458 reused from cache, all `OK`. Tiers under `pp-v0.1`: 199 `SURFACE`, 200 `QUEUE`, 79 `COLLAPSED`. The default model options (`num_ctx=4096;num_predict=200;seed=20261003;temperature=0`) match the cached Llama pass, so `afterword classify --condition b2 --model llama3.1:8b-instruct-q4_K_M` will classify only the 20 new comments. Stored classifications by classifier: `hb-v0.1` 458, `hb-v0.2` 478, Llama at 4096 tokens 458, and the 50-comment 2048-token subset runs of both models.

**Evidence:** `afterword classify` output; counts from the store.

**Workaround:** None.

**Consequence:** Llama is scored on 458 of the 478 labels until the author runs the incremental pass.

**Follow-up:** The author runs the B2 command in their own terminal; Part B is rescored then.

### 2026-10-18 19:00 - With all labels, the C-010 contrast is not about shuffled order

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Final label summary, split by publication order and shuffled order.

**Expectation:** The 2026-10-07 contrast (shuffled labels disagree with hindsight more often: 23 only prospectively against 4) would hold or shrink.

**Observation:** The next 176 shuffled labels (`lg-v0.6`) have 8 only prospectively, 0 only in hindsight, and 164 of 172 agreeing on the consequential binary (95.3%), the same rate as the publication-order labels (140 of 147, 95.2%). The first 152 shuffled labels (`lg-v0.3`) stay at 122 of 146 (83.6%). The disagreement sits in one labeling period, not in shuffled labels.

**Evidence:** `EVALUATION.md` v16, label summary on all 478; `CLAIMS.md` C-010, 2026-10-18.

**Workaround:** The summary reports the shuffled labels whole and in their two parts.

**Consequence:** A calibration pass on the first 150 cannot explain this contrast, since the first 150 are not the outlier (Part B4).

**Follow-up:** None.

### 2026-10-18 19:00 - Accrual estimate shortened by recent volume

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Recompute the accrual estimate now that `dev` labeling is complete.

**Expectation:** The share would settle near 27% and the estimate stay at about 6 weeks (mean rate) to 14 (median rate).

**Observation:** The share is 129 of 478 (27.0%; Wilson 23.2% to 31.1%), so the 100-comment target binds. The weekly rate changed more than the share: on the newest run the trailing 13 complete weeks have mean 21.85 and median 19 comments from others, against 17.0 and 7 on the C-009 run, so the estimate is about 5 to 6 weeks, and a replay of those weeks gives 3 to 8 (median 5).

**Evidence:** `EVALUATION.md` v16, accrual estimate 2026-10-18; `afterword baseline --run 20261018T173927Z` (report git-ignored).

**Workaround:** None.

**Consequence:** Which volume basis is registered (the trailing 13 weeks before the preregistration commit) matters more than the share.

**Follow-up:** Recompute at preregistration from the last full run.

### 2026-10-18 19:02 - Scripted doc edits wrote CRLF

**Platform:** Project

**Type:** FRICTION

**Class:** ENVIRONMENT

**Task:** Append dated claim entries and update the roadmap with a short Python script.

**Expectation:** The files keep LF endings.

**Observation:** Python's text mode on Windows wrote CRLF for `CLAIMS.md` and `ROADMAP.md`; git warned on `git diff --stat`. Both were converted back to LF before anything was staged.

**Evidence:** `git diff --stat` warnings; `file` reported "with CRLF line terminators".

**Workaround:** Write with `newline="\n"`, or edit with the editor tool.

**Consequence:** None; caught before staging.

**Follow-up:** None.

### 2026-10-18 19:05 - Checkpoint (Part A)

**Completed:** A1 ingest (lifecycle, retention, redaction, above); A2 B1 over all 478 and the B2 command for the author; A3 final label summary, accrual estimate, and oracle ceilings of `pp-v0.1` and `pp-v0.2` with SURFACE measures (`EVALUATION.md` v16; `CLAIMS.md` C-001, C-002, C-010 entries dated 2026-10-18; `ROADMAP.md` v10). No code changed. Full check list passed before and after.

**Also in the working tree:** a one-line `README.md` change not made by this session (the pull request sentence); left as it is.
