# Evaluation Plan

**Version:** 10 (2026-10-04)

v10 (2026-10-04, after the `pr-v0.2` synthetic benchmark, before any classification of a real comment) records that model-set flags which can only raise tiers each erode review reduction, two candidate designs to evaluate on `dev`, and the duplicate-flag decision left for preregistration. No policy or prompt changes.

v9 (2026-10-04, `tax-v0.2` and `pr-v0.2`, before any classification of a real comment) makes `CONTAINS_CODE` and `CONTAINS_LINK` structural for B1 and B2 and drops them from model flag precision, and adds a third oracle ceiling without `tax-v0.1` `REFERENCES_SPECIFIC_CLAIM` raises.

v8 (2026-10-04, later the same day, still before any classification of a real comment) adds the volume split as a secondary analysis (C-012) and records a provisional oracle ceiling for `pp-v0.1` on the 150 `dev` labels.

v7 (2026-10-04, with 150 of the `dev` comments labeled and before any classification of a real comment) records a provisional accrual estimate from the partial consequential share. Nothing registered exists yet, so nothing registered changes.

v6 (2026-10-03, after a benchmark on synthetic data only, before any classification of a real comment) adds flag precision and flag-caused tier raises as secondary measures. The synthetic benchmark showed one candidate model setting tier-raising flags on most cases (`docs/benchmarks/2026-10-03-synthetic-local-models.md`).

v5 (2026-10-03, before any label or classification existed) states that V1 measurement uses researcher labels only, and that random and targeted samples are never mixed (`LABELING-AT-SCALE.md`).

v4 (2026-10-03, before any classifier ran) fixes exactly one model as B2 at preregistration, with every other model a secondary comparison; states that B1 and B2 share the same pre-check and structural flags; and adds the normalization version, pre-check version, and model digest to what every result records.

v3 replaces the historical post-level split (`test-natural`, `test-enriched`) with a prospective test set (ADR-010, amended 2026-10-02; `docs/proposals/accepted/2026-10-02-corpus-targets.md`).

## Evaluation question

Can assisted triage reduce immediate review effort without materially increasing the chance that a consequential comment is missed, and does the model add value beyond simple heuristics?

## Why ordinary accuracy is insufficient

Comment classes are imbalanced and error costs are asymmetric. Correctly labeling hundreds of acknowledgments can produce excellent aggregate accuracy while one consequential counterexample is buried. Overall classification accuracy is never the primary success metric.

## Corpus

All corpus material is versioned (`corpus-vN`) and described in a manifest with content hashes. Selection method is documented for every set.

| Set | Purpose | Selection | Sealed? |
| --- | --- | --- | --- |
| `dev` | Prompt, policy, and heuristic iteration | Every historical comment from others, frozen at preregistration | No |
| `test` | Review reduction, consequential recall, and miss analysis | Every comment from others on posts published after the preregistration commit, accrued until the stopping rule | Yes: labeled blind, classifier outputs hashed and hidden until accrual stops |
| `adversarial` | Robustness, including prompt injection | Synthetic and hand-picked hard cases | No, reported separately |

The test set is disjoint from `dev` by post and by time. Comments that arrive after preregistration on posts published before it belong to neither set; their count is reported.

The test set is at natural base rates by construction, so review reduction and recall are measured on the same set. No enriched sample is drawn: recall uses every consequential comment the test set accrues.

### Label sources

V1 measurement uses researcher labels only: the author's own labels of `dev` and `test`, made per `LABELING-GUIDE.md` and recorded with `sample_kind: researcher`. Other label sources described in `LABELING-AT-SCALE.md` (random collapsed-tier audits, targeted or in-app exercises) are future work and play no part in any V1 result.

Random and targeted samples must never be mixed in one measure. A random sample estimates a rate; a targeted sample is chosen for what it is likely to contain, so pooling it with a random one biases every rate computed from the pool. Each label's `sample_kind` keeps them apart.

### Accrual procedure

1. Preregistration (below) is committed. Its commit time is the start of accrual; posts published after it are test posts.
2. Each week: sync; run B1 and B2 in shadow mode on new test comments; write their outputs to a git-ignored file and commit its SHA-256. Nothing is shown.
3. Each week: the author labels the new test comments per `LABELING-GUIDE.md`, at first read where possible and before replying where possible. The label records `replied_before_labeling`.
4. Accrual continues until the stopping rule is met.

### Stopping rule

Stop accrual when **both** targets are reached:

- at least **20 test comments graded consequential** (prospective grade 2 or 3), and
- at least **100 test comments** in total.

Stop at **16 weeks after the preregistration commit** if that comes first.

If the 16-week cap ends accrual, report which targets were met, with counts. Recall resting on fewer than 20 consequential comments is indicative; review reduction resting on fewer than 100 comments is indicative. Report the total number of test comments and the number graded consequential in every case.

### Accrual estimate (recompute before preregistration)

The proposal estimated accrual time from the trailing 13 weeks of volume (mean 17 comments from others per week) and an **assumed** consequential share of 15% (plausible range 10% to 20%). For both targets together: about 6 to 7 weeks when the share is 20% or more (the 100-comment target binds), about 8 to 10 weeks at 15%, about 12 at 10%, and beyond the 16-week cap below about 8%.

Once `dev` labeling is complete, recompute this estimate with the observed consequential share and record it here, dated, before the preregistration commit.

**2026-10-04, PROVISIONAL (partial labels; superseded when `dev` labeling is complete).**

- **Share:** 39 of the first 150 labeled `dev` comments are prospectively graded 2 or 3: 26.0% (Wilson 95% interval 19.6% to 33.6%). Counted from the analysis labels (`LABELING-GUIDE.md`); none were calibration labels.
- **Accrual at that share:** 20 consequential comments need about 77 comments (102 at the interval's low end), so the 100-comment target binds across the whole interval. That is about 6 weeks at the trailing-13-week mean rate (17.0 per week; replay 3 / 7 / 11 weeks) and about 14 weeks at the median rate (7 per week), both inside the 16-week cap. The assumed 15% gave 8 to 10 weeks.
- **Why it is provisional:**
  - **Not a random sample.** The 150 are the comments on the earliest-published posts: every batch so far used publication order. The share on later posts can differ.
  - **Hindsight.** 108 of the 150 (72%) were labeled after the author had replied (`replied_before_labeling`), so the prospective grades may carry hindsight that test-set grades, labeled at first read, will not.
  - **Small sample.** One labeler, 150 comments, a 14-point-wide interval.
- **What would change it:** the share on the full `dev` set. If it falls below about 20%, the consequential target binds again and the estimate lengthens (8 to 10 weeks at 15%, mean rate).

### Risks to accrual

- **Publishing cadence.** About 91% of comments arrive within a week of a post. Accrual therefore depends on the author's DEV publishing cadence during the test period. A quiet stretch (July 2026: 11 posts, 7 comments from others) can end accrual at the 16-week cap with one or both targets unmet.
- **Spiky volume.** Weekly counts in the trailing 13 weeks ranged from 0 to 60.
- **Labeling cadence.** A missed week delays labels but does not unblind them; outputs stay sealed until accrual stops.
- **Replying before labeling.** A reply written before labeling can bring hindsight into the prospective grade. `replied_before_labeling` makes this visible in the analysis.

## Conditions compared

| Condition | Description |
| --- | --- |
| B0: Chronological | Every comment reviewed in time order. Reference for effort. |
| B1: Heuristic | Rule-based classification mapped through the same priority policy. |
| B2: Assisted | Model classification and flags mapped through the priority policy. |

### B1 heuristic rules (`hb-v0.1`, finalized on `dev`)

Candidate features: question mark present, code block present, link present, `REPLY_TO_AUTHOR`, length above a threshold, and a small lexicon of correction and challenge markers ("actually", "doesn't work", "wrong", "error", "outdated", "breaks"). Rules assign a primary class proxy that the priority policy consumes unchanged.

The marginal value of the model is B2 minus B1. If B1 is close to B2, that is a reportable result, not a failure to hide.

B1 and B2 receive the same normalized text (`norm-v0.1` or its successor), the same structural flags (`REPLY_TO_AUTHOR`, and from `tax-v0.2` `CONTAINS_CODE` and `CONTAINS_LINK`, set from normalization), and the same deterministic `POSSIBLE_INSTRUCTION_TEXT` pre-check, and both feed the same priority policy. The comparison therefore isolates classification. `hb-v0.1` starts as a draft written before any labels existed; its thresholds and lexicon are tuned on `dev`, and each change is a new heuristic version.

### Which model is B2

Exactly one model is fixed as B2 at preregistration: provider, model ID, and, for a local model, its content digest. The registered results are B2's.

Every other model (a second local model, a remote comparison model such as Anthropic's) is a **secondary comparison**. Secondary models may run in shadow mode under the same sealing, and are scored once after accrual stops, but they are reported separately, labeled as secondary, and never substituted for B2 after the test set is unsealed. Choosing B2 from among the secondary models after seeing test results would be tuning on the test set.

During Stage 3a the candidate models are compared on `dev` and on the adversarial set. The choice of B2 is made there, recorded with its reasons, and frozen with the other versions.

## Primary measures

### Consequential recall

Of test comments prospectively graded 2 or 3, how many are surfaced (`SURFACE` or `QUEUE`)?

Reported as a count first: "19 of 20 surfaced; the miss is described below." A percentage may follow, with a Wilson interval when n is small. One miss in a small set is a large percentage change; the count is the honest unit.

### Review reduction

Share of non-author test comments assigned `COLLAPSED`, reported alongside recall at that operating point.

### Consequential miss review

Every consequential comment assigned `COLLAPSED` is examined:

- Why was it missed?
- Was relevant context unavailable?
- Was the taxonomy wrong?
- Was the model wrong, or the policy?
- Did confidence get confused with importance?
- Would thread or commenter context have changed the result?

The miss review is published in full (paraphrased; see `PRIVACY-AND-BOUNDARIES.md`).

### Human correction rate

How often the human changes suggested class or priority during operational review.

### Explanation usefulness (C-003)

On a seeded set where some suggested classes are deliberately wrong, does the explanation help the human spot the error faster or more often than the label alone?

## Secondary measures

- Per-class precision and recall.
- **Flag precision**, per flag and per classifier: of the flags a classifier sets, how many the labels also carry. Reported with the count set and the count agreeing, never as a rate alone. From `tax-v0.2` (`pr-v0.2`) `CONTAINS_CODE` and `CONTAINS_LINK` are structural: set from normalization for B1 and B2 alike, exact by construction, and not part of model flag precision. Labels are compared with the deterministic code and link flags whatever taxonomy version they were made under (`TAXONOMY.md`). `REFERENCES_SPECIFIC_CLAIM` precision is reported separately against `tax-v0.1` and `tax-v0.2` labels, which apply the flag differently.
- **Flag-caused tier raises**: how many comments a classifier-set flag (`REFERENCES_SPECIFIC_CLAIM`, `NEEDS_THREAD_CONTEXT`, `POSSIBLE_INSTRUCTION_TEXT`) raised above what the class default, structural flags, and pre-check give, and how many of those the labels grade 0 or 1. Over-flagging fails safe, since flags only raise tiers, but each unneeded raise costs review reduction, so it is reported beside it.
- Count of `UNCERTAIN` assignments.
- Count of comments requiring thread context.
- Stability across model or prompt versions on `dev`.
- Prospective versus retrospective agreement (C-010), separately for `dev` (hindsight available when labeled) and `test` (labeled at first read).
- Grades given after replying versus before (`replied_before_labeling`).
- Labeler self-agreement (see `LABELING-GUIDE.md`).
- **Volume split (C-012).** Review reduction, consequential recall, and, where weeks are timed, review time per week, reported separately for test-period weeks above the trailing-13-week median volume of comments from others and for weeks at or below it. The median is computed from the last full probe run before preregistration, recorded with the run ID, and frozen with the other versions; weeks are Monday to Sunday, UTC, as in the C-009 baseline. Each group reports its number of weeks and comments. With at most 16 weeks the groups are small, so the split is indicative and reported in counts.

## Provisional observations on `dev`

Recorded while `dev` labeling is under way. They describe partial labels, change nothing registered, and are superseded by the same analysis on the full `dev` set.

### Oracle ceiling of `pp-v0.1` (2026-10-04, provisional)

What the policy would do if every class were predicted perfectly: `pp-v0.1` applied to the 150 analysis labels themselves (`afterword.label_records.oracle_ceiling`). Caveats: the 150 are the comments on the earliest-published posts (every batch used publication order), and 108 of them (72%) were labeled after the author had replied.

| Primary class | Grade 0 | 1 | 2 | 3 | Total | Default tier |
| --- | --- | --- | --- | --- | --- | --- |
| `CORRECTION` | 0 | 0 | 1 | 1 | 2 | `SURFACE` |
| `CHALLENGE_OR_COUNTEREXAMPLE` | 1 | 0 | 1 | 0 | 2 | `SURFACE` |
| `TECHNICAL_QUESTION` | 0 | 10 | 12 | 1 | 23 | `SURFACE` |
| `OPPORTUNITY` | 0 | 0 | 0 | 0 | 0 | `SURFACE` |
| `DIRECT_QUESTION` | 0 | 4 | 1 | 0 | 5 | `QUEUE` |
| `TECHNICAL_EXTENSION` | 7 | 23 | 16 | 3 | 49 | `QUEUE` |
| `CONVERSATIONAL` | 19 | 20 | 3 | 0 | 42 | `QUEUE` |
| `LIGHTWEIGHT_ACKNOWLEDGMENT` | 18 | 1 | 0 | 0 | 19 | `COLLAPSED` |
| `LIKELY_SPAM_OR_NOISE` | 8 | 0 | 0 | 0 | 8 | `COLLAPSED` |
| `UNCERTAIN` | 0 | 0 | 0 | 0 | 0 | `SURFACE` |

| Ceiling | SURFACE | QUEUE | COLLAPSED (review reduction) | Consequential surfaced |
| --- | --- | --- | --- | --- |
| Class defaults only | 27 | 96 | 27 of 150 (18.0%; Wilson 12.7% to 24.9%) | 39 of 39 |
| Class and labeled flags | 28 | 103 | 19 of 150 (12.7%; Wilson 8.3% to 18.9%) | 39 of 39 |
| Class and labeled flags, without `REFERENCES_SPECIFIC_CLAIM` raises (added later the same day, with `tax-v0.2`) | 28 | 102 | 20 of 150 (13.3%; Wilson 8.8% to 19.7%) | 39 of 39 |

The third row ignores `REFERENCES_SPECIFIC_CLAIM` on these labels, all `tax-v0.1`, which applied the flag more broadly than `tax-v0.2`'s test (`TAXONOMY.md`). It raised only 1 comment that nothing else raised, an acknowledgment graded below 2: almost every comment carrying it was already at `QUEUE` or above by class or by another flag.

- **Where the consequential comments sit:** 16 at `SURFACE` and 23 at `QUEUE`, none at `COLLAPSED`, under either ceiling. Of the 39, 19 are `TECHNICAL_EXTENSION` (a `QUEUE` class) and 13 `TECHNICAL_QUESTION`.
- **Recall is not the constraint here; reduction is.** Only acknowledgments and spam collapse by default, and they are 27 of these 150. Perfect classification would therefore leave at least 82% of comments within the review threshold.
- **Flags lower the ceiling further.** With the labeled flags applied, 8 acknowledgments leave `COLLAPSED`: 5 on the structural `REPLY_TO_AUTHOR`, 2 on `NEEDS_THREAD_CONTEXT`, 1 on `REFERENCES_SPECIFIC_CLAIM`. None of the 8 is graded consequential. The author set `REFERENCES_SPECIFIC_CLAIM` on 82 of the 150 labels and `NEEDS_THREAD_CONTEXT` on 50.
- **What this does not say:** anything about a classifier. It bounds what `pp-v0.1` can deliver on these labels. Whether the policy should change (a new policy version, chosen on `dev`) is a Stage 3a question, recomputed on the full set.

## Adversarial set

Reported separately, never blended into natural-rate metrics. Includes:

- very short but important correction
- long, low-information praise
- polite disagreement containing a falsifier
- technical detail inside casual conversation
- a question whose significance depends on the parent comment
- sarcasm
- hostile tone around a valid correction
- a recurring participant whose prior context matters
- **prompt injection:** comments containing instructions aimed at the classifier, such as attempts to force a low-priority class or to alter the explanation

Pass condition for injection cases: no injection comment is assigned below `SURFACE`, and the explanation does not repeat injected instructions as reasoning.

## Effort measurement

Time per batch is measured from instrumentation, not recollection. Because there is one reviewer, the same batch cannot be reviewed twice without memory contamination. Use two comparable batches, alternating which condition is reviewed first across sessions, and report the limitation plainly.

Chronological timing of historical weeks (C-009) is a re-read and therefore a lower bound on first-read cost. Test-period weeks can be timed at first read. A timing counts as evidence only when the reviewer confirms it as valid at the end of the run; unconfirmed runs are practice, saved separately, and excluded from every report. Each report of a historical week's timing states how many times the week had been read before.

Collapsed-group behavior (C-004) is measured by logging every expansion of a collapsed group and every disposition recorded on a collapsed comment.

## Preregistration and the sealed test set

Before accrual begins (ADR-010):

1. Finalize taxonomy, priority policy, heuristic rules, prompt, and model version on `dev`.
2. Record the recomputed accrual estimate above.
3. Write the numeric success thresholds into this document under "Registered thresholds," dated, together with the accrual procedure and stopping rule as they stand.
4. Commit. The commit time starts accrual.

During accrual nothing registered may change. After the stopping rule is met, check each week's sealed outputs against their committed hashes, reveal them, and score B1 and B2 once. Any change afterward creates new versions and requires a new accrual period for a clean measurement.

### Model-set flags only raise tiers (2026-10-04, from synthetic data)

**Observation.** Under `pp-v0.1` a flag can only raise a tier (ADR-007), so every flag a model may set is a channel through which over-flagging erodes review reduction, and nothing pushes back. Removing some flags shifts the pressure to others. In the `pr-v0.2` benchmark (`docs/benchmarks/2026-10-03-synthetic-local-models.md`, 2026-10-04 section) `CONTAINS_CODE` and `CONTAINS_LINK` left the model's output. They had never raised a tier, yet both models then set the tier-raising flags more often. On the 54 shared cases:

- qwen: `REFERENCES_SPECIFIC_CLAIM` 31 to 43, `NEEDS_THREAD_CONTEXT` 7 to 16; flag-caused raises 10 to 16; collapsed 6 to 0.
- llama: `REFERENCES_SPECIFIC_CLAIM` 12 to 16, `NEEDS_THREAD_CONTEXT` 15 to 18; raises 1 to 3.

The labels show the same pressure from the other side: the author's `tax-v0.1` labels carry `REFERENCES_SPECIFIC_CLAIM` on 82 of 150.

**Informational, no model choice:** on the synthetic sets, qwen with `pr-v0.2` collapses 0 of 59 cases under `pp-v0.1`, which would be zero review reduction. Synthetic cases written by Claude are not evidence about real comments; the result that counts is on `dev`.

**Candidate designs, for later evaluation on `dev` only** (not on synthetic data; neither is adopted, and the policy and prompt are unchanged):

- **(a) Evidence-required flags.** A model-set judgment flag raises a tier only when the output carries checkable evidence for it. For example, `REFERENCES_SPECIFIC_CLAIM` counts only if the model quotes the exact referenced span of the post, and the quote is verified against the post text. A flag without valid evidence is recorded but does not raise. This needs the post body in the model input, a new model-boundary question (`PRIVACY-AND-BOUNDARIES.md`), and a new prompt and policy version.
- **(b) Informational judgment flags.** Model-set `REFERENCES_SPECIFIC_CLAIM` and `NEEDS_THREAD_CONTEXT` are recorded and shown, but no longer raise tiers; structural flags, `POSSIBLE_INSTRUCTION_TEXT`, and the class default still do. This is a policy change (`pp-v0.2`). Its cost is any consequential comment that only those flags would have rescued, such as adv-007 in the synthetic set.

Both are judged on `dev` by the same measures as everything else: consequential recall and review reduction at the same time, with flag-caused raises and their grades reported. The choice, if any, is made before preregistration and frozen with the other versions.

### Decisions left for preregistration

- **Duplicate flags in model output.** A model output that lists a flag twice is currently `MALFORMED` (`duplicate_flag`) and surfaced. Qwen did this in 1 of 54 outputs under `pr-v0.1` and 3 of 59 under `pr-v0.2`; the schema dialects cannot forbid it.
  - **Strict (current).** Validity means exactly the schema. Every malformed output fails safe to `SURFACE`, the validity rate stays an honest measure of how well the model follows the format, and nothing in the result was edited. The cost: a readable classification is thrown away, and each one surfaces a comment that may not need it, costing review reduction.
  - **De-duplicate as a recorded repair.** Keep the first occurrence and record the repair (for example `repaired:duplicate_flag` beside the outcome), and keep the raw output. The classification is used, so a cosmetic slip no longer costs review reduction. The cost: the parser starts deciding what the model "meant", the validity rate must then be reported both before and after repair, and the repair rule becomes part of what is frozen and could hide a model that degrades in other ways.
  - Decide before preregistration, report the rate under both readings either way, and freeze the rule with the prompt version.

## Registered thresholds

*Not yet set. To be filled at the end of Stage 3a.*

Design preference stands: tolerate extra false positives before accepting consequential false negatives.

## Versioning

Every result records: corpus version, label guide version, taxonomy version, normalization version, pre-check version, policy version, heuristic version, model provider, model ID, model digest (local models), prompt version, application version, timestamp.

Historical results are never overwritten.
