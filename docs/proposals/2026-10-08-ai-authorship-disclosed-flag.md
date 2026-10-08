# Proposal: a structural, informational `AI_AUTHORSHIP_DISCLOSED` flag

**Status:** proposed 2026-10-08 (session 8, Part C2). Not accepted, not implemented. A new flag is a taxonomy change (`tax-v0.3`) and needs the author's approval first; the rule against inferring AI authorship is adopted now in `PRIVACY-AND-BOUNDARIES.md` (v6), independently of this proposal.

## The question

DEV now returns AI-disclosure fields on every comment. Should Afterword record when a comment's author has disclosed that it was written with AI, and if so, how, without guessing?

## Evidence

### What the store holds

- Run `20261007T224849Z`: `ai_disclosure_label` and `ai_disclosure_level` on all 750 comment nodes, one pair of values only: `Not Disclosed` / `not_disclosed`, 750 of 750.
- Run `20261003T141450Z`: the same pair on 189 of 714 nodes; the rest had neither key.
- All 302 labeled comments therefore have `not_disclosed`. On this corpus the fields carry no information yet (`docs/benchmarks/2026-10-08-dev-set-evaluation.md`, section 6).

### What DEV documents (checked 2026-10-08)

- **The feature is self-disclosure on posts.** DEV's announcement, "Introducing AI Disclosure on DEV: Tools for Nuance, Clarity, and Better Feeds" (dev.to, the DEV team account), describes three levels an author picks from a dropdown when writing or editing a post: "Hand Written (No AI)", "AI-Assisted (Some AI)", and "Fully Autonomous". It describes no automatic detection and no moderator override, and mentions comments only in a reader's question, unanswered in the post.
- **The API values.** Forem's OpenAPI description (`swagger/v1/api_v1.json`) documents `ai_disclosure_level` on articles as "AI tooling usage disclosure", with the values `not_disclosed`, `no_ai`, `some_ai`, and `fully_autonomous`.
- **Comments.** Forem pull request #23895, "Emit AI disclosure fields in the v1 comments API" (opened 2026-09-27, merged 2026-10-05), says the v0 comments serializer already returned `ai_disclosure_level` and `ai_disclosure_label`, that "the API schema documents both fields", and that the v1 comment template never emitted them; the change makes v1 emit both. Afterword's adapter requests v1 (`application/vnd.forem.api-v1+json`). The merge date falls between the two runs, which fits the jump from 189 to 750 nodes; why 189 nodes had the keys before the change is not explained by the pull request.
- **Not found:** any DEV page describing how a commenter sets a comment's disclosure, or what `ai_disclosure_label` holds beyond the label for the level. `not_disclosed` means the commenter said nothing; it does not mean "human".

## Proposal

1. **A flag, `AI_AUTHORSHIP_DISCLOSED`, structural and informational.**
   - **Structural:** set by the application from source data, never by a labeler or a model, like `REPLY_TO_AUTHOR`, `CONTAINS_CODE`, and `CONTAINS_LINK`.
   - **Informational:** recorded and shown; it never raises or lowers a tier in V1. Every policy version lists it with no effect, and a test asserts that.
2. **Set only from:**
   - **Platform disclosure fields.** For DEV: `ai_disclosure_level` is `some_ai` or `fully_autonomous`. `not_disclosed`, `no_ai`, an absent field, or an unknown value set nothing. The mapping lives in the DEV adapter (ADR-001); outside it the comment carries only a neutral value such as `ai_disclosure: DISCLOSED_SOME | DISCLOSED_FULL | NOT_DISCLOSED | DISCLOSED_NONE | NOT_EXPOSED`, as a value state with provenance (the source field and run).
   - **Explicit self-disclosure rules agreed with the author.** None exist. Any rule (for example, a comment that states in so many words that it was written by an AI tool) is written down, versioned, and agreed before it is used, and is matched deterministically.
3. **Never inferred from writing style.** No classifier, heuristic, model, or labeler sets it from how a comment reads. This is a privacy rule, not a design preference (`PRIVACY-AND-BOUNDARIES.md` v6, "AI authorship").
4. **Unknown values are signals.** A disclosure value outside the known set is recorded as unexpected and logged in the friction log, as for unknown comment keys (ADR-009).

## Why informational only

- Disclosure describes the commenter's tooling. Using it for priority is close to the reputation-style inputs `PRIORITY-POLICY.md` excludes, and a disclosed AI-assisted correction is still a correction.
- On this corpus every value is `not_disclosed`, so there is nothing to tune on.
- Its first use is counting: dashboards and reports that show human and disclosed-AI comments separately (`FUTURE-FEATURES.md`, parking lot).

## Costs and open questions

- A taxonomy version (`tax-v0.3`), a `DATA-MODEL` change, an adapter change, a labeling-tool change (shown read-only), and a field-guide review.
- Undisclosed AI-written comments are invisible to the flag. That is the accepted cost of not guessing.
- Whether to record the disclosure on the post too (the author's own posts carry it); out of scope here.

## Decision needed from the author

Accept, amend, or reject. If accepted, it is implemented as `tax-v0.3` with the rules above, with no tier effect in any V1 policy.
