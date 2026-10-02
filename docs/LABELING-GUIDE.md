# Labeling Guide

**Version:** `lg-v0.1`

Ground truth for this experiment is produced by one person who is also the author of the posts and, often, a participant in the threads. This guide exists to make that labeling as consistent and honest as one person can make it.

## What is labeled

For each non-author comment in the corpus:

- primary class and flags, per `TAXONOMY.md`
- prospective consequentiality (required)
- retrospective consequentiality (required when known)
- a one-line reason for any consequential label
- labeling time

## Consequential: definition

A comment is **consequential** if the author would want to have seen it before the less important comments in the same batch, because it could change something: the post, the author's understanding, a commitment, a relationship, or a public record.

Working tests. Answer yes to any and the comment is likely consequential:

1. Would ignoring it for two weeks carry a real cost?
2. Does it make a claim the author should verify?
3. Does it ask something only the author can answer, where silence would read as an answer?
4. Would a careful reader of the thread expect the author to respond?
5. Could it lead to a correction, experiment, code change, or new piece of work?

### Graded scale

| Grade | Meaning |
| --- | --- |
| 0 | Not consequential |
| 1 | Nice to see, no cost if delayed |
| 2 | Consequential |
| 3 | Critical: a correction or risk that should be handled promptly |

For recall, **consequential means grade 2 or 3.**

## Prospective versus retrospective

The author already knows how most historical threads ended. That knowledge is useful but is not what a triage system can see.

- **Prospective grade:** judged from the post, the comment, and the thread *as it stood when the comment was posted*. Later replies, including the author's own, are hidden. This is the primary ground truth.
- **Retrospective grade:** judged with full knowledge of what happened afterward. Recorded for analysis of the hindsight gap (C-010).

The labeling view must render thread context as of the comment's timestamp. If that cannot be done for a comment, record `context_reconstructed: false`.

## Blinding

- Label without seeing any model output, heuristic output, or prior labels for the comment.
- Label the test sets before any classifier is run on them.
- Do not consult the commenter's profile or history.

## Self-agreement check

At least 14 days after the initial labeling pass:

1. Re-label a random sample of 25 comments from the test sets, plus every comment originally graded 2 or 3.
2. Do not look at the original labels until finished.
3. Record agreement on primary class (Cohen's kappa) and on the consequential binary (raw agreement plus a list of every disagreement).
4. Discuss each disagreement in the evaluation notes.

Original labels are not changed after this check. If agreement is poor, the corpus is relabeled as a new version under a revised guide, and the poor agreement is reported as a finding.

## Labeling sessions

- Batches of no more than 40 comments, to limit fatigue drift.
- Record start and end times per batch.
- Record any comment that was hard to label, and why, in the session notes. These are candidates for the adversarial set and for taxonomy revision.

## Label record

See `fixtures/README.md` for the JSONL schema.
