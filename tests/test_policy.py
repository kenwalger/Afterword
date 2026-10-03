from __future__ import annotations

import itertools
import re
from pathlib import Path

import pytest

from afterword import taxonomy
from afterword.policy import (
    CLASS_DEFAULTS,
    CONFIDENCE_FLOOR,
    POLICY_VERSION,
    PolicyInput,
    Tier,
    assign,
)

DOC = (Path(__file__).resolve().parents[1] / "docs" / "PRIORITY-POLICY.md").read_text("utf-8")


def ok(cls: str, *flags: str, confidence: str | None = None, edited: bool = False) -> PolicyInput:
    return PolicyInput("OK", cls, frozenset(flags), confidence, edited)


def test_class_defaults_match_the_document():
    table = dict(re.findall(r"^\| `([A-Z_]+)` \| `(SURFACE|QUEUE|COLLAPSED)` \|$", DOC, re.M))
    assert {k: v.name for k, v in CLASS_DEFAULTS.items()} == table
    assert POLICY_VERSION == "pp-v0.1" and f"`{POLICY_VERSION}`" in DOC


@pytest.mark.parametrize("cls", taxonomy.CLASSES)
def test_each_class_gets_its_default_and_records_it(cls):
    decision = assign(ok(cls))
    assert decision.tier == CLASS_DEFAULTS[cls]
    assert decision.rule_applied == f"class_default:{cls}"
    assert decision.rules_fired == (f"class_default:{cls}",)
    assert decision.policy_version == "pp-v0.1"


@pytest.mark.parametrize("outcome", [None, "MALFORMED", "FAILED"])
def test_missing_or_failed_classifications_surface(outcome):
    decision = assign(PolicyInput(outcome, None, frozenset(), None, False))
    assert decision.tier is Tier.SURFACE
    assert decision.rule_applied == "override:classification_failed"
    assert decision.rules_fired == ("override:classification_failed",)


def test_a_failed_classification_ignores_any_class_it_carries():
    decision = assign(
        PolicyInput("MALFORMED", "LIGHTWEIGHT_ACKNOWLEDGMENT", frozenset(), "HIGH", False)
    )
    assert decision.tier is Tier.SURFACE
    assert "class_default:LIGHTWEIGHT_ACKNOWLEDGMENT" not in decision.rules_fired


def test_instruction_text_forces_surface_over_a_collapsed_class():
    decision = assign(ok("LIGHTWEIGHT_ACKNOWLEDGMENT", "POSSIBLE_INSTRUCTION_TEXT"))
    assert decision.tier is Tier.SURFACE
    assert decision.rule_applied == "override:possible_instruction_text"


def test_instruction_text_is_recorded_even_when_the_class_already_surfaces():
    decision = assign(ok("CORRECTION", "POSSIBLE_INSTRUCTION_TEXT"))
    assert decision.tier is Tier.SURFACE
    # The first rule in table order that reaches the final tier.
    assert decision.rule_applied == "override:possible_instruction_text"
    assert decision.rules_fired == (
        "override:possible_instruction_text",
        "class_default:CORRECTION",
    )


@pytest.mark.parametrize(
    ("flag", "rule"),
    [
        ("REPLY_TO_AUTHOR", "override:reply_to_author"),
        ("NEEDS_THREAD_CONTEXT", "override:needs_thread_context"),
        ("REFERENCES_SPECIFIC_CLAIM", "override:references_specific_claim"),
    ],
)
def test_flag_overrides_raise_collapsed_to_queue(flag, rule):
    decision = assign(ok("LIGHTWEIGHT_ACKNOWLEDGMENT", flag))
    assert decision.tier is Tier.QUEUE
    assert decision.rule_applied == rule


def test_a_flag_override_does_not_claim_a_tier_the_class_already_set():
    decision = assign(ok("CORRECTION", "REPLY_TO_AUTHOR"))
    assert decision.tier is Tier.SURFACE
    assert decision.rule_applied == "class_default:CORRECTION"
    assert decision.rules_fired == ("override:reply_to_author", "class_default:CORRECTION")


def test_edited_comments_are_at_least_queued():
    decision = assign(ok("LIKELY_SPAM_OR_NOISE", edited=True))
    assert decision.tier is Tier.QUEUE
    assert decision.rule_applied == "override:edited_since_review"


def test_several_queue_overrides_record_the_first_in_table_order():
    decision = assign(
        ok(
            "LIGHTWEIGHT_ACKNOWLEDGMENT",
            "REFERENCES_SPECIFIC_CLAIM",
            "REPLY_TO_AUTHOR",
            edited=True,
        )
    )
    assert decision.rule_applied == "override:edited_since_review"
    assert decision.rules_fired == (
        "override:edited_since_review",
        "override:reply_to_author",
        "override:references_specific_claim",
        "class_default:LIGHTWEIGHT_ACKNOWLEDGMENT",
    )


def test_flags_without_policy_effect_change_nothing():
    plain = assign(ok("CONVERSATIONAL"))
    flagged = assign(ok("CONVERSATIONAL", "CONTAINS_CODE", "CONTAINS_LINK", "HOSTILE_TONE"))
    assert flagged == plain


def test_confidence_floor_is_off_in_pp_v0_1():
    assert CONFIDENCE_FLOOR is None
    decision = assign(ok("LIGHTWEIGHT_ACKNOWLEDGMENT", confidence="LOW"))
    assert decision.tier is Tier.COLLAPSED


def test_a_floor_treats_low_confidence_as_uncertain_when_set():
    low = assign(ok("LIGHTWEIGHT_ACKNOWLEDGMENT", confidence="LOW"), confidence_floor="MEDIUM")
    assert low.tier is Tier.SURFACE
    assert low.rule_applied == "override:low_confidence"
    medium = assign(
        ok("LIGHTWEIGHT_ACKNOWLEDGMENT", confidence="MEDIUM"), confidence_floor="MEDIUM"
    )
    assert medium.tier is Tier.COLLAPSED


@pytest.mark.parametrize(
    "bad",
    [
        PolicyInput("WEIRD", "CORRECTION", frozenset(), None, False),
        PolicyInput("OK", "PRAISE", frozenset(), None, False),
        PolicyInput("OK", None, frozenset(), None, False),
        PolicyInput("OK", "CORRECTION", frozenset({"IMPORTANT"}), None, False),
        PolicyInput("OK", "CORRECTION", frozenset(), "0.9", False),
    ],
)
def test_unknown_inputs_are_refused(bad):
    with pytest.raises(ValueError):
        assign(bad)


def test_overrides_never_lower_a_tier_exhaustively():
    """Every class, every subset of flags, every confidence, edited or not."""
    for cls in taxonomy.CLASSES:
        base = CLASS_DEFAULTS[cls]
        for n in range(len(taxonomy.FLAGS) + 1):
            for flags in itertools.combinations(taxonomy.FLAGS, n):
                for confidence in (None, "LOW", "MEDIUM", "HIGH"):
                    for edited in (False, True):
                        item = ok(cls, *flags, confidence=confidence, edited=edited)
                        for floor in (None, "MEDIUM", "HIGH"):
                            decision = assign(item, confidence_floor=floor)
                            assert decision.tier >= base
                            assert decision.rule_applied in decision.rules_fired
                            assert decision.rules_fired[-1] == f"class_default:{cls}"


def test_assignment_is_pure():
    item = ok("DIRECT_QUESTION", "NEEDS_THREAD_CONTEXT")
    assert assign(item) == assign(item)
