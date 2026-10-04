# Labeling at Scale

**Status:** Future design note. Not in V1 scope. Gated on the Stage 3 result (see `SCOPE.md`, Future candidates).

Revised 2026-10-04: adds labeler onboarding through a calibration exercise.

## The problem

V1 ground truth comes from one researcher labeling every comment in a historical corpus of a few hundred. That is tedious but feasible. It does not scale:

| Volume | Exhaustive labeling at 20 to 30 seconds per comment |
| --- | --- |
| ~450 comments (the V1 corpus) | 3 to 5 hours |
| ~4,500 comments (an active writer) | 25 to 35 hours |
| ~45,000 comments (an organization) | Not realistic |

## Principle

**Labeling is a research activity. Product users are never required to label.**

V1 labeling exists so the system can be validated once, by the researcher, against careful ground truth. A user at any volume uses the policy and classifier as they are. The question a user needs answered is narrower: "Is it missing things that matter to me?" That question can be answered with small samples rather than exhaustive labels.

## Label sources

| Source | What it is | Strengths | Weaknesses |
| --- | --- | --- | --- |
| **Researcher labels** | Exhaustive labels per `LABELING-GUIDE.md` (V1) | Careful, blinded, versioned | Does not scale |
| **Implicit signals** | Overrides, dispositions, replies recorded during normal review | Free, continuous | Biased toward what the user already looked at; silence is ambiguous |
| **Explicit in-app exercises** | Small, occasional labeling prompts during normal use | Scales with use; can be randomized | Adds user effort; must stay small and optional |

Implicit signals are never treated as ground truth for measurement. A comment the user never opened produces no signal, which is exactly the case recall measurement cares about.

## Random versus targeted samples

The two kinds of sample answer different questions. They must never be mixed.

### Random samples measure

Drawn uniformly at random from a defined population, so results generalize to that population.

- **Collapsed-tier audit.** Periodically show the user a few randomly selected collapsed comments and ask whether any should have been surfaced. This yields an unbiased running estimate of the miss rate, at any volume, from a few seconds of effort per week. It also directly addresses C-004: it guarantees the collapsed group is actually inspected, in small doses.
- **Surfaced-tier audit (optional).** A random sample of surfaced comments estimates how often attention is spent on things that did not need it.

Requirements:

- The sampling rate is fixed in advance and recorded.
- Estimates are reported as counts with intervals, per `EVALUATION.md` small-sample rules.
- The user answers before seeing the system's class, tier, or explanation, so the audit is blind.

### Targeted samples improve

Deliberately chosen where labels are most informative.

- Comments the model marked low confidence or `UNCERTAIN`.
- Disagreements between the heuristic baseline and the model.
- Edited comments, new kinds of posts, or classes with few labels.

Targeted samples are efficient for improving the system and biased by construction. They are never used to estimate miss rates or any other headline metric.

### Separation rules

1. Every label records its `sample_kind`: `researcher`, `random_audit`, `targeted`, `implicit`, or `calibration_exercise` (see Labeler onboarding).
2. Metrics are computed only from `researcher` or `random_audit` labels.
3. A label used to make an improvement is never also used to measure that improvement. Random audits measure; targeted labels improve.

## In-app labeling exercises

A lightweight "labeling exercise" surfaced during normal use, for example "Five quick ones: would you have wanted to see these?"

Design constraints:

- **Opt-in, small, skippable.** A handful of comments at a time, with a frequency cap. Never blocks review.
- **Blind first, reveal after.** The first question is binary and asked before showing the system's judgment: "Would you have wanted to see this?" The class, tier, and explanation are revealed only after the answer, followed by optional detail (class, reason).
- **Same context rules as V1.** Thread context as of the comment's timestamp, later replies hidden where practical.
- **Visible value.** The user can see what their answers changed, such as a revised miss-rate estimate or an adjusted setting.

### How exercises improve the system

Afterword does not fine-tune models, and nothing learns silently. Improvement happens through explicit, versioned changes:

- choosing better few-shot examples for the prompt
- calibrating per-user settings such as a confidence floor (a new policy version)
- identifying taxonomy gaps that need a revision

Each change produces a new version (`TAXONOMY.md`, `PRIORITY-POLICY.md`, prompt), is visible to the user, and is measured afterward with random audits, never with the labels that motivated it. Human authority over what matters (ADR-003) is preserved: exercises inform the system; they do not hand the decision to it.

## Judgment drift

What an author considers consequential changes over time. Labels are therefore **dated judgments, not permanent truths**.

Three distinct effects:

| Effect | Cause | Example |
| --- | --- | --- |
| **Hindsight** | Knowing how a thread turned out | A question that later led to a correction feels more important in retrospect (C-010) |
| **Perspective drift** | The author's knowledge, community standing, or values change | A kind of comment that once seemed minor now matters, or the reverse |
| **Context change** | The author's projects or priorities change | Comments about a retired project stop being consequential |

Implications:

- **Never overwrite.** A re-label is a new label record with its own date. The history of the author's judgment is itself data.
- **Recency for improvement.** When labels inform prompt examples or calibration, recent judgments count more than old ones.
- **Periodic re-audit.** Old labels are occasionally re-judged, which measures drift and keeps calibration current.
- **Measurement windows.** Any reported metric states the period its labels were made in.

Drift is distinct from inconsistency. The 14-day self-agreement check in `LABELING-GUIDE.md` measures short-term consistency. Drift is the long-term change that remains after consistency is accounted for. See C-011 in `CLAIMS.md`.

## Labeler onboarding: the calibration exercise

Anyone who labels for Afterword, including the author of a new account, goes through a short calibration exercise before labeling real comments, so that the learning curve happens on practice material instead of in the ground truth.

### Why

Definitions alone are not enough. The V1 author's first 150 labels showed the learning curve clearly: `REFERENCES_SPECIFIC_CLAIM` was applied to 82 of 150 comments, in the broad sense of "engages with the post" rather than the defined sense of "points to an exact sentence, step, figure, or claim." Labeling one's own comments adds a second difficulty: the labeler already knows how most threads turned out. Every new labeler would face both.

### What it is

- About 20 synthetic comments, each with a **reference label** (primary class, flags, prospective grade) and a **one-paragraph rationale** explaining the decision.
- The comments concentrate on the boundaries that change a tier or are known to be hard:
  - acknowledgment versus conversational (`COLLAPSED` versus `QUEUE`)
  - self-promotion as spam versus a technical contribution with a link, versus an opportunity
  - the `REFERENCES_SPECIFIC_CLAIM` test: an exact referent in the post, or only the topic
  - `NEEDS_THREAD_CONTEXT`: meaning that depends on the thread, versus a reply that stands alone
  - correction versus challenge, and a correction hidden inside praise (precedence)
  - when `UNCERTAIN` is the honest answer
  - prospective grading without hindsight
- Synthetic only. No real comment, commenter, or thread appears in it.

### How it works

1. The labeler labels each exercise comment in the normal labeling interface, without seeing the reference label.
2. After each comment, the reference label and rationale are revealed, with the labeler's answer beside them.
3. At the end, agreement is summarized **per boundary**, not as a single score, so the labeler sees which distinctions need attention.
4. The exercise can be repeated. A second attempt uses a different ordering, and, where the set allows, different comments for the same boundaries.

It is a teaching tool, not a gate. Nobody is blocked from labeling by a score, and exercise results are never used as evidence about the system.

### Rules

- **Separate from evaluation material.** The calibration set is its own versioned file, not the adversarial or benchmark sets, so that showing its reference labels to labelers never touches model evaluation.
- **Reference labels are approved by the researcher.** Drafted reference labels (for example, written by a coding assistant) are proposals until the researcher reviews and approves each one.
- **Versioned with the taxonomy.** Each calibration set records the taxonomy and labeling-guide versions it teaches. A taxonomy change that alters a boundary produces a new calibration set version.
- **Recorded, but kept apart.** Exercise answers are stored with `sample_kind: calibration_exercise` and excluded from every measure, alongside the separation rules above.
- **Worked examples in the guide.** The hardest boundaries also appear as worked examples in `LABELING-GUIDE.md`, so the reasoning is available while labeling, not only during the exercise.

### Possible early use

A minimal version (the set, plus reveal-after-answer in the label UI) could also serve the V1 author before the calibration pass, as a refresher on the tax-v0.2 boundaries. That is optional and does not change V1 measurement.

## Organizations

Additional considerations for team or organizational use:

- **Distributed labeling.** Audits and exercises spread across team members, with inter-rater agreement measured on overlapping samples.
- **Consequential for whom.** A comment consequential to a docs writer may not be to a product manager. Per-role or per-person judgments may be needed rather than one organizational truth.
- **Pooling.** Labels from different people are not pooled into one model of importance without an explicit decision about whose judgment it represents.

## Privacy

- Labels describe comments, not commenters (`PRIVACY-AND-BOUNDARIES.md`).
- Labels are stored locally in the local-first deployment (ADR-013).
- In any hosted mode, labels are derived data about other people's comments and fall under the same data-processing obligations. Labels are never pooled across users without consent.

## Relationship to V1

V1 measurement uses researcher labels only, per `EVALUATION.md`. Nothing here changes the V1 experiment. The V1 label schema may record `sample_kind: researcher` so that later label sources fit without migration.

## Open questions

- What audit sampling rate gives a useful miss-rate estimate at different volumes without becoming a chore?
- How should drift-weighted calibration avoid amplifying a passing mood into a lasting setting?
- Can the binary "would you have wanted to see this?" answer stand in for the full V1 grade for measurement purposes? That is itself testable against V1 labels.