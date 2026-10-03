from __future__ import annotations

import json
from pathlib import Path

import pytest

from afterword import display
from afterword.normalize import (
    NORMALIZATION_VERSION,
    Link,
    normalize,
    text_changed,
    text_hash,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "dev-api"

# DEV-style code block: a highlighted <pre> plus an action panel with icons.
DEV_CODE_BLOCK = (
    '<div class="highlight js-code-highlight">\n'
    '<pre class="highlight python"><code><span class="k">def</span> <span class="nf">f</span>():\n'
    '    <span class="k">return</span> 1\n'
    "</code></pre>\n"
    '<div class="highlight__panel js-actions-panel">\n'
    '<div class="highlight__panel-action js-fullscreen-code-action">\n'
    '<svg><title>Enter fullscreen mode</title><path d="M0"></path></svg>\n'
    '<svg><title>Exit fullscreen mode</title><path d="M0"></path></svg>\n'
    "</div>\n</div>\n</div>\n"
)


def text(html: str) -> str:
    return normalize(html, "HTML").text


def test_version_and_hash_are_recorded():
    result = normalize("<p>Hello</p>", "HTML")
    assert result.version == NORMALIZATION_VERSION == "norm-v0.1"
    assert result.text == "Hello"
    assert result.text_hash == text_hash("Hello")
    assert len(result.text_hash) == 64


def test_code_blocks_are_fenced_with_language_and_whitespace_kept():
    result = normalize(f"<p>Try this:</p>{DEV_CODE_BLOCK}<p>Works for me.</p>", "HTML")
    assert result.text == "Try this:\n\n```python\ndef f():\n    return 1\n```\n\nWorks for me."
    assert result.code_blocks == 1
    assert result.has_code


def test_renderer_chrome_is_dropped():
    assert "fullscreen" not in text(DEV_CODE_BLOCK)
    assert text("<p>a<script>alert(1)</script><style>p{}</style><button>Copy</button>b</p>") == "ab"


def test_plain_code_block_has_no_language():
    assert (
        text('<pre class="highlight plaintext"><code>x  =  1\n</code></pre>') == "```\nx  =  1\n```"
    )


def test_inline_code_is_backticked_and_counted():
    result = normalize("<p>Use <code>--yes</code> and <code>-q</code>.</p>", "HTML")
    assert result.text == "Use `--yes` and `-q`."
    assert result.inline_code == 2
    assert result.code_blocks == 0
    assert result.has_code


def test_links_keep_text_and_target_as_structure():
    result = normalize(
        '<p>See <a href="https://example.com/docs">the docs</a> or '
        '<a href="https://example.com">https://example.com</a>.</p>',
        "HTML",
    )
    assert result.text == "See [the docs](https://example.com/docs) or <https://example.com>."
    assert result.links == (
        Link("the docs", "https://example.com/docs"),
        Link("https://example.com", "https://example.com"),
    )
    assert result.has_link


def test_fragment_and_empty_links_are_plain_text():
    result = normalize('<p><a href="#fn1">1</a> and <a>bare</a></p>', "HTML")
    assert result.text == "1 and bare"
    assert result.links == ()


def test_images_embeds_quotes_lists_and_rules():
    html = (
        '<p><img src="x.png" alt="latency  chart"><img src="y.png"></p>'
        '<iframe src="https://example.com/embed"></iframe>'
        "<blockquote><p>quoted line</p></blockquote>"
        "<ol><li>one<ul><li>nested</li></ul></li><li>two</li></ol>"
        "<hr><p>end</p>"
    )
    result = normalize(html, "HTML")
    assert result.text == (
        "[image: latency chart][image]\n\n"
        "[embed: https://example.com/embed]\n\n"
        "> quoted line\n\n"
        "1. one\n  - nested\n2. two\n\n"
        "---\n\nend"
    )
    assert result.images == 2


def test_tables_keep_cells_apart():
    html = "<table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>"
    assert text(html) == "a | b\n1 | 2"


def test_whitespace_entities_and_unicode_are_normalized():
    # A no-break space is whitespace like any other outside code.
    assert text("<p>  a \n\t b&nbsp;&amp;  c </p><p></p><p></p><p>d</p>") == "a b & c\n\nd"
    assert text("<p>cafe" + chr(0x301) + "</p>") == "caf" + chr(0xE9)


def test_hidden_control_and_format_characters_are_removed():
    # Zero-width space, a right-to-left override, and an escape sequence.
    result = text("<p>ok&#8203;" + chr(0x202E) + "evil[2J</p>")
    assert result == "okevil[2J"


def test_unclosed_markup_is_still_closed():
    assert text("<pre>unclosed <b>x") == "```\nunclosed x\n```"
    assert text("<p>start <code>open") == "start `open`"
    assert text('<p><a href="https://example.com">dangling') == "[dangling](https://example.com)"


def test_empty_and_non_html_bodies():
    assert normalize(None, "HTML").text == ""
    assert normalize("", "TEXT").text_hash == text_hash("")
    assert normalize("  plain\ttext \n", "TEXT").text == "plain text"
    with pytest.raises(ValueError):
        normalize("x", "RTF")


def test_differs_from_the_display_rendering():
    # norm-v0.1 writes links as [text](url); display-v0.1 writes "text <url>".
    html = '<p><a href="https://example.com/a">docs</a></p>'
    assert text(html) != display.html_to_display_text(html)


# Edit detection (DATA-MODEL.md lifecycle: compare normalized text, not payload hashes).


def test_a_rendering_change_with_the_same_text_is_not_an_edit():
    before = "<p>Use <code>x</code>.</p>\n"
    after = '<p class="new-renderer">Use   <code>x</code>.</p>'
    assert not text_changed(before, "HTML", after, "HTML")


def test_changed_words_are_an_edit():
    assert text_changed("<p>Use x.</p>", "HTML", "<p>Use y.</p>", "HTML")


def test_a_changed_link_target_is_an_edit():
    before = '<p><a href="https://example.com/a">docs</a></p>'
    after = '<p><a href="https://example.com/b">docs</a></p>'
    assert text_changed(before, "HTML", after, "HTML")


def test_expected_output_for_the_synthetic_dev_comments():
    expected = json.loads(
        (FIXTURES / "expected" / f"comments-by-article.{NORMALIZATION_VERSION}.json").read_text(
            encoding="utf-8"
        )
    )
    roots = json.loads((FIXTURES / "source" / "comments-by-article.json").read_text("utf-8"))
    seen: dict[str, str] = {}

    def walk(node: dict) -> None:
        seen[node["id_code"]] = normalize(node["body_html"], "HTML").text
        for child in node["children"]:
            walk(child)

    for root in roots:
        walk(root)
    assert seen == expected["texts"]
