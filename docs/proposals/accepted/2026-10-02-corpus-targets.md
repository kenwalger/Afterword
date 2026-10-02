# Proposal: Corpus targets (affects EVALUATION.md and ADR-010)

**Status:** ACCEPTED WITH AMENDMENTS (2026-10-02): Option 2. Applied to `docs/adr/ADR-010-sealed-test-set.md` and `docs/EVALUATION.md` v3. This file is kept as the record of the evidence and the options. Where it differs from the applied text, the ADR and EVALUATION win.

Amendments made on acceptance:

1. `dev` is the full historical corpus.
2. `test` is every comment from others on posts published after the preregistration commit, labeled weekly before shadow-mode classifier output is revealed.
3. Stopping rule: stop accrual when both 20 consequential test comments and 100 total test comments are reached, or 16 weeks after preregistration, whichever comes first. If the cap is hit, the result reports which targets were met, with counts. (First accepted without the 100-comment target; it was restored the same day, before any evidence.)
4. The sizing estimates below are recomputed from the observed `dev` consequential share, and the recomputation is recorded before preregistration.
5. The risks include the author's DEV publishing cadence during the test period.

**Date:** 2026-10-02

## Decision requested

Choose how the sealed test sets are obtained:

- **Option 1: historical only.** Split the existing comments by post into `dev`, `test-natural`, and `test-enriched`, as `EVALUATION.md` describes now.
- **Option 2: historical as dev, prospective test.** All existing comments become `dev`. The test set is made of comments that arrive after preregistration, each labeled before any shadow-mode classifier output for it is revealed.

Labeling is not blocked by this decision. All 432 historical comments from others are labeled under either option, and no classifier exists yet, so there is no classifier output to be blinded from.

## Evidence (aggregates only)

Source: probe run `20261002T171152Z`, the same run as the C-009 baseline (`reports/baseline-20261002T171152Z`, git-ignored). The run has no deletion placeholders and none of the hand-test comments. "From others" excludes the author's comments (ADR-011). Calendar months and post ages were added to the baseline report this session; the earlier figures are unchanged.

### Distribution across posts

| Measure | Value |
| --- | --- |
| Comments from others | 432 |
| Posts | 138 |
| Posts with no comments from others | 74 |
| Posts with at least one | 64 |
| Share held by the top post | 14.4% (62 comments) |
| Share held by the top 3 posts | 34.0% (147) |
| Share held by the top 10 posts | 53.9% (233) |
| Posts needed to reach 50% / 80% | 9 / 27 |

Non-zero per-post counts, descending: 62, 43, 42, 17, 15, 14, 12, 10, 9, 9, 9, 8, 8, then 51 posts with 7 or fewer.

### Comments from others per calendar month (UTC), since March 2026

| Month | Comments from others | Posts published |
| --- | --- | --- |
| 2026-03 | 8 | 8 |
| 2026-04 | 6 | 11 |
| 2026-05 | 91 | 18 |
| 2026-06 | 61 | 16 |
| 2026-07 | 7 | 11 |
| 2026-08 | 124 | 14 |
| 2026-09 | 98 | 14 |
| 2026-10 (first 2 days) | 19 | 2 |

Before March 2026 there are 18 comments from others in total, spread over 2017 to 2024.

### Weekly rate (trailing 13 complete weeks, to 2026-09-27)

Weekly counts, oldest first: 6, 1, 0, 0, 7, 1, 19, 60, 39, 13, 44, 24, 7. Total 221; mean 17.0; median 7; p90 44; max 60.

### When comments arrive

| Post age when the comment arrived | All history | Trailing 13 weeks |
| --- | --- | --- |
| 0 to 7 days | 392 (90.7%) | 209 (94.6%) |
| 8 to 30 days | 27 | 11 |
| 31 to 90 days | 6 | 1 |
| 91 to 365 days | 3 | 0 |
| More than 365 days | 4 | 0 |

Comments arrive almost entirely in the first week after a post is published. Volume therefore depends on the author continuing to publish. Of the 94 posts published since March, 39 have no comments from others (median 1, mean 4.4 per post).

## The assumption this proposal cannot avoid

Neither option can be sized without the share of comments graded consequential (prospective grade 2 or 3). No labels exist, so this proposal **assumes** it and shows the sensitivity. The working assumption is **15%**, with **10% to 20%** as the plausible range and 5% and 30% as outer cases. This is a guess, not an estimate. Labeling the historical comments, which happens under either option, replaces it with an observed share. Every number below that depends on the share should be recomputed then, before preregistration.

## Option 1: historical only

### Achievable split by post

Splitting by post means the three largest posts (62, 43, 42) decide much of the composition of any set they land in.

- **`test-natural` (target 100 to 150).** In 10,000 random post-level draws that stop once 100 comments are reached, the set size had a median of 105 (p90 135). 72% of draws included one of the top three posts. In the median draw, the largest single post made up 40% of the set (58% at p90). A "natural-rate" set is in practice one or two threads plus small posts.
- **`test-enriched` (at least 20 consequential).** Oversampling likely-consequential comments must still be done by whole post. With human labels available before any classifier runs, posts can be chosen by their consequential count, which ADR-010 permits but which ties the set to a handful of threads.
- **`dev`.** The remainder: roughly 150 to 230 comments, depending on where the large posts go.

Consequential comments in the whole pool, and roughly how many the test sets could hold if they take about half while `dev` keeps the rest:

| Assumed share | Consequential in pool | Plausibly in test sets | `test-natural` alone (about 105) |
| --- | --- | --- | --- |
| 5% | 22 | about 11 | about 5 |
| 10% | 43 | about 22 | about 10 |
| 15% | 65 | about 32 | about 16 |
| 20% | 86 | about 43 | about 21 |
| 30% | 130 | about 65 | about 32 |

Below about 10%, 20 consequential test comments cannot be reached without starving `dev`.

### What recall result it could support

At 20 consequential test comments, the result is reported as a count with a Wilson 95% interval:

| Surfaced | Wilson 95% interval |
| --- | --- |
| 20 of 20 | 0.84 to 1.00 |
| 19 of 20 | 0.76 to 0.99 |
| 18 of 20 | 0.70 to 0.97 |

Three weaknesses make that interval optimistic:

1. **Clustering.** The consequential comments would come from a few threads. Misses inside one thread are not independent, so the effective sample is smaller than 20.
2. **Hindsight.** Every historical comment has already been read, and most were answered. The prospective grade is a reconstruction, made by someone who knows how the thread ended (C-010). The test measures agreement with reconstructed judgment.
3. **Same era.** `dev` and test come from the same months and the same kinds of posts. There is no test of whether the classifier holds up on comments it could not have been tuned around.

The recall result would be indicative. `EVALUATION.md` already says so when the corpus cannot supply 20.

### Cost and timing

- No waiting: measurement can follow preregistration immediately.
- About 40% to 55% of the labeled pool is unavailable for iteration.

## Option 2: historical as dev, prospective test

### Design

- **`dev`:** all 432 historical comments (and any that arrive before preregistration). All are labeled and used for iteration.
- **Test:** comments from others that arrive after preregistration (Stage 3b). To keep the test split by post, as ADR-010 intends, include only comments on **posts published after preregistration**. Because over 90% of comments arrive in a post's first week, this costs about 5% of volume.
- **Blinding:** B1 and B2 run in shadow mode as comments arrive. Their outputs are written to a git-ignored file whose hash is committed, and nothing is shown until the author has labeled that comment. Labels are made at first read, which makes the prospective grade genuinely prospective.
- **Base rates:** the test set is natural by construction. Review reduction is measured on it directly. Recall uses every consequential comment in it, so no separate enriched set is drawn; the stopping rule decides when the consequential count is sufficient.
- **Effort:** chronological review timing (C-009) on the test weeks becomes a first-read measurement rather than a re-read lower bound.

### Weeks to a usable test set

Rates come from the trailing 13 complete weeks. "Replay" restarts the actual 13-week sequence at each of its 13 weeks and reports the fewest, median, and most weeks needed. That shows the effect of spikes better than a single average. Replay counts are scaled by 0.95 for the restriction to new posts; the mean-rate and median-rate columns are not.

**100 test comments:** 5.9 weeks at the mean rate, 14.3 at the median rate; replay 3 / 7 / 11 weeks.

**20 consequential test comments**, by assumed share:

| Assumed share | Comments needed | At mean rate (17.0 per week) | At median rate (7 per week) | Replay (fewest / median / most) |
| --- | --- | --- | --- | --- |
| 5% | 400 | 23.5 weeks | 57.1 weeks | 20 / 24 / 26 |
| 10% | 200 | 11.8 weeks | 28.6 weeks | 8 / 12 / 13 |
| **15% (assumed)** | 134 | 7.9 weeks | 19.1 weeks | 4 / 10 / 12 |
| 20% | 100 | 5.9 weeks | 14.3 weeks | 3 / 7 / 11 |
| 30% | 67 | 3.9 weeks | 9.6 weeks | 2 / 4 / 10 |

**Both targets together (the accepted stopping rule):** accrual needs the larger of 100 comments and 20 divided by the consequential share.

| Assumed share | Comments needed | At mean rate (17.0 per week) | At median rate (7 per week) | Replay (fewest / median / most) | Within the 16-week cap? |
| --- | --- | --- | --- | --- | --- |
| 5% | 400 | 23.5 weeks | 57.1 weeks | 20 / 24 / 26 | No |
| 10% | 200 | 11.8 weeks | 28.6 weeks | 8 / 12 / 13 | Yes, except at the median rate |
| **15% (assumed)** | 134 | 7.9 weeks | 19.1 weeks | 4 / 10 / 12 | Yes, except at the median rate |
| 20% | 100 | 5.9 weeks | 14.3 weeks | 3 / 7 / 11 | Yes |
| 30% | 100 | 5.9 weeks | 14.3 weeks | 3 / 7 / 11 | Yes |

At 20% or more, the 100-comment target binds (about 6 to 7 weeks). Below that, the consequential target binds. At the mean rate, scaled for new posts only, 16 weeks accrue about 258 comments, so both targets fit within the cap when the share is about 8% or more.

The median-rate column is the pessimistic case. It describes a stretch of ordinary weeks with no spike, and it is what happens if the author publishes less.

### Risks

- **Volume depends on publishing.** July 2026 had 11 posts and 7 comments from others. A quiet stretch stalls the test set, so a stopping rule is needed (below).
- **Elapsed time.** Stage 3c waits on the calendar after preregistration. Nothing may be tuned during the wait, and the frozen versions stay frozen.
- **New infrastructure.** Incremental sync (Stage 1) must run regularly, and the shadow-mode run and sealed output must exist before the first test comment arrives.
- **Labeling cadence.** The author labels new comments weekly, before seeing classifier output. A missed week delays the comments but does not unblind them.
- **ADR-010 changes.** "Split by post into a development set and sealed test sets" and "test set hashes are committed before any classifier runs on them" must be rewritten for a prospective, time-sealed set. That is an ADR amendment, not an edit to make silently.

### Proposed stopping rule (preregistered with the thresholds)

Stop collecting at the first of:

1. At least 100 test comments **and** at least 20 graded consequential, or
2. A maximum duration fixed at preregistration (suggested: 16 weeks).

If the maximum is reached first, report the counts actually reached and treat recall as indicative, as `EVALUATION.md` already prescribes.

## Comparison

| | Option 1: historical only | Option 2: prospective test |
| --- | --- | --- |
| Data for iteration | About 150 to 230 comments | All 432 |
| Prospective grades | Reconstructed with hindsight | Made at first read |
| Post concentration | 1 to 3 threads dominate each set | Spread over posts published during collection |
| Base rate | `test-natural` is a few threads | Natural by construction |
| Consequential count at 15% | About 32 across test sets, dev starved below 10% | Grows with time; about 8 to 10 weeks to 20 |
| Time to result | Immediately after preregistration | About 6 to 12 weeks after preregistration in the plausible range |
| C-009 effort timing | Re-read lower bound | First-read on test weeks |
| Doc changes | Targets in `EVALUATION.md` only | `EVALUATION.md` corpus section, ADR-010 amendment, ROADMAP Stage 3c |

## Recommendation (the author decides)

Option 2. It removes the hindsight problem from the primary ground truth, keeps every historical comment available for iteration, and measures review reduction on a natural stream. Its cost is calendar time and a dependency on continued publishing, which the stopping rule bounds.

Whichever option is chosen, recompute the sizing in this proposal from the observed consequential share once the historical labels exist, and before preregistration.

## If accepted

Not done until the author decides:

- **Option 1:** revise the targets in `EVALUATION.md` to what the split can supply, record the split method and the post-concentration caveat, and check off "Select and split corpus" in `ROADMAP.md`.
- **Option 2:** amend ADR-010 (prospective, time-sealed test set; posts published after preregistration; shadow-mode output hashed and hidden until labeled). Rewrite the `EVALUATION.md` corpus table, targets, and stopping rule. Update ROADMAP Stage 0 ("select and split" becomes "freeze dev") and Stage 3c (collection period). Append the decision to `docs/FRICTION-LOG.md`.
