"""Deterministic pre-check for instruction-like text (`pc-v0.1`, ADR-008).

Runs on the normalized text, which is exactly what a classifier sees. Any match
sets ``POSSIBLE_INSTRUCTION_TEXT``, and the priority policy then forces
``SURFACE``. The check runs for every classifier (B1, B2, and secondary
models), so the comparison between them isolates classification.

False positives are accepted (ADR-008): a benign comment that quotes a prompt,
or names a taxonomy class in capitals, is surfaced unnecessarily. Patterns are
kept narrow enough that ordinary technical prose ("the server will respond with
a 404", "ignore the warning in step 2") does not match.

Any change to the patterns is a new pre-check version.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from afterword import taxonomy

PRECHECK_VERSION: str = "pc-v0.1"

_I: re.RegexFlag = re.IGNORECASE
_TARGET: str = r"(?:instructions?|prompts?|rules|directions|guidelines|context|messages?)"
_PREVIOUS: str = r"(?:previous|prior|above|earlier|preceding|system|original|all|your|any|the)"

RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ignore_instructions",
        re.compile(
            rf"\b(?:ignore|disregard|forget|override|bypass|skip)\s+(?:(?:all|any|the|your|of)\s+)*"
            rf"(?:{_PREVIOUS}\s+)?{_TARGET}\b",
            _I,
        ),
    ),
    ("new_instructions", re.compile(r"\bnew\s+(?:system\s+)?instructions?\b", _I)),
    ("system_prompt", re.compile(r"\b(?:system|developer|hidden)\s+(?:prompt|message)\b", _I)),
    (
        "role_marker",
        re.compile(
            r"<\s*/?\s*(?:system|assistant|user|instructions?|im_start|im_end)\s*>"
            r"|<\|[a-z_]+\|>"
            r"|\[/?(?:INST|SYS|SYSTEM)\]"
            r"|^\s*#{1,6}\s*(?:system|instructions?|assistant)\b"
            r"|^\s*(?:system|assistant)\s*:",
            _I | re.MULTILINE,
        ),
    ),
    (
        "addressed_to_model",
        re.compile(
            r"\b(?:you\s+are\s+now|dear|note\s+to(?:\s+the)?)\s+(?:an?\s+|the\s+)?"
            r"(?:ai|assistant|classifier|language\s+model|llm|bot)\b"
            r"|\b(?:to|for)\s+(?:the|any)\s+(?:classifier|triage\s+(?:system|tool|model)|"
            r"automated\s+(?:system|tool|reviewer)|comment\s+(?:classifier|triage))\b",
            _I,
        ),
    ),
    (
        "classify_as",
        re.compile(
            r"\b(?:classify|categori[sz]e|label|tag|mark|rate|treat|consider)\s+"
            r"(?:this|the|my)\s+(?:comment|message|text|reply)\s+as\b",
            _I,
        ),
    ),
    (
        "priority_command",
        re.compile(
            r"\b(?:set|change|lower|reduce|assign)\s+(?:the\s+)?(?:priority|tier)\s+"
            r"(?:of\s+|for\s+)?(?:this|my)\s+(?:comment|message|reply)\b"
            r"|\b(?:this|my)\s+(?:comment|message|reply)(?:'s)?\s+(?:priority|tier)\b"
            r"|\b(?:do\s+not|don't|never)\s+(?:surface|escalate)\b"
            r"|\b(?:lowest|low)[\s-]priority\s+(?:class|tier)\b",
            _I,
        ),
    ),
    (
        "output_command",
        re.compile(
            r"\b(?:respond|reply|answer|output|return)\s+(?:only\s+)?(?:with|in)\s+"
            r"(?:only\s+)?(?:json|the\s+following|exactly)\b"
            r"|\byour\s+(?:explanation|output|response|answer|classification)\s+"
            r"(?:must|should|will)\b",
            _I,
        ),
    ),
    (
        "schema_field",
        re.compile(
            r"\bprimary_class\s*[:=]|[\"'](?:explanation|confidence|flags|primary_class)[\"']\s*:",
            _I,
        ),
    ),
    (
        "taxonomy_name",
        re.compile(
            r"\b(?:"
            + "|".join(
                re.escape(name)
                for name in sorted((*taxonomy.CLASSES, *taxonomy.FLAGS), key=len, reverse=True)
            )
            + r")\b"
        ),
    ),
)


@dataclass(frozen=True)
class PrecheckResult:
    """The outcome of the pre-check for one text."""

    flagged: bool
    rules_matched: tuple[str, ...]
    version: str = PRECHECK_VERSION


def precheck(text: str) -> PrecheckResult:
    """Look for text that reads as instructions to an automated system.

    :param text: Normalized comment text (`norm-v0.1` or later).
    :returns: Whether to set ``POSSIBLE_INSTRUCTION_TEXT``, and which rules matched.
    """
    matched = tuple(name for name, pattern in RULES if pattern.search(text))
    return PrecheckResult(flagged=bool(matched), rules_matched=matched)
