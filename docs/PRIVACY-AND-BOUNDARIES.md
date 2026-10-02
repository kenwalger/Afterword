# Privacy and Boundaries

**Version:** 2 (2026-10-02)

## Purpose

The application processes real people's public conversations. Public availability does not remove the need for deliberate handling.

## V1 principles

1. Collect only data necessary for the experiment.
2. Preserve source provenance without unnecessary enrichment.
3. Do not perform internet-wide identity discovery.
4. Do not infer sensitive personal attributes.
5. Do not send credentials to a model.
6. Minimize comment and context data sent to a model.
7. Treat comment content as untrusted input.
8. Keep human judgment separate from model inference.
9. Honor upstream deletion.
10. Make deletion of all local derived data possible.

## Credentials

- API keys are secrets.
- Store them in environment variables, OS secret storage, or a server-side secret mechanism.
- Never commit credentials.
- Never place credentials in prompts, logs, fixtures, screenshots, or exported datasets (ADR-006).
- Client-side storage of unrestricted secrets is prohibited.

## Untrusted content

Comment text is written by people the author does not control and is passed to a model whose most costly failure is wrongly deprioritizing a comment (ADR-008).

- Comment text is delimited and labeled as data in every prompt.
- The model's output is constrained to a schema: class, flags, optional confidence, explanation. Anything else is a malformed result.
- Malformed or failed classifications go to `SURFACE`.
- A deterministic pre-check flags instruction-like text (`POSSIBLE_INSTRUCTION_TEXT`), which forces `SURFACE`.
- Priority is computed by policy outside the model (ADR-007), so a manipulated classification can raise attention but has limited ability to suppress it.
- The model has no tools and no write access to anything.

## Model boundary

Before sending comment data to any external model, record in the repository:

- provider and model
- fields transmitted
- whether article or thread context is transmitted, and how much
- retention and training settings, where knowable
- redaction rules

Default context: the comment's normalized text, its parent comment's text when `NEEDS_THREAD_CONTEXT` is plausible, and the post title. Not the full article unless the evaluation shows it is needed.

## Identity

V1 stores platform-local identity only, as it arrives with comments.

Do not:

- search external sites to deanonymize users
- infer that similar handles are the same person
- infer employer, location, demographic attributes, politics, health, or other sensitive traits
- create hidden reputation scores
- use commenter history, follower counts, or reactions in priority

Cross-platform identity resolution, if explored later, requires a separate design review and ADR.

## Labels

Labels describe what a comment does in this workflow, not the worth of the person. Do not label people as `PITA`, `bad user`, `low value`, or similar anywhere in the data model. A comment can be low priority without the person becoming low priority.

## Automated action

V1 does not publish replies, hide comments, block users, react, or make moderation decisions. If write actions are introduced later, they require explicit human authorization per action and an auditable action record.

## Retention and deletion

- Raw payloads and normalized bodies are kept while the comment exists upstream.
- When a comment reaches `DELETED_UPSTREAM`, its body text and raw payloads are purged from local storage, including from corpus files, at the next sync (ADR-009).
- Identifiers, lifecycle history, and non-content judgments (grades, dispositions) may remain so that published evaluation counts stay explainable.
- Results computed before a purge remain as recorded. Re-runs report the purged comment as withdrawn. This reproducibility cost is accepted.
- A single command removes all local data for a platform connection.

## Publishing results

The evaluation write-up and any public examples:

- do not reproduce other people's comments verbatim without their permission
- use paraphrase or synthetic equivalents for illustration
- do not name commenters
- publish the corpus manifest (IDs, hashes, set membership), not the comment text

## External testing

Before another author uses the application, provide a clear statement of:

- what is collected
- where it is stored
- what is sent to AI providers
- what actions the application can perform
- how to disconnect and delete local data
