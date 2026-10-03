# Priority Policy

**Version:** `pp-v0.1` (provisional)

Clarified 2026-10-03, before any classification existed and before the policy was implemented: the form of confidence, the confidence floor's status in `pp-v0.1`, what "edited since it was last reviewed" means before review records exist, rule names, and which rule is recorded when several apply. Tiers, defaults, and overrides are unchanged.

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

## Step 2: overrides

Overrides only raise a tier. Nothing in this policy lowers a comment below its class default.

| Condition | Effect |
| --- | --- |
| Classification missing, failed, or malformed | `SURFACE` |
| `POSSIBLE_INSTRUCTION_TEXT` flag | `SURFACE` |
| `REPLY_TO_AUTHOR` flag | at least `QUEUE` |
| `NEEDS_THREAD_CONTEXT` flag | at least `QUEUE` |
| `REFERENCES_SPECIFIC_CLAIM` flag | at least `QUEUE` |
| Model-reported confidence below the floor (not active in `pp-v0.1`; see below) | treat as `UNCERTAIN` |
| Comment edited since it was last reviewed | at least `QUEUE`, regardless of prior disposition |

Confidence is used only to raise priority, never as a measure of importance (ADR-005).

**Confidence and the floor.** Model-reported confidence is categorical: `LOW`, `MEDIUM`, or `HIGH`. Small models' self-reported numbers carry no calibration, so no numeric scale is used. In `pp-v0.1` the floor is not set and the rule never fires. Setting it during Stage 3a (for example, "`LOW` is treated as `UNCERTAIN`") is a policy change and produces `pp-v0.2`.

**Edited since it was last reviewed.** Until review records exist (Stage 4), this means the comment's lifecycle state is `EDITED`. Once they exist, it means an edit observed after the comment's most recent review event.

### Rule names and `rule_applied`

| Rule | Name recorded |
| --- | --- |
| Classification missing, failed, or malformed | `override:classification_failed` |
| `POSSIBLE_INSTRUCTION_TEXT` flag | `override:possible_instruction_text` |
| Confidence below the floor | `override:low_confidence` |
| Edited since last reviewed | `override:edited_since_review` |
| `REPLY_TO_AUTHOR` flag | `override:reply_to_author` |
| `NEEDS_THREAD_CONTEXT` flag | `override:needs_thread_context` |
| `REFERENCES_SPECIFIC_CLAIM` flag | `override:references_specific_claim` |
| Class default | `class_default:<CLASS>` |

Every rule whose condition holds is recorded in `rules_fired`, in the order of this table. `rule_applied` is the first rule in this order whose effect reaches the final tier. The class default is recorded only when no override reaches the final tier on its own. A failed classification has no class, so its only rule is `override:classification_failed`.

## Step 3: ordering within a tier

Oldest unreviewed first. V1 has no ranking score within tiers.

## Inputs deliberately excluded

These are not used in V1, to avoid reputation bias and to keep the policy explainable:

- commenter history or prior interactions (C-005, deferred)
- follower counts, reactions, or profile metadata
- comment length as a direct priority input (it may be a heuristic baseline feature; see `EVALUATION.md`)

## Author comments

Comments written by the post's author are not assigned a tier. They are context (ADR-011).

## Explanation requirement

Every tier assignment records which rule produced it: class default or the specific override. The UI shows this alongside the model's explanation, so the human can tell a policy decision from a model judgment.

## Change control

Any change to tiers, defaults, overrides, or thresholds produces a new policy version. Policy versions are fixed before the sealed test set is opened (ADR-010).
