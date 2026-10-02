# ADR-011: The Author's Own Comments Are Context, Not Triage Subjects

**Status:** Accepted for V1

## Context

Threads include the post author's own replies. Classifying them inflates counts and distorts review reduction. They also carry information: a reply from the author is evidence of a `REPLIED` disposition, and a reply to the author is a signal that someone is responding directly.

## Decision

Comments by the content author are marked `is_content_author`. They are excluded from classification, priority, and evaluation metrics, retained as thread context, used to infer `REPLIED` dispositions (marked `INFERRED_FROM_SOURCE`), and used to set the `REPLY_TO_AUTHOR` flag on their children.

## Consequences

- Metrics count only comments from others.
- Inferred dispositions never overwrite human ones.
- Identity of "the author" is platform-local; if the author posts from multiple accounts, that is out of scope for V1.
