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

## Session 11: Part B, decisions after the checkpoint, then design analysis (2026-10-18)

### 2026-10-18 19:17 - ADR-009 amended: a second DEV deletion behavior

**Platform:** DEV

**Type:** SURPRISE

**Class:** PRODUCT

**Task:** Record the author's decision on the two placeholders first seen in run `20261018T173927Z` (entry "Two deletion placeholders first seen as placeholders", above).

**Expectation:** As decided by the author: record them as evidence, change no handling.

**Observation:** The author's reading: a second DEV deletion behavior, in which deleted comments with no replies remain as placeholders and are still counted in `comments_count`, unlike the author self-deletion hand test, where such a comment disappeared. Likely cause moderation or spam removal, unconfirmed.

**Evidence:** Run `20261018T173927Z` (`probe-findings.json`: `deletion_observation`, `count_reconciliation`); the store's lifecycle events for the run.

**Workaround:** None needed: the placeholder rule matched them as it stands.

**Consequence:** ADR-009 amended 2026-10-18 (Context, the amendment note, and two consequences: a placeholder may have no replies; `comments_count` does not reliably exclude placeholders), still provisional. `API-CAPABILITY-MATRIX.md` v6 adds the same evidence to the "Deleted comment representation" and "Comment count on post" rows, which otherwise contradicted the amended ADR. Handling, code, and tests unchanged.

**Follow-up:** Confirm the cause if DEV documents moderation or spam removal, or if a removal by a moderator is observed directly.

### 2026-10-18 19:25 - `pp-v0.2`: free on real comments, costly only for Qwen on synthetic ones

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Part B1: score B1, Llama, and the oracle under `pp-v0.1` and `pp-v0.2` on all labels, and weigh the known cost case.

**Expectation:** `pp-v0.2` adds a few collapses for Llama and none for B1; its cost shows up only as adv-007.

**Observation:** On all 478 labels, `pp-v0.2` moves 12 Llama comments (all graded 0) and 9 oracle comments (graded 0 or 1) from `QUEUE` to `COLLAPSED`, and nothing for B1; `SURFACE` cannot change, since both flags only raise to `QUEUE`. Rescoring the 2026-10-04 synthetic outputs offline: Llama changes on 4 spam cases only; Qwen on 13, including adv-007 and both pre-check-gap injection cases (adv-109, adv-110), which fall from `QUEUE` (already failing the pass condition) to `COLLAPSED`. In every Qwen case the judgment flags had rescued a wrong class by accident.

**Evidence:** `docs/proposals/accepted/2026-10-18-adopt-pp-v0.2.md`; `reports/bench/20261004T2*` (synthetic outputs).

**Workaround:** None.

**Consequence:** The proposal ties adopting `pp-v0.2` to the B2 choice: free with Llama, not with Qwen.

**Follow-up:** The author's decision.

### 2026-10-18 19:30 - Class-default remaps: one stable choice, and it inflates `SURFACE`

**Platform:** Project

**Type:** FRICTION

**Class:** DOMAIN

**Task:** Part B2(a): search class-default mappings, chosen on one half of the posts and reported on the other, with the selection rule fixed in the analysis script before it ran.

**Expectation:** A search over 19,683 mappings would find something that improves `SURFACE` without hurting recall or reduction.

**Observation:** Only `TECHNICAL_EXTENSION` to `SURFACE` is chosen in both folds at the oracle (held-out capture 28 to 66 of 68, precision 61% to 53%, `SURFACE` 19% to 51% of comments), and, once Llama covered all 478, in both folds on Llama's predictions too, where `SURFACE` reaches 79% to 82%. Every other choice changes between folds; three lose consequential comments on the held-out half; a mapping chosen for Llama cuts B1's held-out recall from 67 to 54 of 68. With Llama on 458 comments, its fold-B choice had been different.

**Evidence:** `docs/proposals/accepted/2026-10-18-consequence-to-tier.md`, (a).

**Workaround:** None.

**Consequence:** Class-based mapping cannot exceed the consequential share of the classes it surfaces; the proposal rejects remaps as the answer. This is development evidence on 478 labels.

**Follow-up:** None.

### 2026-10-18 19:30 - The challenge-on-extension observation weakened; Llama's confidence is constant

**Platform:** Project

**Type:** SURPRISE

**Class:** DOMAIN

**Task:** Part B2(b) and (c): the only current evidence for a split of `TECHNICAL_EXTENSION`, and what a model signal could build on.

**Expectation:** The 2026-10-08 observation (57% against 41% consequential) would hold on more labels.

**Observation:** On all 131 labeled extensions: 30 of 55 (54.5%) where Llama says challenge, against 35 of 76 (46.1%) otherwise, with wide overlap; on the labels added since 2026-10-08 it reverses (2 of 6 against 14 of 25). Separately, Llama reports `HIGH` confidence on all 478 classifications. A perfect split would bound the oracle at `SURFACE` 149, precision 119 of 149, capture 119 of 129; the split relabel is 131 comments.

**Evidence:** `docs/proposals/accepted/2026-10-18-consequence-to-tier.md`, (b) and (c).

**Workaround:** None.

**Consequence:** Candidate (b) has a high ceiling and weak current evidence; a self-reported strength is ruled out of candidate (c)'s design.

**Follow-up:** The author's choice among (a), (b), (c), or accepting the ceiling.

### 2026-10-18 19:35 - Self-agreement: only early labels are old enough, and it must come before calibration

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** Part B4: prepare the self-agreement check per `LABELING-GUIDE.md`.

**Expectation:** More than 14 days since the first labels, so a broad pool.

**Observation:** At 19:19 UTC only 107 labels were 14 days old, all in publication order (`lg-v0.2`, `tax-v0.1`). The sample (21 graded 2 or 3 plus 25 random, 2 overlapping) is 44 comments, written to a git-ignored ID list. The same rule on 2026-10-22 would give 104 and include the first shuffled 152, the C-010 outlier. A calibration label would restart the 14-day clock and replace the analysis label, so the check comes first. Under `pp-v0.2` no first-150 label's tier depends on its judgment flags, so little of the planned calibration pass still matters.

**Evidence:** `docs/proposals/accepted/2026-10-18-relabeling-scope.md`; `reports/eval/self-agreement-20261018-s20261018.txt` (git-ignored).

**Workaround:** None.

**Consequence:** No tool yet compares self-agreement labels with the originals (kappa, the binary); needed after the labels exist.

**Follow-up:** The author chooses now (44) or 2026-10-22 (104).

### 2026-10-18 - Session summary

**Goal:** Part A: bring the store up to date and record the final `dev` label summary. Part B: design analysis for the open decisions (policy version, how consequence reaches the tier, B2's identity, relabeling scope), evidence and proposals only.

**Completed:**
- Part A (committed as `5d08a53`): third real ingest (retention reduced eight runs, the hand-test deletion redacted from two), B1 on all 478, `EVALUATION.md` v16 (label summary, accrual 5 to 6 weeks, oracle ceilings), claim entries C-001, C-002, C-010, `ROADMAP.md` v10.
- After the checkpoint: ADR-009 amended 2026-10-18 (a second DEV deletion behavior, the author's decision), `API-CAPABILITY-MATRIX.md` v6.
- Part B, rescored on all 478 after the author's incremental Llama pass: four documents under `docs/proposals/` (adopt `pp-v0.2`; consequence to tier; B2 identity evidence, no recommendation; relabeling scope with the self-agreement list prepared). C-008 entry dated 2026-10-18. No code, policy, taxonomy, or registered text changed.

**Friction discovered:** the prompt's session number; CRLF from scripted edits; remap searches that overfit; self-agreement limited to early labels.

**Delight discovered:** retention and redaction worked as designed on their first real run; the incremental cache made the B2 catch-up a 20-comment job.

**Claims affected:** C-001, C-002, C-008, C-010 (dated entries; no claim text changed).

**ADRs affected:** ADR-009, amended 2026-10-18, still provisional.

**Scope pressure:** a public service function for per-comment analysis rows (the scratch analysis used service internals; deferred); a self-agreement comparison function (needed only once the labels exist); updating the README's findings paragraph and `CLAUDE.md`'s "Current stage" to the 478-label state (the author's documents; not edited).

**Next smallest useful step:** the author's decisions on `pp-v0.2`, the consequence candidates, and the self-agreement date; then B2 and the remaining preregistration versions.

## Session 11: the author's decisions after Part B (2026-10-18)

### 2026-10-18 20:00 - Stage 3a decided: Llama as B2, `pp-v0.2` applied, the ceiling accepted

**Platform:** Project

**Type:** SURPRISE

**Class:** PROJECT

**Task:** Apply the author's five decisions on the Part B proposals.

**Expectation:** Documentation and one constant.

**Observation:**
- **`pp-v0.2` adopted and applied.** `afterword.policy.POLICY_VERSION` is `pp-v0.2`, so `classify` records `pp-v0.2` assignments and `evaluate` scores under it by default; `pp-v0.1` stays available. `PRIORITY-POLICY.md` rewritten as `pp-v0.2`. Four tests that exercised `pp-v0.1` behavior through the default now name `pp-v0.1` explicitly (one of them also checks that every ceiling coincides under `pp-v0.2`), three checks of the default now expect `pp-v0.2`, and one new test, over both flags, checks that they are informational under the applied policy. B1's `pp-v0.2` assignments were recorded from the cache (478, no model involved); stored `pp-v0.1` assignments are kept as recorded.
- **Consequence to tier:** the class-based ceiling is accepted for V1, thresholds to be set against the oracle under `pp-v0.2`; class-default remaps rejected; the extension split and the model signal recorded as V2 candidates in `FUTURE-FEATURES.md` v5, with the author's caution that a hand-made split risks re-encoding the consequence grade, so the open question is whether a classifier can make it.
- **B2 is Llama** (`llama3.1:8b-instruct-q4_K_M`, pinned digest), with B1 as the baseline; the trade-offs are recorded in `EVALUATION.md` v17 and C-008.
- **Self-agreement on or after 2026-10-22,** by the same rule; the 44-ID list of 2026-10-18 is superseded. **The calibration pass is dropped** unless the check shows a problem, because `pp-v0.2` removes most of its effect.
- The four proposals moved to `docs/proposals/accepted/`, each with its decision in the status line; the consequence proposal's own recommendation (try (b) first) is recorded as amended.
- README findings paragraph and `CLAUDE.md` "Current stage" updated to the 478-label state.

**Evidence:** `docs/proposals/accepted/2026-10-18-*.md`; `EVALUATION.md` v17; `PRIORITY-POLICY.md` `pp-v0.2`; `CLAIMS.md` C-002 and C-008 (2026-10-18, later); `ROADMAP.md` v11; `COMMANDS.md` v3.

**Workaround:** None.

**Consequence:** Stage 3a's choices are made; what is left is preregistration work (next entry).

**Follow-up:** The author may record Llama's `pp-v0.2` assignments with `uv run afterword classify --condition b2 --model llama3.1:8b-instruct-q4_K_M` (cache only after the digest check; no comment is sent). Scoring does not need it.

### 2026-10-18 20:05 - What remains before preregistration

**Platform:** Project

**Type:** FRICTION

**Class:** PROJECT

**Task:** List exactly what remains before the preregistration commit (ADR-010, `EVALUATION.md` "Preregistration and the sealed test set", `ROADMAP.md` 3b).

**Expectation:** A short list.

**Observation:**
1. **Self-agreement check** (the author, on or after 2026-10-22): redraw the ID list by the rule (a session, or a small command, since the drawing script was a session scratch file), label it in about three batches, then compare with the originals (Cohen's kappa on class, the consequential binary with every disagreement). The comparison function does not exist yet. If agreement is poor, `LABELING-GUIDE.md` requires relabeling under a revised guide before anything is frozen.
2. **`afterword label --set test`** that selects only comments on posts published after the preregistration commit (`ROADMAP.md` 3b prerequisite; `--set test` must not be used until then).
3. **Shadow mode** (ADR-010): run B1 and B2 weekly on new test comments, write their outputs to a git-ignored file, and commit its SHA-256; nothing shown until accrual stops. It must work before the first test comment arrives. Not built.
4. **The pre-check's two known gaps** (adv-109, adv-110; `ROADMAP.md` 3a, still open): fix them as `pc-v0.2`, or register them as known limitations of the frozen `pc-v0.1`.
5. **Duplicate-flag rule** (`EVALUATION.md`, "Decisions left for preregistration"): strict or recorded repair, frozen with the prompt. Llama produced no malformed output on the 478.
6. **Secondary comparisons:** whether Qwen, the Anthropic path, or neither runs in shadow mode; the Anthropic path needs its model-boundary sign-off first.
7. **The `dev` corpus export and manifest:** `fixtures/corpus/v1/dev.jsonl` (git-ignored) and its hashes in a committed manifest (`ROADMAP.md` Stage 0, unchecked; `fixtures/README.md`, "Freezing"). Not built.
8. **`dev` up to date at the commit:** a fresh probe and ingest just before preregistration; label any comments that arrived since 2026-10-18; classify them with B1 and B2 (incremental).
9. **Accrual estimate and volume split median,** recomputed from that last full probe run and recorded, dated, with its run ID.
10. **Registered thresholds,** numeric, for consequential recall, review reduction, and SURFACE size, precision, and capture, relative to the oracle under `pp-v0.2` on `dev`, written into "Registered thresholds" with the accrual procedure and stopping rule as they stand.
11. **Freeze and record every version:** `tax-v0.2`, `lg-v0.6` (field guide v4), `norm-v0.1`, the pre-check version, `pp-v0.2`, `hb-v0.2`, `pr-v0.2`, Llama's digest and options, the application version.
12. **The preregistration commit,** which starts accrual.

**Evidence:** `ROADMAP.md` 3b; `EVALUATION.md` v17; ADR-010.

**Workaround:** None.

**Consequence:** Items 2, 3, and 7 are code; items 1, 8, and 12 need the author; the rest are decisions and documents.

**Follow-up:** The author orders them.

### 2026-10-18 20:05 - Session summary, after the decisions

The summary above stands for Parts A and B. After it: the author's five decisions were applied (first entry of this section). One code change (`policy.POLICY_VERSION` to `pp-v0.2`) with its tests; no other behavior changed. Claims affected, additionally: C-002 and C-008 (decision entries). ADRs affected: none beyond ADR-009's amendment earlier in the session. Scope pressure: a public command to draw the self-agreement list and a self-agreement comparison function (both needed for item 1; not built in this session). Next smallest useful step: the self-agreement check on or after 2026-10-22.
