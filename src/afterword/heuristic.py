"""Heuristic baseline B1 (`hb-v0.1`, `docs/EVALUATION.md`).

Rule-based classification from the candidate features in EVALUATION.md only:
question mark, code block, link, length, and a small lexicon of correction and
challenge markers. ``REPLY_TO_AUTHOR`` is structural and is applied by the
priority policy, not here. The result feeds the same policy as the model (B2).

`hb-v0.1` is a draft written before any labels existed. Its threshold and
lexicon are tuned on `dev`; every change is a new heuristic version.

Features are computed on prose only: fenced code blocks and inline code are
removed first, so a ``?`` in a ternary or the word "error" in a stack trace does
not count as a question or a correction marker.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from afterword.normalize import NormalizedText

HEURISTIC_VERSION: str = "hb-v0.1"

# Prose characters (code removed) at or above which a comment counts as long.
LONG_THRESHOLD: int = 280

# Correction and challenge markers from EVALUATION.md.
LEXICON: tuple[str, ...] = ("actually", "doesn't work", "wrong", "error", "outdated", "breaks")

_FENCED: re.Pattern[str] = re.compile(r"```.*?```", re.DOTALL)
_INLINE: re.Pattern[str] = re.compile(r"`[^`\n]*`")
_LINK: re.Pattern[str] = re.compile(
    r"\[([^\]]*)\]\([^)\s]*\)|<[a-z][a-z0-9+.-]*:[^>\s]*>", re.IGNORECASE
)
_LEXICON: re.Pattern[str] = re.compile(
    r"\b(?:" + "|".join(re.escape(w).replace("'", "['\\u2019]") for w in LEXICON) + r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Features:
    """What `hb-v0.1` looks at."""

    question: bool
    code_block: bool
    link: bool
    long: bool
    lexicon_match: bool
    prose_length: int


@dataclass(frozen=True)
class HeuristicResult:
    """B1's classification of one comment."""

    primary_class: str
    flags: frozenset[str]
    rule: str
    features: Features
    version: str = HEURISTIC_VERSION

    @property
    def explanation(self) -> str:
        """A one-line, auditable account of which rule fired.

        :returns: The heuristic version and rule name.
        """
        return f"{self.version} rule {self.rule}"


def prose(text: str) -> str:
    """Remove code and link targets, leaving the text a reader would scan as prose.

    :param text: Normalized text.
    :returns: Text without fenced blocks or inline code; links keep their text only.
    """
    without_code = _INLINE.sub(" ", _FENCED.sub(" ", text))
    return re.sub(r"\s+", " ", _LINK.sub(lambda m: m.group(1) or " ", without_code)).strip()


def features(normalized: NormalizedText) -> Features:
    """Compute `hb-v0.1` features.

    :param normalized: The comment's normalized text and structure.
    :returns: The features.
    """
    plain = prose(normalized.text)
    return Features(
        question="?" in plain,
        code_block=normalized.code_blocks > 0,
        link=normalized.has_link,
        long=len(plain) >= LONG_THRESHOLD,
        lexicon_match=_LEXICON.search(plain) is not None,
        prose_length=len(plain),
    )


def classify(normalized: NormalizedText) -> HeuristicResult:
    """Classify one comment with `hb-v0.1`.

    Rules, first match wins:

    1. a lexicon marker: ``CORRECTION``;
    2. a question mark: ``TECHNICAL_QUESTION`` with a code block or long prose,
       otherwise ``DIRECT_QUESTION``;
    3. a code block, or a link in long prose: ``TECHNICAL_EXTENSION``;
    4. long prose: ``CONVERSATIONAL``;
    5. otherwise: ``LIGHTWEIGHT_ACKNOWLEDGMENT``.

    :param normalized: The comment's normalized text and structure.
    :returns: Class proxy, content flags, the rule that fired, and the features.
    """
    f = features(normalized)
    flags = set()
    if normalized.has_code:
        flags.add("CONTAINS_CODE")
    if f.link:
        flags.add("CONTAINS_LINK")

    if f.lexicon_match:
        primary, rule = "CORRECTION", "lexicon"
    elif f.question and (f.code_block or f.long):
        primary, rule = "TECHNICAL_QUESTION", "question_technical"
    elif f.question:
        primary, rule = "DIRECT_QUESTION", "question"
    elif f.code_block:
        primary, rule = "TECHNICAL_EXTENSION", "code_block"
    elif f.link and f.long:
        primary, rule = "TECHNICAL_EXTENSION", "link_long"
    elif f.long:
        primary, rule = "CONVERSATIONAL", "long"
    else:
        primary, rule = "LIGHTWEIGHT_ACKNOWLEDGMENT", "default"
    return HeuristicResult(primary_class=primary, flags=frozenset(flags), rule=rule, features=f)
