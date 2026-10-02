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

## C-009: The problem exists at this author's volume

**Claim:** The author's DEV comment volume is high enough that chronological review imposes a real attention cost.

**Evidence needed:** Observed comment counts per week and per post, and measured time for a chronological review batch.

**Would weaken/falsify:** Chronological review of a typical week takes only a few minutes. In that case the project continues as a methodology study and is described that way.

**Status:** PARTIALLY MEASURED. Volume measured; chronological review time not yet measured.

- 2026-10-02: Volume measured from probe run `20261002T171152Z` (all 138 published DEV articles; report `baseline-20261002T171152Z`, git-ignored). The run contains no deletion placeholders and none of the hand-test comments.
  - **Totals:** 707 comments returned: 432 from others and 275 by the author (39% of all comments, excluded under ADR-011).
  - **Per article (comments from others):** 74 of 138 articles have none. Median 0, mean 3.1, p90 7, max 62. The top article holds 14.4%, the top 3 hold 34.0%, the top 10 hold 53.9%, and 9 articles cover half of all comments from others.
  - **Per week (comments from others, complete weeks only):** there was almost no volume before March 2026.
    - Trailing 52 weeks: median 0.5, mean 7.4, p90 22, max 60.
    - Trailing 13 weeks: median 7, mean 17.0, p90 44, max 60.
  - **Reading:** the volume is recent and spiky, not steady. Several weeks in the last 13 reached 39 to 60 comments from others, which is enough for chronological review to plausibly cost real attention, but this has not been measured yet.
  - **Weeks chosen for timing:** typical week 2026-09-21 to 2026-09-27 (7 comments from others); busy week 2026-09-07 to 2026-09-13 (44).
  - **Not yet established:** the attention cost itself, which needs a timed chronological review of both weeks. The claim is neither supported nor weakened until then.

## C-010: Prospective and retrospective judgment largely agree

**Claim:** For most comments, the author's judgment of consequentiality without hindsight matches judgment with hindsight.

**Evidence needed:** Agreement between prospective and retrospective grades across the labeled corpus.

**Would weaken/falsify:** Many comments become consequential only in hindsight, which would limit what any triage system can achieve and should change how the result is framed.

**Status:** UNTESTED
