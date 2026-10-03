# Labeling at Scale

**Status:** Future design note. Not in V1 scope. Gated on the Stage 3 result (see `SCOPE.md`, Future candidates).

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

1. Every label records its `sample_kind`: `researcher`, `random_audit`, `targeted`, or `implicit`.
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