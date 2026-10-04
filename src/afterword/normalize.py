"""Comment text for classification (`norm-v0.1`).

This is the versioned Stage 2 normalization (`SCOPE.md`, Normalization). It is
deliberately separate from :mod:`afterword.display` (`display-v0.1`), which only
renders text for a human in a terminal and is never stored or hashed. The two
share only the control-character stripper.

The output is plain text that keeps structure visible instead of flattening it:

- code blocks are fenced with triple backticks (with the language when the
  source names one), and keep their internal whitespace;
- inline code is wrapped in single backticks;
- links are written ``[text](url)``, or ``<url>`` when the text is the URL;
- images are written ``[image: alt]``, embedded frames ``[embed: src]``;
- quotes are prefixed with ``> ``, list items with ``- `` or ``1. ``;
- interface chrome a renderer adds around code (buttons, icons, scripts, styles)
  is dropped.

The structure is also returned as counts and a list of links, so downstream code
(the heuristic baseline, structural flags) never re-parses the text.

Comment content is untrusted (ADR-008): control and format characters, which can
hide text or reorder it, are removed. Text is NFC-normalized.

Any change to the output for some input is a new normalization version.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser

from afterword import taxonomy
from afterword.display import strip_controls

NORMALIZATION_VERSION: str = "norm-v0.1"
SOURCE_FORMATS: frozenset[str] = frozenset({"HTML", "MARKDOWN", "TEXT"})

_BLOCKS: frozenset[str] = frozenset(
    {
        "p",
        "div",
        "section",
        "article",
        "table",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "figure",
        "figcaption",
        "details",
        "summary",
    }
)
# Elements whose content is never comment text.
_SKIP: frozenset[str] = frozenset({"svg", "button", "script", "style", "template", "noscript"})
_VOID: frozenset[str] = frozenset({"br", "hr", "img", "input", "wbr", "source", "embed"})
_NOT_LANGUAGES: frozenset[str] = frozenset({"highlight", "js-code-highlight", "plaintext", "text"})


@dataclass(frozen=True)
class Link:
    """A link found in a comment."""

    text: str
    url: str


@dataclass(frozen=True)
class NormalizedText:
    """A comment body normalized for classification."""

    text: str
    version: str
    text_hash: str
    code_blocks: int
    inline_code: int
    links: tuple[Link, ...]
    images: int

    @property
    def has_code(self) -> bool:
        """Whether the comment contains a code block or inline code.

        :returns: ``True`` when either count is non-zero.
        """
        return self.code_blocks > 0 or self.inline_code > 0

    @property
    def has_link(self) -> bool:
        """Whether the comment contains at least one link.

        :returns: ``True`` when any link was found.
        """
        return bool(self.links)


def content_flags(normalized: NormalizedText) -> frozenset[str]:
    """Set the deterministic content flags (`tax-v0.2`) from normalized structure.

    ``CONTAINS_CODE`` when the comment has a code block or any inline code span;
    ``CONTAINS_LINK`` when it has at least one link. Never judged by a labeler
    or a model.

    :param normalized: The comment's normalized text and structure.
    :returns: A subset of :data:`afterword.taxonomy.CONTENT_FLAGS`.
    """
    flags = set()
    if normalized.has_code:
        flags.add(taxonomy.CONTAINS_CODE)
    if normalized.has_link:
        flags.add(taxonomy.CONTAINS_LINK)
    return frozenset(flags)


def text_hash(text: str) -> str:
    """Hash normalized text, for edit detection and the classification cache.

    :param text: Normalized text.
    :returns: Lowercase hex SHA-256 of the UTF-8 bytes.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _language(attrs: dict[str, str | None]) -> str:
    for token in (attrs.get("class") or "").split():
        token = token.removeprefix("language-").removeprefix("lang-")
        if token and token not in _NOT_LANGUAGES and re.fullmatch(r"[A-Za-z0-9_+#.-]{1,20}", token):
            return token.lower()
    return ""


class _Normalizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0
        self.pre = 0
        self.pre_start = 0
        self.pre_language = ""
        self.code = 0
        self.quote = 0
        self.lists: list[list[int]] = []
        self.anchors: list[tuple[str | None, int]] = []
        self.code_blocks = 0
        self.inline_code = 0
        self.links: list[Link] = []
        self.images = 0

    def _text(self) -> str:
        return "".join(self.out)

    def _break(self, blank: bool) -> None:
        text = self._text()
        if not text:
            return
        trailing = len(text) - len(text.rstrip("\n"))
        self.out.append("\n" * max((2 if blank else 1) - trailing, 0))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP:
            if tag not in _VOID:
                self.skip += 1
            return
        if self.skip:
            return
        attr = dict(attrs)
        if tag == "pre":
            self.pre += 1
            if self.pre == 1:
                self._break(blank=True)
                self.pre_start = len(self.out)
                self.pre_language = _language(attr)
        elif tag == "code":
            if self.pre:
                self.pre_language = self.pre_language or _language(attr)
            else:
                self.code += 1
                self.inline_code += 1
                self.out.append("`")
        elif self.pre:
            return
        elif tag in _BLOCKS:
            self._break(blank=tag != "tr")
        elif tag == "br":
            self.out.append("\n")
        elif tag == "hr":
            self._break(blank=True)
            self.out.append("---")
            self._break(blank=True)
        elif tag == "blockquote":
            self._break(blank=True)
            self.quote += 1
        elif tag in ("ul", "ol"):
            self._break(blank=not self.lists)
            self.lists.append([1] if tag == "ol" else [])
        elif tag == "li":
            self._break(blank=False)
            indent = "  " * max(len(self.lists) - 1, 0)
            if self.lists and self.lists[-1]:
                self.out.append(f"{indent}{self.lists[-1][0]}. ")
                self.lists[-1][0] += 1
            else:
                self.out.append(f"{indent}- ")
        elif tag == "a":
            self.anchors.append((attr.get("href"), len(self.out)))
        elif tag == "img":
            self.images += 1
            alt = re.sub(r"\s+", " ", attr.get("alt") or "").strip()
            self.out.append(f"[image: {alt}]" if alt else "[image]")
        elif tag == "iframe":
            src = (attr.get("src") or "").strip()
            self.out.append(f"[embed: {src}]" if src else "[embed]")
        elif tag in ("td", "th"):
            text = self._text()
            if text and not text.endswith("\n"):
                self.out.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP:
            self.skip = max(self.skip - 1, 0)
            return
        if self.skip:
            return
        if tag == "pre" and self.pre:
            self.pre -= 1
            if not self.pre:
                self._close_pre()
        elif tag == "code" and self.code and not self.pre:
            self.code -= 1
            self.out.append("`")
        elif self.pre:
            return
        elif tag == "blockquote" and self.quote:
            self.quote -= 1
            self._break(blank=True)
        elif tag in ("ul", "ol") and self.lists:
            self.lists.pop()
            self._break(blank=not self.lists)
        elif tag == "a" and self.anchors:
            self._close_anchor()
        elif tag == "tr":
            self._break(blank=False)
        elif tag in _BLOCKS:
            self._break(blank=True)

    def _close_pre(self) -> None:
        body = "".join(self.out[self.pre_start :]).strip("\n")
        body = "\n".join(line.rstrip() for line in body.split("\n"))
        del self.out[self.pre_start :]
        self.out.append(f"```{self.pre_language}\n{body}\n```")
        self.code_blocks += 1
        self.pre_language = ""
        self._break(blank=True)

    def _close_anchor(self) -> None:
        href, start = self.anchors.pop()
        shown = "".join(self.out[start:]).strip()
        url = (href or "").strip()
        if not url or url.startswith("#"):
            return
        self.links.append(Link(text=shown, url=url))
        del self.out[start:]
        self.out.append(f"<{url}>" if shown in ("", url) else f"[{shown}]({url})")

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if not self.pre:
            data = re.sub(r"\s+", " ", data)
            text = self._text()
            if not text or text.endswith(("\n", " ")):
                data = data.lstrip(" ")
            if self.quote and data and (not text or text.endswith("\n")):
                data = "> " * self.quote + data
        self.out.append(data)


def _tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")


def _finish(text: str) -> str:
    return _tidy(strip_controls(unicodedata.normalize("NFC", text)))


def normalize(body: str | None, source_format: str) -> NormalizedText:
    """Normalize a comment body for classification.

    :param body: The body as supplied by the source; ``None`` or empty gives empty text.
    :param source_format: ``HTML``, ``MARKDOWN``, or ``TEXT``. No source supplies
        Markdown yet, so it is treated as text.
    :returns: The normalized text, its hash, and its structure.
    :raises ValueError: If the format is not one of the known formats.
    """
    if source_format not in SOURCE_FORMATS:
        raise ValueError(f"unknown source format: {source_format}")
    if not body:
        return NormalizedText("", NORMALIZATION_VERSION, text_hash(""), 0, 0, (), 0)
    if source_format != "HTML":
        lines = (re.sub(r"[ \t]+", " ", line).strip() for line in body.split("\n"))
        text = _finish("\n".join(lines))
        return NormalizedText(text, NORMALIZATION_VERSION, text_hash(text), 0, 0, (), 0)
    parser = _Normalizer()
    parser.feed(body)
    parser.close()
    if parser.pre:  # unclosed <pre>: fence what was collected
        parser.pre = 0
        parser._close_pre()
    parser.out.append("`" * parser.code)  # unclosed inline code
    while parser.anchors:
        parser._close_anchor()
    text = _finish(parser._text())
    return NormalizedText(
        text=text,
        version=NORMALIZATION_VERSION,
        text_hash=text_hash(text),
        code_blocks=parser.code_blocks,
        inline_code=parser.inline_code,
        links=tuple(Link(strip_controls(x.text), strip_controls(x.url)) for x in parser.links),
        images=parser.images,
    )


def text_changed(
    previous_body: str | None,
    previous_format: str,
    current_body: str | None,
    current_format: str,
) -> bool:
    """Decide whether a comment was edited, by comparing normalized text.

    Both bodies are normalized under the current version, so a change of
    normalization version, or a change in how the source renders the same text,
    is not an edit (`DATA-MODEL.md`, lifecycle rules).

    :param previous_body: The body from the earlier source record.
    :param previous_format: Its source format.
    :param current_body: The body from the new source record.
    :param current_format: Its source format.
    :returns: ``True`` when the normalized texts differ.
    """
    before = normalize(previous_body, previous_format).text_hash
    after = normalize(current_body, current_format).text_hash
    return before != after
