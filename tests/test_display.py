from __future__ import annotations

from afterword.display import html_to_display_text, strip_controls


def test_paragraphs_and_line_breaks():
    text = html_to_display_text("<p>First   line<br>second</p>\n<p>Next paragraph.</p>")
    assert text == "First line\nsecond\n\nNext paragraph."


def test_code_blocks_are_fenced_and_keep_whitespace():
    html = "<p>Try:</p><pre><code>def f():\n    return 1\n</code></pre><p>Done.</p>"
    assert html_to_display_text(html) == "Try:\n\n```\ndef f():\n    return 1\n```\n\nDone."


def test_inline_code_and_entities():
    assert html_to_display_text("<p>Use <code>a &lt; b</code> &amp; more</p>") == (
        "Use `a < b` & more"
    )


def test_links_keep_their_url_once():
    html = (
        '<p><a href="https://example.invalid/doc">the docs</a> and '
        '<a href="https://example.invalid/x">https://example.invalid/x</a></p>'
    )
    assert html_to_display_text(html) == (
        "the docs <https://example.invalid/doc> and https://example.invalid/x"
    )


def test_lists_and_quotes():
    html = (
        "<ul><li>one</li><li>two</li></ul><ol><li>first</li></ol>"
        "<blockquote><p>quoted</p></blockquote>"
    )
    assert html_to_display_text(html) == "- one\n- two\n\n1. first\n\n> quoted"


def test_terminal_control_sequences_are_removed():
    html = "<p>\x1b[2J\x1b[31mred\x1b[0m and \u202ereversed\u202c</p>"
    text = html_to_display_text(html)
    assert "\x1b" not in text
    assert "\u202e" not in text
    assert text == "[2J[31mred[0m and reversed"
    assert strip_controls("a\tb\nc\x07") == "a\tb\nc"


def test_empty_input():
    assert html_to_display_text(None) == ""
    assert html_to_display_text("") == ""
