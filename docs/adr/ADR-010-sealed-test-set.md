# ADR-010: The Test Set Is Prospective and Sealed Until Measurement

**Status:** Accepted for V1, amended 2026-10-02 and 2026-10-18

The original decision split the historical corpus by post into a development set and sealed test sets. The 2026-10-02 amendment replaced that with a prospective test set, after the volume baseline showed the historical pool cannot support a development set and two post-disjoint test sets. Evidence and the options compared are in `docs/proposals/accepted/2026-10-02-corpus-targets.md`.

The 2026-10-18 amendment makes two changes, both before preregistration (`docs/friction-log/session-12.md`):

1. **The boundary is a recorded time.** The test set was defined by the preregistration commit. The tools that select it read a time recorded in a file, `registered_at` in `registry/preregistration.json`, which the preregistration commit seals. The file is written a few minutes before the commit that contains it, so the two boundaries differ by those minutes; the decision now names the recorded time, and the runbook (`docs/PREREGISTRATION.md`) keeps the rule that nothing is published between registering and committing, so in practice they coincide.
2. **Posts about Afterword are excluded from the test set.** The author publishes articles about this experiment. Comments on them are about the tool and its measurement, not the comments the experiment exists to triage, and readers who know their comments are being measured are not a natural sample. Such posts are listed in the preregistration record and excluded.

## Context

Iterating prompts, policy, or heuristics against the same data used to measure them overstates performance. With one labeler and a small corpus, the effect can be large.

The historical corpus has 432 comments from others. Three posts hold 34% of them, so any split by post is dominated by one or two threads. Every historical comment has already been read, and most were answered, so a prospective grade assigned to one now is a reconstruction made with hindsight (C-010).

Comments arrive almost entirely in the first week after a post is published (91% of the historical pool). A test set drawn from posts published after preregistration is therefore disjoint by post from the development set at little cost in volume.

A boundary that tools can apply has to be a value they can read. A commit's time is a property of the repository's history, not of the files in it, and the record that sets the boundary is itself part of the commit. A recorded time, sealed by the commit, is exact, checkable against the commit, and readable by every tool.

The author's articles about Afterword invite comments about Afterword. Labeling and scoring them would measure the tool against comments written about the tool, by readers who know the tool is watching. The first such article (Part 1, 2026-10-27) is published before preregistration and so is not a test post either way; later ones (Parts 2 and 3) would be.

## Decision

1. **Development set:** the full historical corpus of comments from others, frozen at preregistration: every comment created at or before `registered_at` on a post published at or before it.
2. **Test set:** every comment from others on a post published after `registered_at`, the preregistration time recorded in `registry/preregistration.json` and sealed by the preregistration commit, **except posts listed in that record's `excluded_posts`**. Comments that arrive after `registered_at` on earlier posts, and comments on excluded posts, belong to neither set; they are counted and reported.
3. **Exclusions:** a post about Afterword itself is excluded from the test set. It is listed in `excluded_posts` with its post ID, a reason, and the time it was recorded. Posts known at preregistration are listed then; a later one is added by a recorded amendment, committed, **before any of its comments is labeled**. An exclusion recorded after labeling is marked as such (a deviation, kept visible). Exclusions are by post, decided before the reveal, and never on the basis of any classifier output.
4. **Blind labeling:** test comments are labeled weekly by the author, at first read where possible, before any classifier output for them is revealed.
5. **Shadow mode:** B1 and B2 classify test comments as they arrive. Each week's outputs are written to a git-ignored file whose SHA-256 is committed that week. No output is shown until accrual stops.
6. **Preregistration:** thresholds, versions, the accrual procedure, the stopping rule, and the preregistration record are registered (`EVALUATION.md`, `registry/preregistration.json`) and committed before accrual begins. Nothing registered changes during accrual, except exclusions under decision 3, each recorded with its time.
7. **Stopping rule:** accrual stops when both targets are reached: at least 20 test comments graded consequential (prospective grade 2 or 3) and at least 100 test comments in total. It also stops 16 weeks after `registered_at`, if that comes first. If the 16-week cap ends accrual, the result reports which targets were met, with counts, and any result resting on an unmet target is indicative.
8. **Measurement:** after accrual stops, the sealed outputs are checked against their committed hashes, revealed, and scored once. Only labels made before the reveal are scored.

## Consequences

- Reported results reflect comments the classifier could not have been tuned on, from posts it never saw, graded without hindsight.
- Measurement waits on the calendar: up to 16 weeks after preregistration.
- Accrual depends on the author continuing to publish on DEV during the test period. A quiet stretch can end accrual at the 16-week cap with one or both targets unmet. Excluded posts do not count toward either target, so articles about Afterword do not help accrual.
- Requiring 100 test comments as well as 20 consequential ones keeps review reduction from resting on a small set when the consequential share is high.
- Incremental sync and the shadow-mode run must work before the first test comment arrives.
- Any change after measurement requires new versions and a new accrual period for a clean result.
- The development set is the entire historical pool, so no labeled data is withheld from iteration.
- Comments on earlier posts that arrive after preregistration are excluded from both sets, which keeps the test set disjoint by post at the cost of about 5% of test-period volume.
- The boundary is checkable: `registered_at` can be compared with the preregistration commit's time, and the runbook's rule (nothing published between them) can be checked against the posts' publication times.
- An exclusion recorded late leaves its post's sealed outputs in their files, whose hashes are committed; they are left out of every count and score, and the late exclusion is reported.
