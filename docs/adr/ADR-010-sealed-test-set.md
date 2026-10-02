# ADR-010: The Test Set Is Prospective and Sealed Until Measurement

**Status:** Accepted for V1, amended 2026-10-02

The original decision split the historical corpus by post into a development set and sealed test sets. The amendment replaces that with a prospective test set, after the volume baseline showed the historical pool cannot support a development set and two post-disjoint test sets. Evidence and the options compared are in `docs/proposals/accepted/2026-10-02-corpus-targets.md`.

## Context

Iterating prompts, policy, or heuristics against the same data used to measure them overstates performance. With one labeler and a small corpus, the effect can be large.

The historical corpus has 432 comments from others. Three posts hold 34% of them, so any split by post is dominated by one or two threads. Every historical comment has already been read, and most were answered, so a prospective grade assigned to one now is a reconstruction made with hindsight (C-010).

Comments arrive almost entirely in the first week after a post is published (91% of the historical pool). A test set drawn from posts published after preregistration is therefore disjoint by post from the development set at little cost in volume.

## Decision

1. **Development set:** the full historical corpus of comments from others, frozen at preregistration. All iteration happens on it.
2. **Test set:** every comment from others on a post published after the preregistration commit. Comments that arrive after preregistration on earlier posts belong to neither set; they are counted and reported.
3. **Blind labeling:** test comments are labeled weekly by the author, at first read where possible, before any classifier output for them is revealed.
4. **Shadow mode:** B1 and B2 classify test comments as they arrive. Each week's outputs are written to a git-ignored file whose SHA-256 is committed that week. No output is shown until accrual stops.
5. **Preregistration:** thresholds, versions, the accrual procedure, and the stopping rule are registered in `EVALUATION.md` and committed before accrual begins. Nothing registered changes during accrual.
6. **Stopping rule:** accrual stops when both targets are reached: at least 20 test comments graded consequential (prospective grade 2 or 3) and at least 100 test comments in total. It also stops 16 weeks after the preregistration commit, if that comes first. If the 16-week cap ends accrual, the result reports which targets were met, with counts, and any result resting on an unmet target is indicative.
7. **Measurement:** after accrual stops, the sealed outputs are checked against their committed hashes, revealed, and scored once.

## Consequences

- Reported results reflect comments the classifier could not have been tuned on, from posts it never saw, graded without hindsight.
- Measurement waits on the calendar: up to 16 weeks after preregistration.
- Accrual depends on the author continuing to publish on DEV during the test period. A quiet stretch can end accrual at the 16-week cap with one or both targets unmet.
- Requiring 100 test comments as well as 20 consequential ones keeps review reduction from resting on a small set when the consequential share is high.
- Incremental sync and the shadow-mode run must work before the first test comment arrives.
- Any change after measurement requires new versions and a new accrual period for a clean result.
- The development set is the entire historical pool, so no labeled data is withheld from iteration.
- Comments on earlier posts that arrive after preregistration are excluded from both sets, which keeps the test set disjoint by post at the cost of about 5% of test-period volume.
