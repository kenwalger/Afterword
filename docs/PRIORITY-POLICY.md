# Priority Policy

**Version:** `pp-v0.2` (adopted 2026-10-18; provisional until frozen at preregistration)

`pp-v0.2` (2026-10-18, with all 478 `dev` labels) makes the two model-set judgment flags, `NEEDS_THREAD_CONTEXT` and `REFERENCES_SPECIFIC_CLAIM`, informational: recorded and shown, never raising a tier. Everything else is as in `pp-v0.1`. It was evaluated offline as a candidate from 2026-10-07 and adopted by the author on 2026-10-18; the evidence is in `docs/proposals/accepted/2026-10-18-adopt-pp-v0.2.md`. It is the version applied when classifying. `pp-v0.1` remains available for rescoring earlier results, and assignments made under it are kept as recorded.

`pp-v0.1` was clarified 2026-10-03, before any classification existed and before the policy was implemented: the form of confidence, the confidence floor's status, what "edited since it was last reviewed" means before review records exist, rule names, and which rule is recorded when several apply.

Priority is computed by this policy from the classification and structural signals. The model does not choose priority (ADR-007).

## Tiers

| Tier | Meaning | Within review threshold? |
| --- | --- | --- |
| `SURFACE` | Review first. | Yes |
| `QUEUE` | Review in normal order. | Yes |
| `COLLAPSED` | Grouped behind `Review all`. Never hidden or discarded (ADR-004). | No |

**Review threshold:** a comment is "surfaced" for evaluation purposes if its tier is `SURFACE` or `QUEUE`.

**Review reduction** is the share of non-author comments assigned `COLLAPSED`.

## Step 1: default tier by primary class

| Primary class | Default tier |
| --- | --- |
| `CORRECTION` | `SURFACE` |
| `CHALLENGE_OR_COUNTEREXAMPLE` | `SURFACE` |
| `TECHNICAL_QUESTION` | `SURFACE` |
| `OPPORTUNITY` | `SURFACE` |
| `UNCERTAIN` | `SURFACE` |
| `DIRECT_QUESTION` | `QUEUE` |
| `TECHNICAL_EXTENSION` | `QUEUE` |
| `CONVERSATIONAL` | `QUEUE` |
| `LIGHTWEIGHT_ACKNOWLEDGMENT` | `COLLAPSED` |
| `LIKELY_SPAM_OR_NOISE` | `COLLAPSED` |

The class defaults are unchanged from `pp-v0.1`. Class-default remaps were evaluated on `dev` on 2026-10-18 and rejected (`docs/proposals/accepted/2026-10-18-consequence-to-tier.md`).

## Step 2: overrides

Overrides only raise a tier. Nothing in this policy lowers a comment below its class default.

| Condition | Effect |
| --- | --- |
| Classification missing, failed, or malformed | `SURFACE` |
| `POSSIBLE_INSTRUCTION_TEXT` flag | `SURFACE` |
| `REPLY_TO_AUTHOR` flag | at least `QUEUE` |
| Model-reported confidence below the floor (not active; see below) | treat as `UNCERTAIN` |
| Comment edited since it was last reviewed | at least `QUEUE`, regardless of prior disposition |

**Informational flags (`pp-v0.2`).** `NEEDS_THREAD_CONTEXT` and `REFERENCES_SPECIFIC_CLAIM` are recorded on the classification and shown, but they never raise a tier, and their rules neither fire nor decide. Only a classifier sets these two flags; structure and the pre-check never do. Under `pp-v0.1` each raised a comment to at least `QUEUE`. On the 478 `dev` labels, the raises they caused were all of comments graded 0 or 1 (12 for Llama, all graded 0; 9 at the oracle), and on the synthetic sets the only cost appeared for Qwen, whose wrong classes they had rescued by accident (adv-007, adv-109, adv-110).

Confidence is used only to raise priority, never as a measure of importance (ADR-005).

**Confidence and the floor.** Model-reported confidence is categorical: `LOW`, `MEDIUM`, or `HIGH`. Small models' self-reported numbers carry no calibration, so no numeric scale is used. The floor is not set in `pp-v0.1` or `pp-v0.2`, and the rule never fires. (On `dev`, Llama reported `HIGH` for all 478 comments.) Setting it is a policy change and produces a new version.

**Edited since it was last reviewed.** Until review records exist (Stage 4), this means the comment's lifecycle state is `EDITED`. Once they exist, it means an edit observed after the comment's most recent review event.

### Rule names and `rule_applied`

| Rule | Name recorded |
| --- | --- |
| Classification missing, failed, or malformed | `override:classification_failed` |
| `POSSIBLE_INSTRUCTION_TEXT` flag | `override:possible_instruction_text` |
| Confidence below the floor | `override:low_confidence` |
| Edited since last reviewed | `override:edited_since_review` |
| `REPLY_TO_AUTHOR` flag | `override:reply_to_author` |
| `NEEDS_THREAD_CONTEXT` flag (`pp-v0.1` only) | `override:needs_thread_context` |
| `REFERENCES_SPECIFIC_CLAIM` flag (`pp-v0.1` only) | `override:references_specific_claim` |
| Class default | `class_default:<CLASS>` |

Every rule whose condition holds is recorded in `rules_fired`, in the order of this table. `rule_applied` is the first rule in this order whose effect reaches the final tier. The class default is recorded only when no override reaches the final tier on its own. A failed classification has no class, so its only rule is `override:classification_failed`. Under `pp-v0.2` the two informational flags' rules never appear in `rules_fired`.

## Step 3: ordering within a tier

Oldest unreviewed first. V1 has no ranking score within tiers.

## Inputs deliberately excluded

These are not used in V1, to avoid reputation bias and to keep the policy explainable:

- commenter history or prior interactions (C-005, deferred)
- follower counts, reactions, or profile metadata
- comment length as a direct priority input (it may be a heuristic baseline feature; see `EVALUATION.md`)
- a model-predicted consequence or importance signal (a V2 candidate in `FUTURE-FEATURES.md`; it would need an ADR-007 amendment)

## Author comments

Comments written by the post's author are not assigned a tier. They are context (ADR-011).

## Explanation requirement

Every tier assignment records which rule produced it: class default or the specific override. The UI shows this alongside the model's explanation, so the human can tell a policy decision from a model judgment.

## The ceiling this policy accepts (2026-10-18)

Class is a weak proxy for consequence: with perfect classes and flags, `pp-v0.2` surfaces all 129 consequential `dev` comments within the review threshold but puts 75 of them at `QUEUE` (SURFACE capture 54 of 129, precision 54 of 84, review reduction 103 of 478). The author accepted this ceiling for V1 on 2026-10-18: registered thresholds are set relative to the oracle under `pp-v0.2`, and how consequence could reach the tier is carried to V2 (`FUTURE-FEATURES.md`).

## Change control

Any change to tiers, defaults, overrides, or thresholds produces a new policy version. Policy versions are fixed before the sealed test set is opened (ADR-010).
