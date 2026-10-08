"""Local, deterministic language detection for counts only (session 8, Part C2).

An analysis aid, not a structural field: nothing here is stored on a comment or
used by the policy. It runs `py3langid` (the analysis dependency group), on the
machine, with its normalized probabilities, so the same text always gives the
same answer and nothing leaves the machine.

Two guardrails, set by the author before any count was made:

- Text shorter than :data:`MIN_CHARS` characters of prose (normalized text with
  code and link targets removed) is ``too_short``, not assigned a language.
- A detection whose normalized confidence is below :data:`MIN_CONFIDENCE` is
  ``uncertain``, not assigned a language.

If language becomes a runtime structural field, the detector is chosen again
then (`docs/FUTURE-FEATURES.md`, "Multilingual comments").
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import Any

DETECTOR: str = "py3langid-0.4.0"
# Prose characters below which no language is assigned.
MIN_CHARS: int = 40
# Normalized confidence below which no language is assigned.
MIN_CONFIDENCE: float = 0.80
TOO_SHORT: str = "too_short"
UNCERTAIN: str = "uncertain"


@dataclass(frozen=True)
class LanguageGuess:
    """The detector's answer for one text.

    ``language`` is an ISO 639-1 code, or :data:`TOO_SHORT` or :data:`UNCERTAIN`.
    """

    language: str
    confidence: float | None


@cache
def _identifier() -> Any:
    from py3langid.langid import MODEL_FILE, LanguageIdentifier  # type: ignore[import-untyped]

    return LanguageIdentifier.from_model_file(MODEL_FILE, norm_probs=True)


def detect(prose: str) -> LanguageGuess:
    """Detect the language of a comment's prose, with the two guardrails applied.

    :param prose: Normalized text with code and link targets removed
        (:func:`afterword.heuristic.prose`).
    :returns: The language, or ``too_short`` or ``uncertain``.
    """
    text = prose.strip()
    if len(text) < MIN_CHARS:
        return LanguageGuess(TOO_SHORT, None)
    language, confidence = _identifier().classify(text)
    confidence = float(confidence)
    if confidence < MIN_CONFIDENCE:
        return LanguageGuess(UNCERTAIN, round(confidence, 4))
    return LanguageGuess(str(language), round(confidence, 4))
