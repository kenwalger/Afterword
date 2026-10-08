# Dev-set evaluation: B1 and Llama on the labeled `dev` comments (2026-10-08)

**Status:** provisional evidence on the development set. Not a measurement, not a model choice, and not a policy choice. Nothing is chosen here. The registered measurement is on the prospective, sealed `test` set (ADR-010, `EVALUATION.md`).

## Read this first: why these numbers flatter and mislead

Every figure below carries these caveats. They are not footnotes; each one can move a result by more than the differences between conditions.

1. **Historical comments.** Every comment was posted before the experiment began, on posts that had already run their course. The test set will be comments on posts published after preregistration.
2. **Labels made with hindsight, mostly after replying.** The author had already read every comment, and had replied to most: 192 of the 302 labels (63.6%) were made after the author's own reply existed (`replied_before_labeling`), 108 of 150 in publication order and 84 of 152 shuffled. Prospective grades of historical comments are reconstructions (C-010).
3. **The first 150 labels are in publication order.** They are the comments on the earliest-published posts, labeled under `lg-v0.2` and `tax-v0.1`. The other 152 are a seeded shuffle of posts (`--posts random --seed 20261004`), labeled under `lg-v0.3` and `tax-v0.2`. The two halves differ in sample, guide version, taxonomy version, and labeler experience at once, so every result is also reported for each half.
4. **Tuning on the same set.** `hb-v0.2`'s length threshold was chosen on these 302 labels (`EVALUATION.md`, "B1 on `dev`"), and the prompt, policy, and taxonomy are being iterated on `dev`. Scores on the set a condition was tuned on overstate how it will do on new comments.
5. **One labeler, 302 of 458 comments.** 156 stored comments from others are unlabeled. No calibration or self-agreement labels exist yet.
6. **Small counts.** Every share comes with its count and a Wilson 95% interval. A difference of a few comments is not a finding.

## Setup

- **Store:** runs `20261003T141450Z` then `20261007T224849Z` ingested; 458 live comments from others on 140 posts. No comment is `EDITED`, so the edit rule never fires.
- **Labels:** 302 analysis labels (`fixtures/labels/unfrozen/`, git-ignored; 302 initial, 0 calibration), all from run `20261003T141450Z`. Graded 2 or 3: 84 (39 in publication order, 45 shuffled).
- **B1:** `hb-v0.2`, all 458 classified.
- **B2 candidate:** `llama3.1:8b-instruct-q4_K_M`, digest `46e0c10c039e...`, prompt `pr-v0.2`, taxonomy `tax-v0.2`, normalization `norm-v0.1`, pre-check `pc-v0.1`, options `num_ctx=4096;num_predict=200;seed=20261003;temperature=0`. Run by the author in their own terminal; finished 2026-10-08 07:05 UTC; 458 classified, 458 `OK`. Qwen's full pass was skipped by agreement; its 50-comment subset result is in `docs/friction-log/session-8.md`.
- **Policies:** `pp-v0.1` (applied when classifying) and the candidate `pp-v0.2` (model-set `NEEDS_THREAD_CONTEXT` and `REFERENCES_SPECIFIC_CLAIM` informational), applied offline to the cached classifications. Confidence is not passed to the policy; the floor is unset in both versions.
- **Oracle:** the policy applied to the labels themselves (class and labeled flags, deterministic code and link flags), on the same 302.
- **How it was computed:** `afterword evaluate` and `afterword dev-analysis` (`afterword.service.analyze_dev`), offline, no model call. Reports in `reports/eval/` (git-ignored, counts only). No comment text was read in producing any of this; every figure is a count.

## 1. What decided each tier

`rule_applied` is the first rule, in the order of `PRIORITY-POLICY.md`, whose tier is the final tier. An override is recorded whenever it reaches the final tier, even if the class default would have given the same tier, so "decided by an override" is not the same as "raised by an override". The raises are counted separately below.

### All 458 comments from others

| Rule applied | B1 `hb-v0.2` (either policy) | Llama, `pp-v0.1` | Llama, `pp-v0.2` |
| --- | --- | --- | --- |
| `class_default:CORRECTION` | 125 | 14 | 14 |
| `class_default:CHALLENGE_OR_COUNTEREXAMPLE` | 0 | 142 | 142 |
| `class_default:TECHNICAL_QUESTION` | 60 | 32 | 32 |
| `class_default:OPPORTUNITY` | 0 | 11 | 11 |
| `class_default:DIRECT_QUESTION` | 11 | 0 | 2 |
| `class_default:TECHNICAL_EXTENSION` | 18 | 91 | 122 |
| `class_default:CONVERSATIONAL` | 80 | 18 | 19 |
| `class_default:LIGHTWEIGHT_ACKNOWLEDGMENT` | 77 | 26 | 28 |
| `class_default:LIKELY_SPAM_OR_NOISE` | 0 | 1 | 11 |
| `override:possible_instruction_text` | 3 | 10 | 10 |
| `override:reply_to_author` | 84 | 67 | 67 |
| `override:needs_thread_context` | | 44 | |
| `override:references_specific_claim` | | 2 | |
| **Tiers: SURFACE / QUEUE / COLLAPSED** | 188 / 193 / 77 | 209 / 222 / 27 | 209 / 210 / 39 |

On the 302 labeled comments, the same counts are: B1 `CORRECTION` 83, `TECHNICAL_QUESTION` 41, `CONVERSATIONAL` 46, `TECHNICAL_EXTENSION` 16, `DIRECT_QUESTION` 7, acknowledgment 45, `reply_to_author` 62, pre-check 2. Llama under `pp-v0.1`: challenge 96, extension 58, question 25, acknowledgment 16, `CORRECTION` 12, conversational 11, opportunity 4, spam 1, `reply_to_author` 44, `needs_thread_context` 28, `possible_instruction_text` 5, `references_specific_claim` 2. Under `pp-v0.2` the two judgment-flag rules disappear: extension 78, acknowledgment 18, spam 7, `DIRECT_QUESTION` 2, everything else unchanged.

### Raises, not just decisions

- **Model-set flags (Llama, labeled comments):** under `pp-v0.1` they raised 9 comments above what the class, structure, and pre-check give, all 9 graded 0 or 1 (8 of them in the publication-order labels). Under `pp-v0.2`, 1 (the model's own `POSSIBLE_INSTRUCTION_TEXT`), graded below 2. B1 sets no judgment flags.
- **Llama sets the judgment flags on more than half the labeled comments** (`REFERENCES_SPECIFIC_CLAIM` 173 of 302, 67 agreeing with the label; `NEEDS_THREAD_CONTEXT` 164, 55 agreeing), but they raise only 9, because most of those comments are already at `QUEUE` or above by class. `REFERENCES_SPECIFIC_CLAIM` against `tax-v0.1` labels: set 84, agree 55 (82 labeled); against `tax-v0.2` labels: set 89, agree 12 (18 labeled).

### The pre-check on real comments

The author's posts are largely about AI, so ordinary comments about prompts and models could trip `pc-v0.1`.

- **It fired on 3 of 458 comments from others.** Rules matched: `system_prompt` 2 (a phrase such as "system prompt" or "system message"), `taxonomy_name` 1 (a taxonomy class or flag name in capitals).
- **2 of the 3 are labeled; neither is consequential** (one graded 0, one graded 1; one `CONVERSATIONAL`, one `DIRECT_QUESTION`). The author's own labels set `POSSIBLE_INSTRUCTION_TEXT` on 1 comment.
- **What it cost:** the pre-check alone raised 1 comment to `SURFACE` under B1 and 2 under Llama (1 of them labeled, graded below 2). The other firings were on comments already at `SURFACE` by class.
- **Llama set `POSSIBLE_INSTRUCTION_TEXT` itself on 7 comments,** none of them among the pre-check's 3; 3 are labeled, none consequential. The model, not the deterministic check, is the larger source of instruction flags on this set.
- **Reading:** the hypothesis holds in kind (the `system_prompt` rule matched ordinary AI discussion) but the count is small: at most 2 `SURFACE` places of 458. Nothing here argues for loosening the check, which exists for the adversarial case (ADR-008).
- **English only.** Every `pc-v0.1` pattern is English, so a non-English instruction bypasses it. Adversarial case `adv-110` is the known example. On this set, the 2 comments detected as non-English (section 5) did not trip it.

## 2. Class confusion: Llama against the labels

Rows: Llama's predicted class (all 302 `OK`). Columns: the label. Counts only.

| Predicted \ Label | CORR | CHAL | TQ | OPP | DQ | TE | CONV | ACK | SPAM | UNC | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CORRECTION` | 1 | 0 | 0 | 0 | 0 | 6 | 4 | 1 | 0 | 0 | 12 |
| `CHALLENGE_OR_COUNTEREXAMPLE` | 1 | 4 | 16 | 0 | 0 | 49 | 23 | 2 | 0 | 1 | 96 |
| `TECHNICAL_QUESTION` | 0 | 0 | 14 | 0 | 4 | 2 | 4 | 2 | 0 | 0 | 26 |
| `OPPORTUNITY` | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 4 | 0 | 6 |
| `DIRECT_QUESTION` | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 1 | 0 | 0 | 5 |
| `TECHNICAL_EXTENSION` | 0 | 0 | 15 | 0 | 0 | 37 | 40 | 14 | 3 | 0 | 109 |
| `CONVERSATIONAL` | 0 | 0 | 0 | 0 | 0 | 4 | 5 | 4 | 1 | 0 | 14 |
| `LIGHTWEIGHT_ACKNOWLEDGMENT` | 0 | 0 | 1 | 0 | 1 | 2 | 6 | 15 | 1 | 0 | 26 |
| `LIKELY_SPAM_OR_NOISE` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 8 |
| `UNCERTAIN` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | 2 | 4 | 46 | 1 | 5 | 100 | 86 | 40 | 17 | 1 | 302 |

Agreement: 84 of 302 (27.8%). B1 `hb-v0.2` agrees on 77 of 302 (25.5%), with different errors: it calls 83 comments `CORRECTION` (2 agree) and never predicts challenge, opportunity, spam, or `UNCERTAIN`.

**Where Llama's `SURFACE` comes from (labeled comments):** 142 at `SURFACE` under either policy. 137 by class default: challenge 96, question 25, `CORRECTION` 12, opportunity 4. 5 by `POSSIBLE_INSTRUCTION_TEXT` (2 the pre-check, 3 the model), none consequential. **The inflation comes from class assignment, not from overrides,** and above all from `CHALLENGE_OR_COUNTEREXAMPLE`: 96 predicted, 4 labeled. Of the 96, 49 are labeled `TECHNICAL_EXTENSION`, 23 `CONVERSATIONAL`, 16 `TECHNICAL_QUESTION`.

**And from the same misclassification, more consequential comments reach `SURFACE` than the oracle allows.** Of the 55 consequential comments at Llama's `SURFACE`, 41 were predicted challenge. Of the 49 labeled extensions Llama called a challenge, 28 are graded 2 or 3 (57%), against 21 of the other 51 labeled extensions (41%). Read as a class, the call is wrong; read as a signal, "this extension pushes back on something" carries some information about consequence. Two cells of one confusion matrix on hindsight labels are not evidence for a design, but the observation bears on the session 9 question.

**Where Llama loses review reduction:** it predicts 26 acknowledgments and 8 spam against 40 and 17 labeled. Labeled acknowledgments go mostly to extension (14) and conversational (4); labeled spam to opportunity (4) and extension (3). Those comments then sit at `QUEUE` or `SURFACE`.

## 3. The five primary measures

On the 302 labeled comments. Counts first; Wilson 95% intervals in brackets.

| Condition | Consequential recall | Review reduction | SURFACE size | SURFACE precision | SURFACE capture |
| --- | --- | --- | --- | --- | --- |
| B1 `hb-v0.2`, `pp-v0.1` or `pp-v0.2` | 81 of 84 (96.4%) [90.0, 98.8] | 45 of 302 (14.9%) [11.3, 19.4] | 126 (41.7%) | 50 of 126 (39.7%) [31.6, 48.4] | 50 of 84 (59.5%) [48.8, 69.4] |
| Llama, `pp-v0.1` | 84 of 84 (100%) [95.6, 100] | 17 of 302 (5.6%) [3.5, 8.8] | 142 (47.0%) | 55 of 142 (38.7%) [31.1, 46.9] | 55 of 84 (65.5%) [54.8, 74.8] |
| Llama, `pp-v0.2` | 84 of 84 (100%) [95.6, 100] | 25 of 302 (8.3%) [5.7, 11.9] | 142 (47.0%) | 55 of 142 (38.7%) [31.1, 46.9] | 55 of 84 (65.5%) [54.8, 74.8] |
| Oracle, `pp-v0.1` | 84 of 84 | 44 of 302 (14.6%) [11.0, 19.0] | 55 (18.2%) | 30 of 55 (54.5%) [41.5, 67.0] | 30 of 84 (35.7%) [26.3, 46.4] |
| Oracle, `pp-v0.2` | 84 of 84 | 51 of 302 (16.9%) [13.1, 21.5] | 55 (18.2%) | 30 of 55 (54.5%) [41.5, 67.0] | 30 of 84 (35.7%) [26.3, 46.4] |

### By post order

| Condition | Order | Recall | Reduction | SURFACE | Precision | Capture |
| --- | --- | --- | --- | --- | --- | --- |
| B1 `hb-v0.2` | publication (150) | 36 of 39 | 25 (16.7%) | 63 | 27 of 63 | 27 of 39 |
| | shuffled (152) | 45 of 45 | 20 (13.2%) | 63 | 23 of 63 | 23 of 45 |
| Llama, `pp-v0.1` | publication | 39 of 39 | 10 (6.7%) | 71 | 27 of 71 | 27 of 39 |
| | shuffled | 45 of 45 | 7 (4.6%) | 71 | 28 of 71 | 28 of 45 |
| Llama, `pp-v0.2` | publication | 39 of 39 | 17 (11.3%) | 71 | 27 of 71 | 27 of 39 |
| | shuffled | 45 of 45 | 8 (5.3%) | 71 | 28 of 71 | 28 of 45 |
| Oracle, `pp-v0.1` | publication | 39 of 39 | 19 (12.7%) | 28 | 16 of 28 | 16 of 39 |
| | shuffled | 45 of 45 | 25 (16.4%) | 27 | 14 of 27 | 14 of 45 |
| Oracle, `pp-v0.2` | publication | 39 of 39 | 22 (14.7%) | 28 | 16 of 28 | 16 of 39 |
| | shuffled | 45 of 45 | 29 (19.1%) | 27 | 14 of 27 | 14 of 45 |

### What the five measures say together

- **Recall:** Llama misses none of the 84; B1 misses 3, all in the publication-order labels and the same 3 since `hb-v0.1`. Three comments is the whole difference, inside both intervals.
- **Reduction:** Llama collapses far less than B1 or the oracle: 17 (or 25 under `pp-v0.2`) against 45 and 44. Under `pp-v0.1` Llama gives up about two thirds of the reduction the oracle allows; `pp-v0.2` recovers 8 collapses, none consequential.
- **`SURFACE`:** both B1 and Llama put more than 40% of comments at `SURFACE`, against the oracle's 18%. Their precision is about the same (39.7% and 38.7%) and below the oracle's 54.5%. Their capture is higher than the oracle's (59.5% and 65.5% against 35.7%), because they surface more of everything: capture above the oracle is not better classification, it is a larger `SURFACE`.
- **`pp-v0.2`** changes only reduction, and only for Llama: +8 collapsed, no consequential comment lost, `SURFACE` unchanged. The judgment flags it neutralizes raised 9 comments, all graded 0 or 1.
- **Neither condition is near the oracle on all five at once.** B1 matches the oracle's reduction with a `SURFACE` more than twice its size; Llama has perfect recall and the highest capture, with the smallest reduction and the largest `SURFACE`.

## 4. What this does not say

- Anything about the `test` set, or about comments the conditions were not tuned on.
- That Llama is B2, or that `pp-v0.2` is the policy. Both choices are made before preregistration and recorded with their reasons (`EVALUATION.md`, "Which model is B2").
- That class confusion this large is a property of the model rather than of the prompt, the taxonomy's boundaries, or the labels. The labels are one person's, made with hindsight.
- How consequence should reach the tier. Section 2's observation is an input to that question (session 9), not an answer.

## 5. Languages (measured, not acted on)

Detector: `py3langid` 0.4.0, local and deterministic (analysis dependency group only). Run on each comment's normalized prose (code and link targets removed). Guardrails set by the author before counting: under 40 characters of prose is "too short to classify"; a normalized confidence under 0.80 is "uncertain". The 0.80 threshold was chosen on a handful of synthetic sentences in six languages, before any real comment was counted.

| Bucket | Comments | Labeled | Graded 2 or 3 | Llama `pp-v0.1` S / Q / C | Llama `pp-v0.2` S / Q / C |
| --- | --- | --- | --- | --- | --- |
| `en` | 435 | 290 | 84 | 205 / 211 / 19 | 205 / 204 / 26 |
| `vi` | 2 | 0 | | 2 / 0 / 0 | 2 / 0 / 0 |
| uncertain | 5 | 3 | 0 | 1 / 4 / 0 | 1 / 0 / 4 |
| too short | 16 | 9 | 0 | 1 / 7 / 8 | 1 / 6 / 9 |

- **Non-English (detected):** 2 comments, both detected as Vietnamese, neither labeled. Llama classified both as `CHALLENGE_OR_COUNTEREXAMPLE`, so both are at `SURFACE`; the pre-check matched neither. Detection on 2 comments is not verified (no text was read), so "Vietnamese" is the detector's answer, not a finding.
- **Uncertain:** 5; the 3 labeled are all spam, graded 0.
- **Too short:** 16; the 9 labeled are acknowledgments, conversational, or spam, all graded 0.
- **Labels read via translation:** 0. The field (`read_via_translation`) did not exist when these labels were made; it exists from `lg-v0.5`.
- **Pre-check:** English-only patterns; see section 1.

## 6. AI-authorship disclosure fields (measured, not acted on)

- **Values across stored comments:** run `20261007T224849Z`, the source of every stored comment's current payload, carries `ai_disclosure_label` and `ai_disclosure_level` on all 750 comment nodes, with exactly one pair of values: `Not Disclosed` / `not_disclosed`, 750 of 750 (459 of them not by the author: the 458 live comments from others and the deletion placeholder, whose author is unknown). The older run had them on 189 of 714 nodes, the same pair every time.
- **Cross-tabulated with the labels:** every one of the 302 labeled comments has `not_disclosed`, so the cross-tab is the label distribution itself (class and grade tables in `EVALUATION.md`). The fields carry no information about these comments.
- **What DEV says they mean:** see `docs/API-CAPABILITY-MATRIX.md` (row "Comment AI disclosure fields", 2026-10-08) and the proposal `docs/proposals/2026-10-08-ai-authorship-disclosed-flag.md`.
