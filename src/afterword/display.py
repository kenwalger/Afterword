"""HTML to terminal text, for DISPLAY ONLY (`display-v0.1`).

This is not the versioned classification normalization planned for Stage 2.
It exists so a human can read a comment in a terminal while labeling or timing
a review. Nothing it produces is stored as comment text, hashed, or sent
anywhere; labels record only that the labeler saw `display-v0.1`.

Comment HTML is untrusted (ADR-008). Besides dropping tags, the output has
terminal control characters removed, so a comment cannot move the cursor,
recolor the screen, or hide text from the labeler.
"""

from __future__ import annotations

import re
import unicodedata
from html.parser import HTMLParser

DISPLAY_VERSION: str = "display-v0.1"

_BLOCKS: frozenset[str] = frozenset(
    {"p", "div", "ul", "ol", "table", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "hr"}
)
_KEEP_CONTROLS: frozenset[str] = frozenset({"\n", "\t"})


def strip_controls(text: str) -> str:
    """Remove control and format characters (ESC, bidi overrides), keeping newline and tab.

    :param text: Untrusted text.
    :returns: Text that cannot drive the terminal.
    """
    return "".join(
        ch for ch in text if ch in _KEEP_CONTROLS or unicodedata.category(ch) not in ("Cc", "Cf")
    )


class _Renderer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.pre = 0
        self.code = 0
        self.quote = 0
        self.lists: list[list[int]] = []  # one entry per open list: [next number] or [] if bulleted
        self.href: list[str | None] = []
        self.link_text: list[int] = []

    def _newline(self, blank: bool = False) -> None:
        text = "".join(self.out)
        if not text:
            return
        trailing = len(text) - len(text.rstrip("\n"))
        need = 2 if blank else 1
        self.out.append("\n" * max(need - trailing, 0))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _BLOCKS:
            self._newline(blank=tag not in ("tr",))
        if tag == "br":
            self.out.append("\n")
        elif tag == "pre":
            self._newline(blank=True)
            self.out.append("```\n")
            self.pre += 1
        elif tag == "code" and not self.pre:
            self.out.append("`")
            self.code += 1
        elif tag == "blockquote":
            self._newline(blank=True)
            self.quote += 1
        elif tag in ("ul", "ol"):
            self.lists.append([1] if tag == "ol" else [])
        elif tag == "li":
            self._newline()
            indent = "  " * max(len(self.lists) - 1, 0)
            if self.lists and self.lists[-1]:
                self.out.append(f"{indent}{self.lists[-1][0]}. ")
                self.lists[-1][0] += 1
            else:
                self.out.append(f"{indent}- ")
        elif tag == "a":
            self.href.append(dict(attrs).get("href"))
            self.link_text.append(len(self.out))
        elif tag == "img":
            alt = dict(attrs).get("alt") or "image"
            self.out.append(f"[{alt}]")
        elif tag in ("td", "th"):
            self.out.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "pre" and self.pre:
            self.pre -= 1
            if not "".join(self.out).endswith("\n"):
                self.out.append("\n")
            self.out.append("```")
            self._newline(blank=True)
        elif tag == "code" and self.code and not self.pre:
            self.code -= 1
            self.out.append("`")
        elif tag == "blockquote" and self.quote:
            self.quote -= 1
            self._newline(blank=True)
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self._newline(blank=True)
        elif tag == "a" and self.href:
            href = self.href.pop()
            start = self.link_text.pop()
            shown = "".join(self.out[start:]).strip()
            if href and href != shown:
                self.out.append(f" <{href}>")
        elif tag in _BLOCKS:
            self._newline(blank=True)

    def handle_data(self, data: str) -> None:
        if not self.pre:
            data = re.sub(r"\s+", " ", data)
            if "".join(self.out).endswith(("\n", " ")) or not self.out:
                data = data.lstrip(" ")
        if self.quote and not self.pre:
            text = "".join(self.out)
            if not text or text.endswith("\n"):
                data = "> " * self.quote + data
        self.out.append(data)


def html_to_display_text(html: str | None) -> str:
    """Render comment HTML as readable terminal text. Display only.

    Code blocks are fenced with backticks, inline code is backticked, and links
    keep their URL.

    :param html: Comment HTML, or ``None``.
    :returns: Plain text with terminal control characters removed.
    """
    if not html:
        return ""
    renderer = _Renderer()
    renderer.feed(html)
    renderer.close()
    text = strip_controls("".join(renderer.out))
    lines = [line.rstrip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")
