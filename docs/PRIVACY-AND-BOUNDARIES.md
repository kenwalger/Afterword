# Privacy and Boundaries

**Version:** 7 (2026-10-08)

v7 records the author's amended acceptance of the disclosure proposal: the labeler records `ai_self_disclosed` when a comment says explicitly that an AI wrote it; automated detection, even of explicit self-disclosure text, is deferred; the platform fields stay a dormant source.

v6 adds the rule that AI authorship is never inferred from writing style ("AI authorship", under Identity), with the proposal for a structural, informational disclosure flag (`docs/proposals/accepted/2026-10-08-ai-authorship-disclosed-flag.md`, not yet accepted).

v5 records path A's context size raised from 2048 to 4096 tokens, after the first real runs (nothing else on the path changes; nothing leaves the machine).

v4 records the author's sign-off of path A (local, Ollama). Path B (Anthropic) remains unsigned.

v3 adds the model-boundary records for the two classifier paths: local (Ollama) and remote (Anthropic). Neither has yet processed real comment data.

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

Because whether context is needed cannot be known before classification, the classifier sends the parent's text for every reply and none for a top-level comment.

### Model-boundary records

Drafted 2026-10-03. Real comment data may go through a path only after its record is complete, the author has signed it off (recorded below, dated), and the roadmap stage permits it (Stage 3a, after `dev` labels exist). Until then both paths run on synthetic fixtures only.

#### What the classifier input contains (both paths)

Built by the application from the store, never by the adapter. The same fields go to every provider, so the comparison is fair and the input hash is provider-independent.

| Field | Sent | Notes |
| --- | --- | --- |
| Comment text, normalized (`norm-v0.1`) | Yes | As the commenter wrote it, including any handles, names, or links that appear in the text itself. Not redacted: redaction would change meaning (a mention can be the point of a comment), and the comparison with labels needs the same text the author saw. |
| Post title | Yes | The author's own published text. |
| Parent comment text, normalized | Only for replies | Truncated to 600 characters. May be the author's own reply. |
| Whether the comment replies to the post's author | Yes, as yes or no | Structural, from the store. |
| Commenter name, handle, platform user ID, profile data | No | |
| Comment and post IDs, URLs, timestamps | No | The store keeps the mapping from request to comment. |
| The full post body | No | |
| Other comments in the thread, beyond the parent | No | |
| Labels, prior classifications, dispositions | No | |
| Any credential | No | ADR-006. |

`input_fields_sent` on each Classification records the field names actually sent.

#### Path A: local model (Ollama), primary

- **Provider and models:** Ollama on the author's machine, at `http://localhost:11434`. Candidate models, pinned by content digest: `qwen3:4b-instruct-2507-q4_K_M` and `llama3.1:8b-instruct-q4_K_M` (digests recorded in `docs/FRICTION-LOG.md` when pulled and verified by the application before each run).
- **What leaves the machine:** nothing. Requests go to the loopback interface only. The application refuses a non-loopback Ollama host unless configuration names it explicitly, and a non-loopback host is a different boundary that needs its own record.
- **Retention:** whatever the local Ollama server keeps. Ollama does not store prompts by default; its server log may record request metadata. The store keeps each response locally (`raw_output`), purged with the comment's body (ADR-009).
- **Context limit:** 4096 tokens with a 200-token output cap (2048 until 2026-10-08; raised because the guard refused 3 of the 458 `dev` comments, while the longest input is at most about 1,984 tokens at 3 characters per token). The context size is part of every cache key. An input that may not fit is not sent at all (it would otherwise be silently cut by Ollama); the classification is `FAILED` and the comment is surfaced.
- **Training:** none. Local inference does not change the model.
- **Redaction:** none beyond the field list above.
- **Model download:** pulling a model contacts the Ollama registry. No comment data is involved.
- **Author sign-off:** signed off 2026-10-03 by the author (session 5), on the grounds that nothing leaves the machine. The sign-off covers this path only: a loopback Ollama host and the pinned models above. The roadmap condition still holds: real comments go through this path no earlier than Stage 3a, after `dev` labels exist, and only when the author runs it. The application enforces the sign-off: `afterword classify --condition b2` refuses any provider whose path is not signed off.

#### Path B: remote model (Anthropic), secondary comparison

- **Provider and model:** Anthropic Messages API, `claude-haiku-4-5-20251001` (pinned by its dated ID), called directly over HTTPS with the author's own API key.
- **What is transmitted:** the fields in the table above, plus the fixed prompt (instructions and taxonomy definitions) and the output schema. Nothing else. The API key goes in a request header, never in the prompt.
- **Retention (as published by Anthropic, checked 2026-10-03):** API inputs and outputs are deleted from Anthropic's backend within 30 days of receipt or generation, unless a different agreement applies (such as zero data retention), the input is flagged for violating Anthropic's Usage Policy (then retained up to 2 years), or retention is required by law. Source: Anthropic's privacy center article "How long do you store my organization's data?" (dated 2026-07-01).
- **Training (as published, checked 2026-10-03):** by default, inputs and outputs from Anthropic's commercial products, including the API, are not used to train models, unless the customer explicitly shares them (for example, as feedback). Source: "Is my data used for model training?" (dated 2026-08-18).
- **Redaction:** none beyond the field list above.
- **Consequence:** this path sends other people's comment text to a third party, which keeps it for up to 30 days. It is a secondary comparison only (`EVALUATION.md`), and nothing in V1 depends on it.
- **Author sign-off:** not yet recorded. The provider is exercised only against mocked HTTP in tests; no request has reached Anthropic.

## Identity

V1 stores platform-local identity only, as it arrives with comments.

Do not:

- search external sites to deanonymize users
- infer that similar handles are the same person
- infer employer, location, demographic attributes, politics, health, or other sensitive traits
- create hidden reputation scores
- use commenter history, follower counts, or reactions in priority

Cross-platform identity resolution, if explored later, requires a separate design review and ADR.

### AI authorship

Whether a comment was written with AI is recorded only when someone has said so:

- **The labeler, from what the comment states.** `ai_self_disclosed` on a label is set by the labeler only when the comment says explicitly that an AI wrote it (`LABELING-GUIDE.md`, `lg-v0.6`). It is a fact about the text's own statement, not a judgment about its style.
- **A platform's disclosure field, dormant for now.** The DEV adapter maps `ai_disclosure_level` to a source-neutral value on each observed comment, but nothing stores, shows, or uses it: DEV documents disclosure for posts, and every comment so far reads `not_disclosed`.
- **Automated detection is deferred, even of explicit self-disclosure text.** No pattern, rule, heuristic, or model sets anything about AI authorship. Proposing one needs the author's agreement first.

- **Never infer AI authorship from writing style.** No model, heuristic, classifier, or labeler marks a comment as AI-written, AI-assisted, or human because of how it reads. Style-based detection is unreliable, falls hardest on non-native writers and on people who write formally, and turns a guess about a person's tools into a stored judgment about them.
- A disclosure is a fact about what the commenter stated, recorded with its source and run. Absence of a disclosure (`not_disclosed`) means nothing was said, not that the comment is human-written.
- In V1 a disclosure has no effect on priority.

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
