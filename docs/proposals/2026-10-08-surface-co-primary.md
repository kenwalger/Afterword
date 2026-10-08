# Proposal: SURFACE size and SURFACE precision as co-primary measures (amends EVALUATION.md)

**Status:** PROPOSED (2026-10-08). Not applied. `EVALUATION.md` is unchanged until the author approves.

**Date:** 2026-10-08, before preregistration and before any model classified a real comment.

## Evidence

B1 and the oracle ceiling on the 302 `dev` analysis labels, under `pp-v0.1` (`EVALUATION.md` v12, "B1 on `dev`"; counts from `afterword evaluate`):

| | Consequential surfaced | Collapsed (review reduction) | SURFACE size | SURFACE precision (graded 2 or 3) |
| --- | --- | --- | --- | --- |
| B1, `hb-v0.1` | 81 of 84 | 44 of 302 | 126 | 50 of 126, 39.7% (Wilson 31.6% to 48.4%) |
| B1, `hb-v0.2` | 81 of 84 | 45 of 302 | 126 | 50 of 126, 39.7% |
| Oracle, labeled class only | 84 of 84 | 57 of 302 | 54 | 30 of 54, 55.6% (42.4% to 68.0%) |
| Oracle, labeled class and flags | 84 of 84 | 44 of 302 | 55 | 30 of 55, 54.5% (41.5% to 67.0%) |

By post order, B1 `hb-v0.1`: SURFACE precision 27 of 63 in publication order, 23 of 63 shuffled. `pp-v0.2` changes none of B1's figures, and none of the oracle's SURFACE figures.

**Reading.** On the two current primary measures, B1 is close to the ceiling: the same review reduction as perfect classes and flags (44 of 44) and 3 consequential comments fewer surfaced. The difference sits where neither primary measure looks: B1 puts 126 comments at `SURFACE`, against the oracle's 55, because its lexicon rule calls 83 comments `CORRECTION` (2 agree with the labels). A condition can therefore look nearly perfect while its "review first" tier is mostly noise. That is the tier a busy-week digest would deliver (`FUTURE-FEATURES.md`, spike insurance; C-012).

Two things the evidence also shows, which shape the definitions below:

- **The ceiling on SURFACE precision is well below 100% under `pp-v0.1`.** Every `TECHNICAL_QUESTION` defaults to `SURFACE`, and 22 of the 46 labeled ones are graded 1. Precision must be read against the oracle, not against 100%.
- **Precision alone rewards a small SURFACE.** B1 holds 50 consequential comments at `SURFACE`, more than the oracle's 30, because it surfaces more of everything. So SURFACE precision is reported with SURFACE size and the count of consequential comments at `SURFACE`, never alone.

## Proposed amendment to `EVALUATION.md`

Under "Primary measures", after "Review reduction", add:

> ### SURFACE size and SURFACE precision
>
> **SURFACE size:** the number of non-author test comments assigned `SURFACE`, reported as a count and as a share of all test comments.
>
> **SURFACE precision:** of the comments assigned `SURFACE`, how many are prospectively graded 2 or 3. Reported as a count first ("30 of 55"), then a percentage with a Wilson interval, always beside SURFACE size and the number of consequential comments at `SURFACE`.
>
> Both are co-primary with consequential recall and review reduction: a condition is judged on all four at once. Recall and reduction say whether the review threshold is in the right place; SURFACE size and precision say whether "review first" means anything. The oracle ceiling (`pp` applied to the labels themselves) is reported beside every condition, because the policy's class defaults bound SURFACE precision well below 100%.

And in "Registered thresholds", when they are set: a threshold for SURFACE size or precision is registered with the others, relative to the oracle on `dev` (for example, "SURFACE size no more than N times the oracle's on the test set"), or the registration states explicitly that none is set.

## What this does not change

The review threshold, the policy, recall's definition, and the stopping rule. Secondary measures stay as they are; per-class precision already exists there, but it is per class, not per tier.

## Decision requested

Approve, revise, or reject. If approved, the text above is applied to `EVALUATION.md` as a new version, and this file moves to `docs/proposals/accepted/`. C2's write-up reports SURFACE size and precision for every condition either way (the author's instruction, 2026-10-08).
