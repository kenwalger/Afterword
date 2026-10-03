from __future__ import annotations

import pytest

from afterword.heuristic import HEURISTIC_VERSION, LONG_THRESHOLD, classify, features, prose
from afterword.normalize import normalize

LONG = "word " * (LONG_THRESHOLD // 5 + 1)


def b1(html: str):
    return classify(normalize(html, "HTML"))


@pytest.mark.parametrize(
    ("html", "cls", "rule"),
    [
        ("<p>Step 2 is wrong.</p>", "CORRECTION", "lexicon"),
        ("<p>This doesn&#8217;t work on 3.12.</p>", "CORRECTION", "lexicon"),
        ("<p>Actually, is it outdated?</p>", "CORRECTION", "lexicon"),
        (
            "<p>Why not use a queue?</p><pre><code>q = []</code></pre>",
            "TECHNICAL_QUESTION",
            "question_technical",
        ),
        (f"<p>{LONG} so how does it scale?</p>", "TECHNICAL_QUESTION", "question_technical"),
        ("<p>Part two soon?</p>", "DIRECT_QUESTION", "question"),
        ("<p>Mine:</p><pre><code>x = 1</code></pre>", "TECHNICAL_EXTENSION", "code_block"),
        (
            f'<p>{LONG} <a href="https://example.com">ref</a></p>',
            "TECHNICAL_EXTENSION",
            "link_long",
        ),
        (f"<p>{LONG}</p>", "CONVERSATIONAL", "long"),
        ("<p>Great post!</p>", "LIGHTWEIGHT_ACKNOWLEDGMENT", "default"),
        ('<p><a href="https://example.com">link</a></p>', "LIGHTWEIGHT_ACKNOWLEDGMENT", "default"),
    ],
)
def test_rules_fire_in_order(html, cls, rule):
    result = b1(html)
    assert (result.primary_class, result.rule) == (cls, rule)
    assert result.version == HEURISTIC_VERSION == "hb-v0.1"
    assert result.explanation == f"hb-v0.1 rule {rule}"


def test_code_does_not_count_as_prose():
    # A ternary's "?" and "error" in a trace are inside code, not questions or corrections.
    result = b1(
        "<p>Here:</p><pre><code>x = a ? b : c  # error</code></pre><p>Use <code>err?</code></p>"
    )
    assert not result.features.question
    assert not result.features.lexicon_match
    assert result.primary_class == "TECHNICAL_EXTENSION"


def test_link_targets_are_not_prose():
    assert (
        prose("see [docs](https://example.com/wrong?) and <https://example.com/error>")
        == "see docs and"
    )


def test_lexicon_matches_whole_words_only():
    assert not b1("<p>Wrongly accused, errors aside, I agree.</p>").features.lexicon_match


def test_content_flags_come_from_structure():
    assert b1("<p>Use <code>x</code></p>").flags == {"CONTAINS_CODE"}
    assert b1('<p><a href="https://example.com">a</a></p>').flags == {"CONTAINS_LINK"}
    assert b1("<p>plain</p>").flags == frozenset()


def test_length_threshold_boundary():
    at = "x" * LONG_THRESHOLD
    below = "x" * (LONG_THRESHOLD - 1)
    assert features(normalize(at, "TEXT")).long
    assert not features(normalize(below, "TEXT")).long


def test_b1_never_sets_model_judgment_flags():
    result = b1(f"<p>{LONG} you are wrong, this is rude and refers to step 3?</p>")
    assert result.flags <= {"CONTAINS_CODE", "CONTAINS_LINK"}
