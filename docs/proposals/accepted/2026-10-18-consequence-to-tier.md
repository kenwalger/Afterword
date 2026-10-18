# Proposal: how consequence reaches the tier (three candidates compared)

**Status:** DECIDED by the author, 2026-10-18 (session 11): **accept the ceiling for V1** (the proposal's option 4). Registered thresholds will be set against the oracle under `pp-v0.2`. **(a) class-default remaps: rejected.** **(b) the extension split and (c) the model signal: deferred to V2** as candidates in `FUTURE-FEATURES.md`, with the author's note that a hand-made split risks re-encoding the consequence grade, so the open question for (b) is whether a classifier can make the split. This amends the proposal's recommendation to try (b) first. The text below is the proposal as submitted; nothing was run for candidate (c).

**The question** (`EVALUATION.md`, "Class is a weak proxy for consequence"): under `pp-v0.1`, perfect classification puts 75 of the 129 consequential `dev` comments at `QUEUE`, not `SURFACE` (SURFACE capture 54 of 129). 65 of the 75 are `TECHNICAL_EXTENSION`, a class whose labeled comments are graded 2 or 3 almost exactly half the time (65 of 131). How should consequence reach the tier without the model choosing priority (ADR-007)?

**Basis:** all 478 `dev` labels; B1 `hb-v0.2` on 478; Llama on all 478 (the last 20 classified by the author on 2026-10-18). Base policy `pp-v0.2` unless stated (`docs/proposals/accepted/2026-10-18-adopt-pp-v0.2.md`); `pp-v0.1` gives the same conclusions. **Everything below is development evidence** on the set being designed against, with labels made with hindsight. Overrides apply unchanged on top of every remap.

## Reference points

| Condition, all labels | Recall | Reduction | SURFACE | Precision | Capture |
| --- | --- | --- | --- | --- | --- |
| Oracle, `pp-v0.2` | 129 of 129 | 103 (21.5%) | 84 (17.6%) | 54 of 84 (64.3%) | 54 of 129 (41.9%) |
| B1, `pp-v0.2` | 125 of 129 | 79 (16.5%) | 199 (41.6%) | 77 of 199 (38.7%) | 77 of 129 (59.7%) |
| Llama, `pp-v0.2` | 129 of 129 | 39 (8.2%) | 216 (45.2%) | 79 of 216 (36.6%) | 79 of 129 (61.2%) |
| Grade ceiling (2 or 3 at `SURFACE`, 1 at `QUEUE`, 0 collapsed) | 129 of 129 | 158 (33.1%) | 129 (27.0%) | 129 of 129 | 129 of 129 |

The grade ceiling is not a design. It is the scale against which the candidates are read: what a tier would look like if it followed the author's grade exactly.

## (a) Class-default remaps

### Single remaps, all labels (no search)

| Remap | Oracle: SURFACE, precision, capture | B1 | Llama | Recall or reduction change |
| --- | --- | --- | --- | --- |
| None (`pp-v0.2`) | 84, 54 of 84, 54 of 129 | 199, 77 of 199, 77 of 129 | 216, 79 of 216, 79 of 129 | |
| `TECHNICAL_QUESTION` to `QUEUE` | 18, 13 of 18, 13 of 129 | 136, 50 of 136, 50 of 129 | 181, 62 of 181, 62 of 129 | none |
| `TECHNICAL_EXTENSION` to `SURFACE` | 214, 119 of 214, 119 of 129 | 220, 79 of 220, 79 of 129 | 397 (83.1%), 126 of 397, 126 of 129 | none |
| `CHALLENGE_OR_COUNTEREXAMPLE` to `QUEUE` | 73, 45 of 73, 45 of 129 | unchanged (never predicted) | 72, 23 of 72, 23 of 129 | none |
| `CONVERSATIONAL` to `COLLAPSED` | unchanged SURFACE | unchanged SURFACE | unchanged SURFACE | misses: oracle 5, B1 25, Llama 0; reduction: oracle +84, B1 +84, Llama +19 |

- **`TECHNICAL_QUESTION` to `QUEUE`** (the example in the session prompt) shrinks the oracle's `SURFACE` from 84 to 18 and its capture from 54 to 13: precision rises a little (72%), but "review first" would hold one in ten consequential comments. For both classifiers it removes consequential comments from `SURFACE` about as fast as others.
- **`TECHNICAL_EXTENSION` to `SURFACE`** gives the oracle capture of 92% at precision 55.6%, but `SURFACE` becomes 45% of all comments; for Llama, which calls many comments extensions or challenges, 83%. A `SURFACE` that large is no longer a "review first" tier.

### Searched remaps, chosen on one half and reported on the other

**Rule, fixed before the search ran:** posts shuffled with seed 20261018, then each post put in the half with fewer labeled comments so far (half A: 233 comments on 35 posts, 61 consequential, 47 in publication order; half B: 245 on 32 posts, 68 consequential, 103 in publication order). A mapping gives each class except `UNCERTAIN` (fixed at `SURFACE`) a tier, 19,683 mappings. On the selection half, keep mappings with no more consequential comments collapsed and no less reduction than the base policy, and choose the highest F1 of `SURFACE` against consequence (the harmonic mean of SURFACE precision and capture); ties go to more reduction, a smaller `SURFACE`, then fewer changes. Report on the other half. Both folds, for the oracle and for each classifier, under both base policies.

| Searched on | Fold | Chosen mapping (changes only) | Held-out half: base to remap |
| --- | --- | --- | --- |
| Oracle | A, then B | `TECHNICAL_EXTENSION` to `SURFACE` | SURFACE 46 to 124; precision 28 of 46 to 66 of 124; capture 28 of 68 to 66 of 68; recall and reduction unchanged; F1 0.491 to 0.688 |
| Oracle | B, then A | `TECHNICAL_EXTENSION` to `SURFACE`, `DIRECT_QUESTION` to `COLLAPSED` | SURFACE 38 to 90; precision 26 of 38 to 53 of 90; capture 26 of 61 to 53 of 61; **recall 61 to 60 of 61** |
| B1 | A, then B | `DIRECT_QUESTION` and `CONVERSATIONAL` to `SURFACE` | SURFACE 98 to 174 (71% of comments); F1 0.482 to 0.545 |
| B1 | B, then A | as above, plus `TECHNICAL_EXTENSION` to `COLLAPSED` | SURFACE 101 to 172 (74%); **recall 58 to 57 of 61** |
| Llama | A, then B | `OPPORTUNITY` and `CONVERSATIONAL` to `COLLAPSED`, `TECHNICAL_EXTENSION` to `SURFACE` | SURFACE 115 to 201 (82%); reduction 16 to 29; F1 0.459 to 0.483 |
| Llama | B, then A | as above, plus `DIRECT_QUESTION` to `COLLAPSED` | SURFACE 101 to 183 (79%); reduction 23 to 42; F1 0.457 to 0.500 |

Under `pp-v0.1` the oracle's fold A choice is the same; fold B chooses `CONVERSATIONAL` to `COLLAPSED` instead of `DIRECT_QUESTION`, which loses 4 of 61 consequential comments on the held-out half.

**Reading:**

- **Only one remap is stable:** `TECHNICAL_EXTENSION` to `SURFACE`, chosen in both folds at the oracle and in both folds on Llama's predictions. Everything else changes between folds, and three choices lose consequential comments on the half they were not chosen on. (With Llama on 458 comments, before the last 20 were classified, Llama's fold B did not choose it: one more sign of how unstable the classifier searches are.) That is what overfitting on 478 labels looks like.
- **A mapping chosen for one classifier breaks another.** Llama's fold-A mapping, applied to B1 on half B, lowers B1's recall from 67 to 54 of 68. The policy is shared by B1 and B2 (ADR-007), so a remap has to work for both and for the oracle.
- **Class-based mapping cannot beat the class's own consequence share.** Every comment of a class gets the same tier, so `SURFACE` precision is a weighted average of the shares of the classes put there. With `TECHNICAL_EXTENSION` at 49.6% consequential, moving it anywhere trades capture for `SURFACE` size one for one.

**Verdict on (a):** no remap improves all five measures, and the only stable one makes `SURFACE` too large to mean "first" for either real classifier. **Proposed: no class-default remap.** If one is wanted anyway, `TECHNICAL_EXTENSION` to `SURFACE` is the only candidate the evidence supports, and only paired with something that shrinks `SURFACE` elsewhere.

**Bears on:** C-001 (class decides whether to inspect, not what first), C-002 (reduction), C-008 (a shared policy must suit both conditions). **Falsified, for a given remap,** if on the test set its SURFACE F1 is no better than the base policy's, or it collapses a consequential comment the base would have kept.

## (b) Splitting `TECHNICAL_EXTENSION` into substantive and passing

Cannot be scored without new labels: the current labels say "extension", not which kind.

### Relabeling effort

- **131 labeled extensions**: 49 in publication order, 82 shuffled; 65 graded 2 or 3, 66 graded 0 or 1 (grades 0: 10, 1: 56, 2: 53, 3: 12).
- Their original labels took a median of 33.5 seconds each (mean 60.6; 132 minutes in all). A split relabel is one decision with the thread shown, so about **75 to 135 minutes**, in 4 batches of at most 40.
- It also needs: a taxonomy version (`tax-v0.3`, two classes or a class plus a flag), a guide version and a field-guide review, a prompt version for B2 (`pr-v0.3`) and a full Llama rerun (478 comments at about 44 seconds each, about 6 hours, since a new prompt is a new cache key), and a B1 rule for the split (`hb-v0.3`), because B1 and B2 share the policy.

### What the split could do (bounds, not results)

| Assumption | SURFACE | Precision | Capture | Reduction |
| --- | --- | --- | --- | --- |
| Oracle, `pp-v0.2`, no split | 84 | 54 of 84 (64.3%) | 54 of 129 (41.9%) | 103 |
| Perfect split: every consequential extension "substantive" (`SURFACE`), every other one "passing" (`QUEUE`) | 149 (31.2%) | 119 of 149 (79.9%) | 119 of 129 (92.2%) | 103 |
| The same, with passing extensions `COLLAPSED` unless an override applies | 149 | 119 of 149 | 119 of 129 | 150 (31.4%) |
| Llama's challenge call as the split: labeled extensions Llama calls a challenge go to `SURFACE` | 139 (29.1%) | 84 of 139 (60.4%) | 84 of 129 (65.1%) | 103 |

The perfect-split row assumes the split tracks the grade exactly. It will not: "substantive" has to be a judgment about what the comment does (it engages with the post's argument, reports a result, extends a method), made separately from the grade, or it is the grade under another name. How close a real split comes is exactly what the relabel measures.

### The only current evidence: Llama's challenge calls on extensions

| Labeled extensions | Llama says challenge | Llama says anything else |
| --- | --- | --- |
| First 302 labels (2026-10-08) | 28 of 49 consequential (57%) | 21 of 51 (41%) |
| All 131 labeled extensions | 30 of 55 (54.5%; 41.5 to 67.0) | 35 of 76 (46.1%; 35.3 to 57.2) |
| Publication order | 10 of 24 (41.7%) | 9 of 25 (36.0%) |
| Shuffled | 20 of 31 (64.5%) | 26 of 51 (51.0%) |
| Only the labels added since 2026-10-08 | 2 of 6 (33.3%) | 14 of 25 (56.0%) |

The observation **weakened** with more labels: the gap fell from 16 points to 9, the intervals overlap widely, and on the newest labels it reverses (small counts). As a split proxy it moves capture from 54 to 84 of 129 at the oracle while keeping precision near 60%: better than (a), well short of the perfect-split bound.

**Bears on:** C-001 (whether a finer class makes class a better proxy for consequence), C-002, C-008 (B1 would need its own split rule), C-011 (the split is a new judgment, subject to drift). **Falsified** if, after relabeling, the substantive extensions' consequential share is not clearly above the class's 49.6% (say, the interval for substantive does not exclude it), or if the author's self-agreement on the split is poor.

## (c) A model-predicted consequence signal as a raise-only tier input (design only)

### What an ADR-007 amendment would have to say

ADR-007 says the model produces class, flags, optional confidence, and explanation, and a deterministic policy maps them to a tier. An amendment admitting a consequence signal would have to state, at least:

1. **What the signal describes.** A property of what the comment does, checkable against its text, not an importance score. For example, `PUSHES_ON_POST`: the comment disputes, tests, or reports a result bearing on a specific claim or method in the post. "Important", "needs a reply", or a numeric score is excluded: that is the model-chosen priority ADR-007 removed.
2. **That it only raises,** and only to `SURFACE`, through a named policy rule (`override:model_signal` or similar) recorded in `rule_applied`. It never lowers, and its absence lowers nothing.
3. **That the policy, not the model, decides what the signal does,** and that a policy version can make it informational again (as `pp-v0.2` does for the judgment flags).
4. **Manipulation (ADR-008).** A raise-only signal cannot suppress a comment, but it can inflate `SURFACE`: comment text written to trip it ("this contradicts your benchmark") costs attention. The amendment accepts that cost explicitly and requires injection cases aimed at the signal in the adversarial set.
5. **Evidence.** The signal raises only when the output carries checkable evidence: a quoted span of the comment, verified verbatim against the comment text. (Quoting the post instead would need the post body in the model input, a new model-boundary record in `PRIVACY-AND-BOUNDARIES.md`.)
6. **No confidence.** A binary only. Llama reported `HIGH` confidence on all 478 classifications, so self-reported strength carries no information here (ADR-005 stands).
7. **The heuristic baseline.** ADR-007's consequence "the heuristic baseline and the model share the same policy, so their comparison isolates classification" no longer holds unless B1 gets an equivalent signal. The amendment must either give B1 a deterministic counterpart or state that B2 minus B1 now measures classification plus the signal (C-008).
8. **What is given up.** ADR-007 recorded that "some nuance a model could express directly about importance is deliberately given up in exchange for auditability". The amendment takes back a narrow, evidence-carrying part of that nuance, and says so.

### What would be needed to test it

- **Prompt `pr-v0.3`:** the `pr-v0.2` schema plus one boolean and one evidence field (the quoted span), with the signal defined by what the comment does and with synthetic examples on both sides. Taxonomy unchanged if it is a flag (`tax-v0.3` if it is a class split instead).
- **Synthetic first** (`afterword bench --synthetic`): new synthetic cases that should and should not set it, and injection cases that try to set it. Pass condition: no injection case sets it with valid evidence, or the raise is recorded as such.
- **Then `dev`,** by the author in their own terminal: Llama, `pr-v0.3`, `num_ctx=4096`, all 478 comments (about 6 hours; a new cache key). No new model-boundary record if the input fields do not change.
- **Scoring offline** under a candidate policy (`pp-v0.3`: `pp-v0.2` plus the signal rule), with the same five measures, split by post order and by the halves above, the signal's precision against the grades reported as a count, and the raises it causes with their grades.

**Bears on:** ADR-007, ADR-008, ADR-005; C-002, C-008 (the model would have a role B1 does not), C-001. **Falsified** if the signal's raises are no more often consequential than the condition's existing `SURFACE` (precision no better than 36.6% for Llama), if it fires on a large share of comments as the judgment flags do (about half), or if adversarial cases can trip it with valid-looking evidence.

## Comparison

| | (a) Remaps | (b) Extension split | (c) Model signal |
| --- | --- | --- | --- |
| Can be scored now | yes | no (131 relabels) | no (new prompt and run) |
| Best evidence | stable only for `TECHNICAL_EXTENSION` to `SURFACE`, which inflates `SURFACE` | upper bound high; current proxy weak and weakening | none yet; nearest analogue (judgment flags) over-fires |
| Within ADR-007 as written | yes | yes (taxonomy and policy versions) | no (needs an amendment) |
| B1 and B2 share it | must, and it breaks one or the other | needs a B1 rule | needs a B1 counterpart or a restated comparison |
| Manipulation surface | none new | none new (the class is still predicted) | new, raise-only |
| Cost | none | about 2 hours of labeling, tax, guide, prompt, rerun | prompt, synthetic cases, a 6-hour rerun, an ADR amendment |

## Proposal

1. **Reject (a)** as the answer, on the evidence above. Keep the class defaults of `pp-v0.2`.
2. **If the author wants consequence in the tier before preregistration, try (b) first:** it stays inside ADR-007, it is auditable, and its upper bound is the only one that improves precision and capture together. Its first step is cheap and decisive: relabel the 131 extensions for the split and score the oracle. If the split does not separate consequence (falsifier above), stop there.
3. **Hold (c)** unless (b) fails and the author still wants the question answered; it is the only candidate that needs an ADR amendment and adds a manipulation surface.
4. **Or accept the ceiling:** register thresholds relative to the oracle under `pp-v0.2` (SURFACE capture 41.9%) and report the shape honestly. This is a legitimate outcome under `ROADMAP.md` (reframe) and costs nothing now.

## Decision requested

Which of (a), (b), (c), or accepting the ceiling, and if (b), whether to relabel before or after the self-agreement check (`docs/proposals/accepted/2026-10-18-relabeling-scope.md`).
