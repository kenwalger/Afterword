"""The taxonomy (`tax-v0.1`) as data: classes, flags, and one-line definitions.

`docs/TAXONOMY.md` is the source of truth. This module mirrors it so that the
labeling tool's help screen, the heuristic baseline, and the classifier prompt
all use the same names and order. `tests/test_taxonomy.py` checks it against the
document.
"""

from __future__ import annotations

TAXONOMY_VERSION: str = "tax-v0.1"

# Precedence order from TAXONOMY.md, then UNCERTAIN (never a tie-break).
CLASSES: tuple[str, ...] = (
    "CORRECTION",
    "CHALLENGE_OR_COUNTEREXAMPLE",
    "TECHNICAL_QUESTION",
    "OPPORTUNITY",
    "DIRECT_QUESTION",
    "TECHNICAL_EXTENSION",
    "CONVERSATIONAL",
    "LIGHTWEIGHT_ACKNOWLEDGMENT",
    "LIKELY_SPAM_OR_NOISE",
    "UNCERTAIN",
)

CLASS_DEFINITIONS: dict[str, str] = {
    "CORRECTION": "Says something in the post or the author's reply is wrong, outdated, or broken.",
    "CHALLENGE_OR_COUNTEREXAMPLE": (
        "Disputes a claim or recommendation, or gives a case where it does not hold."
    ),
    "TECHNICAL_QUESTION": "Asks something technical the author is best placed to answer.",
    "OPPORTUNITY": "Proposes collaboration, speaking, hiring, integration, or publication.",
    "DIRECT_QUESTION": "Asks the author something non-technical and expects an answer.",
    "TECHNICAL_EXTENSION": "Adds technical substance without disputing anything.",
    "CONVERSATIONAL": "Discussion with a specific point, but nothing that needs action.",
    "LIGHTWEIGHT_ACKNOWLEDGMENT": "Thanks, praise, or agreement with no further content.",
    "LIKELY_SPAM_OR_NOISE": "Off-topic promotion, generated filler, link drops, unrelated text.",
    "UNCERTAIN": "Cannot choose with reasonable confidence, or meaning needs missing context.",
}

REPLY_TO_AUTHOR: str = "REPLY_TO_AUTHOR"
POSSIBLE_INSTRUCTION_TEXT: str = "POSSIBLE_INSTRUCTION_TEXT"

# Table order from TAXONOMY.md.
FLAGS: tuple[str, ...] = (
    "NEEDS_THREAD_CONTEXT",
    REPLY_TO_AUTHOR,
    "CONTAINS_CODE",
    "CONTAINS_LINK",
    "REFERENCES_SPECIFIC_CLAIM",
    "ADDRESSED_TO_OTHER_COMMENTER",
    "HOSTILE_TONE",
    POSSIBLE_INSTRUCTION_TEXT,
)

FLAG_DEFINITIONS: dict[str, str] = {
    "NEEDS_THREAD_CONTEXT": "Meaning depends on the parent comment or thread.",
    REPLY_TO_AUTHOR: "Direct reply to a comment by the post's author. Set structurally.",
    "CONTAINS_CODE": "Includes a code block or inline code of substance.",
    "CONTAINS_LINK": "Includes one or more links.",
    "REFERENCES_SPECIFIC_CLAIM": (
        "Points at a specific sentence, step, figure, or claim in the post."
    ),
    "ADDRESSED_TO_OTHER_COMMENTER": "Primarily directed at someone other than the author.",
    "HOSTILE_TONE": "Rude or aggressive tone. Does not change the primary class.",
    POSSIBLE_INSTRUCTION_TEXT: "Reads as instructions to an automated system.",
}

# Flags that come from structure, never from a labeler's or model's judgment.
STRUCTURAL_FLAGS: frozenset[str] = frozenset({REPLY_TO_AUTHOR})


def help_text() -> str:
    """Render every class and flag with its one-line definition.

    :returns: Plain text for a terminal, classes in precedence order, then flags.
    """
    width = max(len(name) for name in (*CLASSES, *FLAGS))
    lines = ["Classes (precedence order: when two fit, take the earlier):"]
    lines += [f"  {name:<{width}}  {CLASS_DEFINITIONS[name]}" for name in CLASSES]
    lines += ["", "Flags (zero or more):"]
    lines += [f"  {name:<{width}}  {FLAG_DEFINITIONS[name]}" for name in FLAGS]
    return "\n".join(lines)
