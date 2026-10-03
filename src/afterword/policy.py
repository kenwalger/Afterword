"""Priority policy `pp-v0.1` (`docs/PRIORITY-POLICY.md`, ADR-007).

A pure function from a classification (or its absence) and structural signals
to a tier. The model never chooses priority. Overrides only raise a tier.

Every assignment records the rule that decided it (``rule_applied``) and every
rule whose condition held (``rules_fired``), so a human can tell a policy
decision from a model judgment.

Author comments and deletion placeholders are not triage subjects (ADR-011,
ADR-009). The service layer never passes them here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from afterword import taxonomy

POLICY_VERSION: str = "pp-v0.1"


class Tier(IntEnum):
    """Review tiers. A larger value is reviewed sooner."""

    COLLAPSED = 0
    QUEUE = 1
    SURFACE = 2


OUTCOMES: frozenset[str] = frozenset({"OK", "MALFORMED", "FAILED"})
CONFIDENCE_LEVELS: tuple[str, ...] = ("LOW", "MEDIUM", "HIGH")

CLASS_DEFAULTS: dict[str, Tier] = {
    "CORRECTION": Tier.SURFACE,
    "CHALLENGE_OR_COUNTEREXAMPLE": Tier.SURFACE,
    "TECHNICAL_QUESTION": Tier.SURFACE,
    "OPPORTUNITY": Tier.SURFACE,
    "UNCERTAIN": Tier.SURFACE,
    "DIRECT_QUESTION": Tier.QUEUE,
    "TECHNICAL_EXTENSION": Tier.QUEUE,
    "CONVERSATIONAL": Tier.QUEUE,
    "LIGHTWEIGHT_ACKNOWLEDGMENT": Tier.COLLAPSED,
    "LIKELY_SPAM_OR_NOISE": Tier.COLLAPSED,
}

# The confidence floor is not set in pp-v0.1, so the low-confidence rule never
# fires. Setting it is a policy change and produces pp-v0.2.
CONFIDENCE_FLOOR: str | None = None

RULE_CLASSIFICATION_FAILED: str = "override:classification_failed"
RULE_INSTRUCTION_TEXT: str = "override:possible_instruction_text"
RULE_LOW_CONFIDENCE: str = "override:low_confidence"
RULE_EDITED: str = "override:edited_since_review"
RULE_REPLY_TO_AUTHOR: str = "override:reply_to_author"
RULE_NEEDS_CONTEXT: str = "override:needs_thread_context"
RULE_SPECIFIC_CLAIM: str = "override:references_specific_claim"

# (rule name, the tier it raises to, the flag that triggers it), in the order of
# the rule table in PRIORITY-POLICY.md, after the three non-flag overrides.
_FLAG_OVERRIDES: tuple[tuple[str, Tier, str], ...] = (
    (RULE_REPLY_TO_AUTHOR, Tier.QUEUE, taxonomy.REPLY_TO_AUTHOR),
    (RULE_NEEDS_CONTEXT, Tier.QUEUE, "NEEDS_THREAD_CONTEXT"),
    (RULE_SPECIFIC_CLAIM, Tier.QUEUE, "REFERENCES_SPECIFIC_CLAIM"),
)


@dataclass(frozen=True)
class PolicyInput:
    """Everything the policy may look at for one comment.

    ``outcome`` is ``None`` when no classification exists. ``primary_class`` and
    ``confidence`` matter only when the outcome is ``OK``. ``flags`` is the union
    of model, structural, and pre-check flags; a failed classification still
    carries its structural and pre-check flags.
    """

    outcome: str | None
    primary_class: str | None
    flags: frozenset[str]
    confidence: str | None
    edited_since_review: bool


@dataclass(frozen=True)
class PriorityDecision:
    """The policy's output for one comment."""

    tier: Tier
    rule_applied: str
    rules_fired: tuple[str, ...]
    policy_version: str = POLICY_VERSION


def _below_floor(confidence: str | None, floor: str | None) -> bool:
    if floor is None or confidence is None:
        return False
    return CONFIDENCE_LEVELS.index(confidence) < CONFIDENCE_LEVELS.index(floor)


def assign(
    item: PolicyInput, *, confidence_floor: str | None = CONFIDENCE_FLOOR
) -> PriorityDecision:
    """Compute the tier for one comment under `pp-v0.1`.

    :param item: The classification outcome, class, flags, confidence, and edit state.
    :param confidence_floor: Confidence level below which a class is treated as
        ``UNCERTAIN``. ``None`` (the `pp-v0.1` value) disables the rule. Tests
        pass a level to exercise the rule ahead of `pp-v0.2`.
    :returns: The tier, the deciding rule, and every rule that fired.
    :raises ValueError: If the outcome, class, confidence, or a flag is unknown,
        or an ``OK`` classification has no class.
    """
    if item.outcome is not None and item.outcome not in OUTCOMES:
        raise ValueError(f"unknown outcome: {item.outcome}")
    unknown = item.flags - set(taxonomy.FLAGS)
    if unknown:
        raise ValueError(f"unknown flags: {sorted(unknown)}")
    if item.confidence is not None and item.confidence not in CONFIDENCE_LEVELS:
        raise ValueError(f"unknown confidence: {item.confidence}")
    if confidence_floor is not None and confidence_floor not in CONFIDENCE_LEVELS:
        raise ValueError(f"unknown confidence floor: {confidence_floor}")

    failed = item.outcome != "OK"
    if not failed and item.primary_class not in CLASS_DEFAULTS:
        raise ValueError(f"unknown or missing class: {item.primary_class}")

    # (rule, tier it raises to), in table order. Only conditions that hold.
    fired: list[tuple[str, Tier]] = []
    if failed:
        fired.append((RULE_CLASSIFICATION_FAILED, Tier.SURFACE))
    if taxonomy.POSSIBLE_INSTRUCTION_TEXT in item.flags:
        fired.append((RULE_INSTRUCTION_TEXT, Tier.SURFACE))
    if not failed and _below_floor(item.confidence, confidence_floor):
        fired.append((RULE_LOW_CONFIDENCE, CLASS_DEFAULTS["UNCERTAIN"]))
    if item.edited_since_review:
        fired.append((RULE_EDITED, Tier.QUEUE))
    fired += [(rule, tier) for rule, tier, flag in _FLAG_OVERRIDES if flag in item.flags]

    if failed:
        tier = max(t for _, t in fired)
    else:
        assert item.primary_class is not None  # checked above
        default = f"class_default:{item.primary_class}"
        fired.append((default, CLASS_DEFAULTS[item.primary_class]))
        tier = max(t for _, t in fired)

    rule_applied = next(rule for rule, t in fired if t == tier)
    return PriorityDecision(
        tier=tier,
        rule_applied=rule_applied,
        rules_fired=tuple(rule for rule, _ in fired),
    )
