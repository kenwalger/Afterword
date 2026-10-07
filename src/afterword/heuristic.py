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

# Every heuristic version and its length threshold. Versions differ only in the
# threshold so far: `hb-v0.2` (2026-10-07) is `hb-v0.1` with the threshold tuned
# on `dev` labels (EVALUATION.md, "B1 heuristic rules"). Tuning, not measurement.
HEURISTIC_VERSIONS: dict[str, int] = {"hb-v0.1": LONG_THRESHOLD, "hb-v0.2": 281}

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


def features(normalized: NormalizedText, long_threshold: int = LONG_THRESHOLD) -> Features:
    """Compute the heuristic's features.

    :param normalized: The comment's normalized text and structure.
    :param long_threshold: Prose length at or above which a comment counts as long.
    :returns: The features.
    """
    plain = prose(normalized.text)
    return Features(
        question="?" in plain,
        code_block=normalized.code_blocks > 0,
        link=normalized.has_link,
        long=len(plain) >= long_threshold,
        lexicon_match=_LEXICON.search(plain) is not None,
        prose_length=len(plain),
    )


def decide(f: Features) -> tuple[str, str]:
    """Apply the rules to computed features.

    :param f: Features, with ``long`` set by the version's threshold.
    :returns: The class proxy and the rule that fired (see :func:`classify`).
    """
    if f.lexicon_match:
        return "CORRECTION", "lexicon"
    if f.question and (f.code_block or f.long):
        return "TECHNICAL_QUESTION", "question_technical"
    if f.question:
        return "DIRECT_QUESTION", "question"
    if f.code_block:
        return "TECHNICAL_EXTENSION", "code_block"
    if f.link and f.long:
        return "TECHNICAL_EXTENSION", "link_long"
    if f.long:
        return "CONVERSATIONAL", "long"
    return "LIGHTWEIGHT_ACKNOWLEDGMENT", "default"


def classify(normalized: NormalizedText, version: str = HEURISTIC_VERSION) -> HeuristicResult:
    """Classify one comment with a heuristic version.

    Rules, first match wins:

    1. a lexicon marker: ``CORRECTION``;
    2. a question mark: ``TECHNICAL_QUESTION`` with a code block or long prose,
       otherwise ``DIRECT_QUESTION``;
    3. a code block, or a link in long prose: ``TECHNICAL_EXTENSION``;
    4. long prose: ``CONVERSATIONAL``;
    5. otherwise: ``LIGHTWEIGHT_ACKNOWLEDGMENT``.

    :param normalized: The comment's normalized text and structure.
    :param version: One of :data:`HEURISTIC_VERSIONS`.
    :returns: Class proxy, content flags, the rule that fired, and the features.
    :raises ValueError: For an unknown version.
    """
    if version not in HEURISTIC_VERSIONS:
        raise ValueError(f"unknown heuristic version: {version}")
    f = features(normalized, HEURISTIC_VERSIONS[version])
    # Code and link flags are structural from tax-v0.2: the service sets them from
    # normalization for B1 and B2 alike, so the heuristic sets no flags itself.
    primary, rule = decide(f)
    return HeuristicResult(
        primary_class=primary, flags=frozenset(), rule=rule, features=f, version=version
    )
