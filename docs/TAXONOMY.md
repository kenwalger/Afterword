# Taxonomy

**Version:** `tax-v0.1` (provisional)

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
- Excludes: generic promotion of the commenter's own product (`LIKELY_SPAM_OR_NOISE`).

### DIRECT_QUESTION

Addressed to the author, expects an answer, not primarily technical.

- Includes: "Is there a part two coming?" "Where's the repo?"

### TECHNICAL_EXTENSION

Adds technical substance without disputing anything: a related technique, a tool, an experience report, a follow-on idea.

- Includes: "We did something similar with event sourcing and it also helped with audit."

### CONVERSATIONAL

Ordinary discussion with some content beyond acknowledgment, no question or technical substance requiring action.

- Includes: personal anecdotes, general reactions with a specific point.

### LIGHTWEIGHT_ACKNOWLEDGMENT

Thanks, praise, or agreement with no further content.

- Includes: "Great post!" "Bookmarked." Long praise with no specific content still belongs here.

### LIKELY_SPAM_OR_NOISE

Off-topic promotion, generated filler, link drops, or text unrelated to the post.

- Excludes: rudeness. A rude comment is classified by what it does and flagged `HOSTILE_TONE`.

### UNCERTAIN

See precedence rule. Always surfaced by policy.

## Flags

| Flag | Meaning |
| --- | --- |
| `NEEDS_THREAD_CONTEXT` | Meaning depends on the parent comment or thread. |
| `REPLY_TO_AUTHOR` | Direct reply to a comment written by the post's author. Set structurally, not by the model. |
| `CONTAINS_CODE` | Includes a code block or inline code of substance. |
| `CONTAINS_LINK` | Includes one or more links. |
| `REFERENCES_SPECIFIC_CLAIM` | Points at a specific sentence, step, figure, or claim in the post. |
| `ADDRESSED_TO_OTHER_COMMENTER` | Primarily directed at someone other than the author. |
| `HOSTILE_TONE` | Rude or aggressive tone. Does not change the primary class. |
| `POSSIBLE_INSTRUCTION_TEXT` | Contains text that reads as instructions to an automated system. Set by a deterministic pre-check and may also be set by the model. |

## Change control

Any change to classes, definitions, precedence, or flags produces a new taxonomy version. Labels and classifications record the version they were made under. Historical results are never relabeled in place.
