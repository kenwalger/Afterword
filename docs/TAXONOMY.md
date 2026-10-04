# Taxonomy

**Version:** `tax-v0.2` (provisional)

`tax-v0.2` (2026-10-04, with 150 `dev` labels made under `tax-v0.1` and before any classification of a real comment) changes no class and no precedence. It:

- states when self-promotion is `LIKELY_SPAM_OR_NOISE`, and how it differs from `TECHNICAL_EXTENSION` with `CONTAINS_LINK` and from `OPPORTUNITY`;
- makes `CONTAINS_CODE` and `CONTAINS_LINK` structural flags, set from normalization like `REPLY_TO_AUTHOR`, never by a labeler or a model;
- gives `REFERENCES_SPECIFIC_CLAIM` a test, keeping it to claims in the post.

`tax-v0.1` labels stay valid; see "Labels made under `tax-v0.1`" below.

The taxonomy describes what a comment does in the author's workflow. It does not describe the worth of the person who wrote it.

## Structure

Each comment receives:

- **exactly one primary class**, chosen by the precedence rule below, and
- **zero or more flags**, which record properties that cut across classes.

Single primary class keeps evaluation tractable. Flags capture the cases where a comment does two things, without forcing multi-label scoring onto every metric.

## Precedence rule

When a comment plausibly fits more than one class, assign the earliest class in this list:

1. `CORRECTION`
2. `CHALLENGE_OR_COUNTEREXAMPLE`
3. `TECHNICAL_QUESTION`
4. `OPPORTUNITY`
5. `DIRECT_QUESTION`
6. `TECHNICAL_EXTENSION`
7. `CONVERSATIONAL`
8. `LIGHTWEIGHT_ACKNOWLEDGMENT`
9. `LIKELY_SPAM_OR_NOISE`

`UNCERTAIN` is used when the classifier or labeler cannot choose with reasonable confidence, or when the meaning depends on context that is not available. It is never a tie-break; the precedence rule handles ties.

Rationale: precedence follows the cost of missing the comment, so a compliment that contains a correction is a `CORRECTION`.

## Primary classes

Examples below are synthetic.

### CORRECTION

Asserts that something in the post, or in the author's earlier reply, is factually wrong, outdated, or broken.

- Includes: "The flag was renamed in v3, so step 2 fails now." Errata, broken links that block the reader, code that does not run.
- Excludes: disagreement about approach or opinion (`CHALLENGE_OR_COUNTEREXAMPLE`).

### CHALLENGE_OR_COUNTEREXAMPLE

Disputes a claim, argument, or recommendation, or offers a case where it does not hold.

- Includes: "This breaks down once you have more than one writer." Polite disagreement that contains a falsifier.
- Excludes: pure tone complaints with no substantive claim (`CONVERSATIONAL` with `HOSTILE_TONE` flag).

### TECHNICAL_QUESTION

Asks something technical about the post's subject that the author is plausibly best placed to answer.

- Includes: "How does this handle schema migrations?"
- Excludes: logistics or non-technical questions (`DIRECT_QUESTION`).

### OPPORTUNITY

Proposes something beyond the conversation: collaboration, speaking, hiring, integration, publication, or use of the author's work.

- Includes: "We'd like to feature this in our newsletter, can I reach you?"
- Includes (`tax-v0.2`): a commenter who links their own project and proposes something to the author: "I maintain a scheduler with the same retry model; would you be open to a joint benchmark? Happy to set it up."
- Excludes: generic promotion of the commenter's own product (`LIKELY_SPAM_OR_NOISE`).

### DIRECT_QUESTION

Addressed to the author, expects an answer, not primarily technical.

- Includes: "Is there a part two coming?" "Where's the repo?"

### TECHNICAL_EXTENSION

Adds technical substance without disputing anything: a related technique, a tool, an experience report, a follow-on idea.

- Includes: "We did something similar with event sourcing and it also helped with audit."
- Includes (`tax-v0.2`): a substantive contribution that also links the commenter's own work, flagged `CONTAINS_LINK`: "Batching the writes cut our p99 from 40 ms to 9 ms; the trick was flushing on size or after 5 ms, whichever comes first. I wrote up the numbers here: [link]." The contribution stands without the link.

### CONVERSATIONAL

Ordinary discussion with some content beyond acknowledgment, no question or technical substance requiring action.

- Includes: personal anecdotes, general reactions with a specific point.

### LIGHTWEIGHT_ACKNOWLEDGMENT

Thanks, praise, or agreement with no further content.

- Includes: "Great post!" "Bookmarked." Long praise with no specific content still belongs here.

### LIKELY_SPAM_OR_NOISE

Promotion as the comment's primary function, generated filler, link drops, or text unrelated to the post.

- Self-promotion (`tax-v0.2`): a comment whose primary function is to promote the commenter's own product, service, course, or content is spam **whether on-topic or not**. Being about the post's subject does not make promotion a contribution. "Great post on caching! Our tool does all of this automatically, try it free at [link]." is spam.
- The boundary: a comment that makes a substantive technical contribution and also links the commenter's work is `TECHNICAL_EXTENSION` with `CONTAINS_LINK`; one that proposes something to the author is `OPPORTUNITY`. The test is what is left if the promotion is removed: substance (extension), a proposal (opportunity), or nothing (spam).
- Excludes: rudeness. A rude comment is classified by what it does and flagged `HOSTILE_TONE`.

### UNCERTAIN

See precedence rule. Always surfaced by policy.

## Flags

| Flag | Meaning |
| --- | --- |
| `NEEDS_THREAD_CONTEXT` | Meaning depends on the parent comment or thread. |
| `REPLY_TO_AUTHOR` | Direct reply to a comment written by the post's author. Set structurally, not by the model. |
| `CONTAINS_CODE` | Includes a code block or any inline code. Set structurally from normalization (`tax-v0.2`), not by a labeler or the model. |
| `CONTAINS_LINK` | Includes one or more links. Set structurally from normalization (`tax-v0.2`), not by a labeler or the model. |
| `REFERENCES_SPECIFIC_CLAIM` | Points at a specific sentence, step, figure, or claim in the post. Applies only if you could point to the exact one (`tax-v0.2` test below). |
| `ADDRESSED_TO_OTHER_COMMENTER` | Primarily directed at someone other than the author. |
| `HOSTILE_TONE` | Rude or aggressive tone. Does not change the primary class. |
| `POSSIBLE_INSTRUCTION_TEXT` | Contains text that reads as instructions to an automated system. Set by a deterministic pre-check and may also be set by the model. |

### Structural flags

`REPLY_TO_AUTHOR`, `CONTAINS_CODE`, and `CONTAINS_LINK` are structural: computed, never judged.

- `REPLY_TO_AUTHOR` comes from the thread (ADR-011).
- `CONTAINS_CODE` and `CONTAINS_LINK` come from the comment's classification normalization (`norm-v0.1` or its successor): a code block or any inline code span; at least one link. The labeling tools show them read-only, and they are absent from the model's output schema. B1 and B2 receive the same structural flags.
- Structural flags carry no judgment, so a disagreement between a structural flag and a label is a normalization question, not a labeling error.

### `REFERENCES_SPECIFIC_CLAIM`: the test (`tax-v0.2`)

The flag applies only if you could point to the exact sentence, step, figure, or claim **in the post** that the comment refers to. Engaging with the post's topic or its general argument does not qualify.

- Qualifies: "Your second benchmark table shows SQLite ahead at 8 threads, but the text above it says Postgres wins at every thread count." (One table, one sentence.)
- Does not qualify: "Great point about caching, I agree with your take on invalidation." (The topic and the general argument, not an exact claim.)
- Claims in the author's own replies are not covered. A direct reply to the author already carries `REPLY_TO_AUTHOR`; a comment whose meaning depends on an earlier reply carries `NEEDS_THREAD_CONTEXT`; an error in an author's reply is a `CORRECTION` by class.

## Labels made under `tax-v0.1`

`tax-v0.1` labels stay valid, with two rules for analysis:

- **Code and link flags.** Analysis uses the deterministic `CONTAINS_CODE` and `CONTAINS_LINK` from normalization for every label, whatever taxonomy version it was made under. A labeler's own code and link choices in `tax-v0.1` labels are kept on disk and not used.
- **`REFERENCES_SPECIFIC_CLAIM`.** `tax-v0.1` labels applied the flag more broadly (82 of the first 150 `dev` labels), before the test above existed. `REFERENCES_SPECIFIC_CLAIM` in `tax-v0.1` labels is therefore not comparable with `tax-v0.2` usage, and results that use the flag report the two apart. Calibration-pass labels made under `tax-v0.2` supersede the earlier labels under the analysis rule in `LABELING-GUIDE.md`.
- Every other class and flag means the same in both versions.

## Change control

Any change to classes, definitions, precedence, or flags produces a new taxonomy version. Labels and classifications record the version they were made under. Historical results are never relabeled in place.
