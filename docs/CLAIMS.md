# Claims and Experiment Ledger

This file records claims before the application has a chance to make them appear inevitable.

## Update rule

When evidence changes a claim, append the result and date. Do not rewrite the original claim to match the outcome.

---

## C-001: Operational classification is useful

**Claim:** Most comments can be assigned to a small set of operational categories that help an author decide what to inspect next.

**Evidence needed:** Human-labeled corpus shows useful agreement and manageable ambiguity.

**Would weaken/falsify:** Large share of comments require bespoke categories or classification does not affect review behavior.

**Status:** UNTESTED

- 2026-10-02: Measurement linked to labeler self-agreement (`LABELING-GUIDE.md`) and `UNCERTAIN` rate. No evidence yet.

## C-002: Prioritization can reduce review workload

**Claim:** Suggested priority can reduce immediate-review volume while preserving consequential comments.

**Evidence needed:** Assisted review reduces inspected items/time while maintaining high consequential recall.

**Would weaken/falsify:** Consequential false negatives remain common or review savings are trivial.

**Status:** UNTESTED

- 2026-10-02: Priority is now policy-computed (ADR-007). Measured on `test-natural` for reduction and `test-enriched` for recall. No evidence yet.
- 2026-10-02 (later): ADR-010 amended. `test-natural` and `test-enriched` are replaced by one prospective `test` set (comments on posts published after preregistration), which measures both reduction and recall. No evidence yet.

## C-003: Explanations improve oversight

**Claim:** A concise explanation helps the human detect incorrect classification or priority decisions.

**Evidence needed:** Human can identify/reverse errors faster or more reliably with explanations than labels alone.

**Would weaken/falsify:** Explanations merely rationalize outputs or increase review time without improving detection.

**Status:** UNTESTED

- 2026-10-02: Test design added: seeded wrong labels, with and without explanation. No evidence yet.

## C-004: Low-priority collapse is safer than hidden filtering

**Claim:** Collapsing low-priority comments while retaining a `Review all` path provides workload reduction without surrendering visibility.

**Evidence needed:** Users can recover missed comments and understand what was collapsed.

**Would weaken/falsify:** Collapsed groups are effectively never inspected and consequential misses remain undiscovered.

**Status:** UNTESTED

- 2026-10-02: Requires review-event instrumentation, now in V1 scope. No evidence yet.

## C-005: Historical interaction context may improve triage

**Claim:** Prior conversation history with a platform identity can improve interpretation of some comments.

**Evidence needed:** Context-dependent examples where classification/priority materially improves with relevant history.

**Would weaken/falsify:** History adds noise, creates reputation bias, or does not improve consequential recall.

**Status:** DEFERRED UNTIL BASIC CLASSIFIER EXISTS

## C-006: Source-neutral core is justified

**Claim:** A source-adapter architecture can support a second publishing platform without corrupting source-specific semantics.

**Evidence needed:** CoderLegion or another source can be added after V1 with localized adapter changes and explicit capability gaps.

**Would weaken/falsify:** Canonical model repeatedly requires source-specific hacks or normalization destroys meaning.

**Status:** DEFERRED UNTIL SECOND SOURCE

## C-007: Propagation is a meaningful outcome

**Claim:** Recording downstream effects of comments provides more useful information than comment count alone for this author's workflow.

**Evidence needed:** Real comments can be linked to corrections, experiments, code/spec changes, future articles, or retained claims after investigation.

**Would weaken/falsify:** Propagation is too subjective or burdensome to record consistently.

**Status:** UNTESTED

---

Claims below were added on 2026-10-02 during scoping v2.

## C-008: The model adds value beyond heuristics

**Claim:** LLM-assisted classification (B2) achieves materially better consequential recall at the same review reduction, or better reduction at the same recall, than a rule-based heuristic (B1).

**Evidence needed:** B2 outperforms B1 on the sealed test sets, with the difference visible in counts, not only percentages.

**Would weaken/falsify:** B1 matches B2 within one or two consequential comments on the test sets.

**Status:** UNTESTED

- 2026-10-02: Measured on the prospective `test` set (ADR-010 amended), where B1 and B2 run in shadow mode with sealed outputs. No evidence yet.
- 2026-10-08: Provisional, from `dev` (302 labels; tuning set, not the test set). B1 under `pp-v0.1` already matches the oracle ceiling on review reduction (44 of 302 collapsed, as with perfect classes and flags) and surfaces 81 of 84 consequential comments against the oracle's 84. On the claim's two named measures, the room left for B2 to beat B1 on `dev` is therefore at most 3 consequential comments, or reduction beyond the oracle's under `pp-v0.1`, which only a policy change could give. Where B1 is weak is `SURFACE`: 126 comments, 50 of them graded 2 or 3 (39.7%), against the oracle's 55 and 30 of 55. A proposal (`docs/proposals/2026-10-08-surface-co-primary.md`, not yet approved) would make SURFACE size and precision co-primary measures, which would change what "materially better" in this claim is measured on. The claim text is unchanged.

## C-009: The problem exists at this author's volume

**Claim:** The author's DEV comment volume is high enough that chronological review imposes a real attention cost.

**Evidence needed:** Observed comment counts per week and per post, and measured time for a chronological review batch.

**Would weaken/falsify:** Chronological review of a typical week takes only a few minutes. In that case the project continues as a methodology study and is described that way.

**Status:** MEASURED, MIXED. Volume and chronological reading time are measured (2026-10-04 entry). The typical week took under 4 minutes to read, which meets the falsification condition; the busy week took about 17.5 minutes, which does not. The Stage 0 gate decision (continue, or continue as a methodology study) is the author's and is not yet recorded.

- 2026-10-02: Volume measured from probe run `20261002T171152Z` (all 138 published DEV articles; report `baseline-20261002T171152Z`, git-ignored). The run contains no deletion placeholders and none of the hand-test comments.
  - **Totals:** 707 comments returned: 432 from others and 275 by the author (39% of all comments, excluded under ADR-011).
  - **Per article (comments from others):** 74 of 138 articles have none. Median 0, mean 3.1, p90 7, max 62. The top article holds 14.4%, the top 3 hold 34.0%, the top 10 hold 53.9%, and 9 articles cover half of all comments from others.
  - **Per week (comments from others, complete weeks only):** there was almost no volume before March 2026.
    - Trailing 52 weeks: median 0.5, mean 7.4, p90 22, max 60.
    - Trailing 13 weeks: median 7, mean 17.0, p90 44, max 60.
  - **Reading:** the volume is recent and spiky, not steady. Several weeks in the last 13 reached 39 to 60 comments from others, which is enough for chronological review to plausibly cost real attention, but this has not been measured yet.
  - **Weeks chosen for timing:** typical week 2026-09-21 to 2026-09-27 (7 comments from others); busy week 2026-09-07 to 2026-09-13 (44).
  - **Not yet established:** the attention cost itself, which needs a timed chronological review of both weeks. The claim is neither supported nor weakened until then.
- 2026-10-03: The typical week to time is replaced. 2026-09-21 had been re-read twice (once in a practice timing run, which was not recorded as evidence), so a timing of it would no longer be a usable lower bound. The replacement is 2026-07-27 to 2026-08-02 (7 comments from others), the complete week closest to the trailing-13-week median of run `20261002T171152Z`, excluding 2026-09-21 and 2026-09-07. The busy week is unchanged. Only timings confirmed as valid count; practice runs are kept apart. No review time measured yet.
- 2026-10-04: Both chronological timings were recorded as valid on 2026-10-03, from probe run `20261003T141450Z`, and are entered here a day late: every session summary after 2026-10-03 listed them as open. Figures are from the two records under `reports/timing/` (git-ignored), counts and times only.
  - **Typical week, 2026-07-27 to 2026-08-02:** 7 of 7 comments from others read, complete, in 228.4 seconds (3.8 minutes; 32.6 seconds per comment).
  - **Busy week, 2026-09-07 to 2026-09-13:** 44 of 44 read, complete, in 1051.7 seconds (17.5 minutes; 23.9 seconds per comment).
  - **What the figures are.** Both are re-reads of historical weeks, so they are lower bounds on first-read cost (`EVALUATION.md`, Effort measurement). The comments in both weeks had been seen before, when they arrived; how many times each week had been read before its timing is not recorded. No practice timing of either week is on record, and both were timed before any comment in them was labeled (the first labeling batch started at 18:44 UTC that day). They cover reading only, oldest first with each reply chain: not deciding what to do, replying, or following up.
  - **Reading against the falsification condition.** The typical week falls in the "only a few minutes" range named above: under 4 minutes. The busy week does not: about 17.5 minutes for one week's comments. Weekly volume is spiky (trailing 13 weeks: median 7, max 60), so the cost is small in an ordinary week and real in a busy one. On this evidence the claim holds for busy weeks and not for a typical week.
  - **Consequence.** The Stage 0 gate (`ROADMAP.md`) asks for an explicit decision when C-009 shows trivial volume. That decision, to continue as planned or to continue and describe the project as a methodology study, is the author's and is not recorded here.
- 2026-10-04 (later): Stage 0 gate decision by the author: **continue as planned.** This supersedes "not yet recorded" in the status line above, which is left as written. The split this evidence suggests (cheap in a typical week, costly in a busy one) becomes a claim of its own, C-012, tested on the prospective test period.

## C-010: Prospective and retrospective judgment largely agree

**Claim:** For most comments, the author's judgment of consequentiality without hindsight matches judgment with hindsight.

**Evidence needed:** Agreement between prospective and retrospective grades across the labeled corpus.

**Would weaken/falsify:** Many comments become consequential only in hindsight, which would limit what any triage system can achieve and should change how the result is framed.

**Status:** UNTESTED

- 2026-10-07: Provisional, from 302 of 458 `dev` labels (`EVALUATION.md`, 2026-10-07 label summary). Where both grades exist (293), the consequential binary agrees in 262; 4 comments are consequential only in hindsight and 27 only prospectively. By label order: publication order (first 150) 140 of 147 agree, 3 only in hindsight, 4 only prospectively; shuffled order (next 152) 122 of 146 agree, 1 only in hindsight, 23 only prospectively. The direction named in the falsifier (consequential only in hindsight) is rare in both. The shuffled labels show more disagreement in the other direction, whose cause (sample, guide version, or labeler experience) these labels cannot separate. These are historical comments, mostly labeled after replying, so they say little about the prospective test set, where C-010 is measured.

---

Claims below were added on 2026-10-03 (session 5).

## C-011: The author's judgment drifts over months

**Claim:** The author's judgment of what is consequential drifts measurably over months, beyond short-term inconsistency.

**Evidence needed:** Re-labeling a random `dev` sample at least 3 months after the original labels (naturally, at the end of the prospective test period), compared against the 14-day self-agreement baseline (`LABELING-GUIDE.md`).

**Would weaken/falsify:** Long-term agreement matches 14-day agreement.

**Status:** UNTESTED

---

Claims below were added on 2026-10-04 (session 7).

## C-012: The value of assisted triage is concentrated in high-volume weeks

**Claim:** Assisted triage delivers most of its value in high-volume weeks; in typical weeks chronological review is already cheap.

**Evidence needed:** Test-period results reported separately for weeks above and below the trailing-13-week median volume.

**Would weaken/falsify:** Benefit is similar across volume levels, or negligible in busy weeks too.

**Status:** UNTESTED

- 2026-10-04: Added after the C-009 timings (typical week 3.8 minutes, busy week 17.5 minutes, both re-reads) and the author's decision to continue as planned. Measured as a secondary analysis in `EVALUATION.md` (volume split). No evidence yet.

---

Claims below were added on 2026-10-07 (session 8), as proposed in `FUTURE-FEATURES.md` (v2). Each belongs to a feature gated on the Stage 3 result; none is tested in V1.

## C-013: Assisted suggestions make propagation recording sustainable

**Claim:** Assisted suggestions make propagation recording sustainable.

**Evidence needed:** Over a defined period, the share of consequential comments with a recorded propagation outcome, with and without suggestions, and the share of suggestions the author accepts.

**Would weaken/falsify:** Recording rates stay low with suggestions, or most suggestions are rejected.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 2 (propagation ledger). No evidence yet.

## C-014: Rediscovery surfaces material the author judges worth revisiting

**Claim:** Rediscovery surfaces material the author judges worth revisiting.

**Evidence needed:** For rediscovery digests over a defined period, the share of surfaced items the author marks as worth revisiting, and how many lead to a recorded action (reply, propagation, new work).

**Would weaken/falsify:** Most surfaced items are judged not worth revisiting, or none leads to action.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 3 (rediscovery). No evidence yet.

## C-015: Reply context improves the author's replies

**Claim:** Reply context improves the author's replies.

**Evidence needed:** Over a defined period, how often the author opens the panel, how often a shown item is marked relevant, and how often the author reports that it changed or informed the reply.

**Would weaken/falsify:** The panel is rarely opened, or shown items are mostly judged irrelevant.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 4 (reply context and position history). No evidence yet.

## C-016: Position summaries are faithful to their sources

**Claim:** Position summaries are faithful to their sources.

**Evidence needed:** An audit of generated position summaries, checking every statement against its cited excerpt.

**Would weaken/falsify:** Summaries contain statements not supported by their citations, or the author frequently judges them to misrepresent their views.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 4 (reply context and position history). No evidence yet.

## C-017: Duplicate-question clustering reduces repeated answering at high volume

**Claim:** Duplicate-question clustering reduces repeated answering at high volume.

**Evidence needed:** On a high-volume account, the share of questions that fall into clusters of two or more, the author's judgment of cluster correctness on a random sample, and the reduction in separate answers written.

**Would weaken/falsify:** Few questions cluster, or sampled clusters are frequently judged wrong.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 5 (duplicate-question clustering). No evidence yet.

## C-018: An unanswered-questions queue reduces questions left unanswered

**Claim:** An unanswered-questions queue reduces questions left unanswered.

**Evidence needed:** Over a defined period, the share of questions from others that receive a reply or a handled mark, compared with a prior period without the queue.

**Would weaken/falsify:** The unanswered share does not change, or the queue is rarely opened.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 6 (unanswered-questions queue). No evidence yet.

## C-019: Feedback extraction captures product signal that would otherwise be lost

**Claim:** Feedback extraction captures product signal that would otherwise be lost.

**Evidence needed:** On a team account, the number of comments exported per period, the share of exports the team keeps (not closed as invalid), and the team's estimate of how many would have been captured by hand.

**Would weaken/falsify:** Few comments qualify, most exports are closed as invalid, or the team already captures the same signal by hand.

**Status:** DEFERRED UNTIL STAGE 3 GATE

- 2026-10-07: Added from `FUTURE-FEATURES.md`, feature 7 (feedback extraction through output adapters). No evidence yet.


## Future features (docs only, no code):
- Add docs/FUTURE-FEATURES.md (already on disk) to the README reading
  order, after LABELING-AT-SCALE.md.
- Append C-013 through C-016 to CLAIMS.md exactly as proposed in
  FUTURE-FEATURES.md, in the existing format, each with status
  "DEFERRED UNTIL STAGE 3 GATE". Do not change C-001 to C-012.
- SCOPE.md: add one Future candidates entry pointing to
  FUTURE-FEATURES.md (spike insurance, propagation ledger, rediscovery,
  reply context and position history), gated on the Stage 3 result,
  noting that grouping by commenter remains excluded without the C-005
  ADR.
- ROADMAP.md: add the four features to Deferred, in the suggested order
  from FUTURE-FEATURES.md.
