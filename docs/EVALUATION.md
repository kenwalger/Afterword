# Evaluation Plan

**Version:** 2 (2026-10-02)

## Evaluation question

Can assisted triage reduce immediate review effort without materially increasing the chance that a consequential comment is missed, and does the model add value beyond simple heuristics?

## Why ordinary accuracy is insufficient

Comment classes are imbalanced and error costs are asymmetric. Correctly labeling hundreds of acknowledgments can produce excellent aggregate accuracy while one consequential counterexample is buried. Overall classification accuracy is never the primary success metric.

## Corpus

All corpus material is versioned (`corpus-vN`) and described in a manifest with content hashes. Selection method is documented for every set.

| Set | Purpose | Selection | Sealed? |
| --- | --- | --- | --- |
| `dev` | Prompt, policy, and heuristic iteration | Random sample from posts not used in test sets | No |
| `test-natural` | Review reduction and recall at real base rates | Random sample at natural rates, disjoint posts from `dev` | Yes |
| `test-enriched` | Recall and miss analysis with enough consequential cases | Stratified sample oversampling likely-consequential comments, disjoint from all others | Yes |
| `adversarial` | Robustness, including prompt injection | Synthetic and hand-picked hard cases | No, reported separately |

Splitting by post rather than by comment prevents thread context leaking between development and test.

**Targets:** `test-natural` 100 to 150 comments. `test-enriched` sized so that it contains at least 20 comments graded consequential. If the author's corpus cannot supply that many, report the actual count and treat the recall result as indicative only.

Review reduction is only reported from `test-natural`, because oversampling distorts base rates.

## Conditions compared

| Condition | Description |
| --- | --- |
| B0: Chronological | Every comment reviewed in time order. Reference for effort. |
| B1: Heuristic | Rule-based classification mapped through the same priority policy. |
| B2: Assisted | Model classification and flags mapped through the priority policy. |

### B1 heuristic rules (`hb-v0.1`, finalized on `dev`)

Candidate features: question mark present, code block present, link present, `REPLY_TO_AUTHOR`, length above a threshold, and a small lexicon of correction and challenge markers ("actually", "doesn't work", "wrong", "error", "outdated", "breaks"). Rules assign a primary class proxy that the priority policy consumes unchanged.

The marginal value of the model is B2 minus B1. If B1 is close to B2, that is a reportable result, not a failure to hide.

## Primary measures

### Consequential recall

Of comments prospectively graded 2 or 3, how many are surfaced (`SURFACE` or `QUEUE`)?

Reported as a count first: "19 of 20 surfaced; the miss is described below." A percentage may follow, with a Wilson interval when n is small. One miss in a small set is a large percentage change; the count is the honest unit.

### Review reduction

Share of non-author comments in `test-natural` assigned `COLLAPSED`, reported alongside recall at that operating point.

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
- Count of `UNCERTAIN` assignments.
- Count of comments requiring thread context.
- Stability across model or prompt versions on `dev`.
- Prospective versus retrospective agreement (C-010).
- Labeler self-agreement (see `LABELING-GUIDE.md`).

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

Collapsed-group behavior (C-004) is measured by logging every expansion of a collapsed group and every disposition recorded on a collapsed comment.

## Preregistration and the sealed test sets

Before the test sets are opened (ADR-010):

1. Finalize taxonomy, priority policy, heuristic rules, prompt, and model version on `dev`.
2. Write the numeric success thresholds into this document under "Registered thresholds," dated.
3. Commit.

Then run B1 and B2 once on the test sets. Any change afterward creates new versions and requires a new sealed set for a clean measurement.

## Registered thresholds

*Not yet set. To be filled at the end of Stage 3a.*

Design preference stands: tolerate extra false positives before accepting consequential false negatives.

## Versioning

Every result records: corpus version, label guide version, taxonomy version, policy version, heuristic version, model and provider, prompt version, application version, timestamp.

Historical results are never overwritten.
