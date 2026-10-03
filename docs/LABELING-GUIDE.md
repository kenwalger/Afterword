# Labeling Guide

**Version:** `lg-v0.2`

`lg-v0.2` (2026-10-02, before any labels existed) defines how context is reconstructed and what `context_reconstructed` means, and records labeling time as `duration_seconds`. Grades, definitions, and tests are unchanged from `lg-v0.1`.

Ground truth for this experiment is produced by one person who is also the author of the posts and, often, a participant in the threads. This guide exists to make that labeling as consistent and honest as one person can make it.

## What is labeled

For each non-author comment in the corpus:

- primary class and flags, per `TAXONOMY.md`
- prospective consequentiality (required)
- retrospective consequentiality (required when known)
- a one-line reason for any consequential label
- labeling time (`duration_seconds`, recorded by the labeling tool)

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

### Context reconstruction (`afterword label`)

The view shows the post title and the comment's top-level thread, keeping only comments created at or before the labeled comment. Earlier replies by the author are shown; later replies, including the author's, are hidden. The retrospective prompt, which comes only after the prospective grade is saved, can reveal the full thread.

The reconstruction is partial, and the limits are known:

- **Parent edits are undetectable.** DEV comments carry no edit timestamp, so an earlier comment that was edited later is shown with its current text, not the text the commenter replied to.
- **Deleted comments without replies are gone.** If one preceded the labeled comment, the view cannot show it, and nothing indicates it existed.
- **Deleted comments with replies remain as placeholders,** shown as `[deleted comment]` with no text or author.
- **Post edits.** The post title is shown as it is now. The post body is not shown. Full probe runs from `dev-probe-0.2` on fetch every post singly, so the post's last edit time is known.

`replied_before_labeling` is also recorded by the tool: `true` when the snapshot contains the author's direct reply to the comment. For historical comments it is usually `true`, and it lets the analysis separate grades given after replying from grades given before. For the prospective test set, label before replying where possible.

`context_reconstructed` is recorded by the tool, not chosen by the labeler. It is `false` when any comment in the shown thread (an ancestor or earlier sibling) is a deletion placeholder, or when the post's last edit time is later than the comment. Otherwise it is `true`, which means "no known gap", not "verified identical". Runs from before `dev-probe-0.2` lack most posts' edit times; the tool then checks only the posts it has.

## Blinding

- Label without seeing any model output, heuristic output, or prior labels for the comment.
- Label each test comment before any classifier output for it is revealed. Shadow-mode outputs stay sealed until accrual stops (ADR-010).
- Do not consult the commenter's profile or history.

## Self-agreement check

At least 14 days after the initial labeling pass:

1. Re-label a random sample of 25 comments from the test set, plus every comment originally graded 2 or 3.
2. Do not look at the original labels until finished.
3. Record agreement on primary class (Cohen's kappa) and on the consequential binary (raw agreement plus a list of every disagreement).
4. Discuss each disagreement in the evaluation notes.

Original labels are not changed after this check. If agreement is poor, the corpus is relabeled as a new version under a revised guide, and the poor agreement is reported as a finding.

## Labeling sessions

- Batches of no more than 40 comments, to limit fatigue drift.
- Record start and end times per batch.
- The tool does both. `uv run afterword label --run <full-run-id>` labels one batch and stops; run it again to continue. It warns when the run is more than 7 days old: run a fresh full probe first, so comments deleted upstream are not labeled (ADR-009).
- Labels go to `fixtures/labels/<corpus_version>/<pass>.jsonl` and batch records (start, end, hard-to-label notes) to `batches.jsonl` in the same git-ignored directory.
- Comments are taken post by post, oldest first within a post, so no comment is labeled after a later comment from the same post has been seen.
- Commenters are shown as "Commenter A", "Commenter B" within a thread, and the author as "You (author)". Names and handles are not shown.
- At the class and flag prompts, `h` lists every class and flag with a one-line definition from `TAXONOMY.md`.
- Chronological timing for C-009: `uv run afterword label --run <full-run-id> --mode chronological --week <any date in the week>`. It shows that week's comments from others oldest first, with no labeling prompts. At the end it asks whether to record the run as a valid timing (warning first if the average is under 2 seconds per comment). Confirmed runs are written under `reports/timing/`; anything else goes to `reports/timing/practice/` and is never evidence. Time a week before labeling it (`docs/WORKFLOW.md`).
- Record any comment that was hard to label, and why, in the session notes. These are candidates for the adversarial set and for taxonomy revision.

## Label record

See `fixtures/README.md` for the JSONL schema.
