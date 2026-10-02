# Priority Policy

**Version:** `pp-v0.1` (provisional)

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
| Model-reported confidence below `pp-v0.1` floor (set during Stage 3a) | treat as `UNCERTAIN` |
| Comment edited since it was last reviewed | at least `QUEUE`, regardless of prior disposition |

Confidence is used only to raise priority, never as a measure of importance (ADR-005).

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
