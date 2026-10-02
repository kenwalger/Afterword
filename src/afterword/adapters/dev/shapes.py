"""Structural summaries of JSON payloads that contain no values.

The output records key paths, JSON types, presence counts, coarse string
formats, and lengths. It never records a string, number, or other value,
so it is safe to read without exposing comment text or commenter names.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from typing import Any


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _string_format(value: str) -> str:
    if not value:
        return "empty"
    if value.isdigit():
        return "digits"
    try:
        parsed = datetime.fromisoformat(value)
        return "timestamp-tz" if parsed.tzinfo else "timestamp-naive"
    except ValueError:
        pass
    if value.startswith(("http://", "https://")):
        return "url"
    if value.lstrip().startswith("<"):
        return "html"
    return "text"


class _Entry:
    def __init__(self) -> None:
        self.seen = 0
        self.types: Counter[str] = Counter()
        self.formats: Counter[str] = Counter()
        self.len_min: int | None = None
        self.len_max: int | None = None

    def length(self, n: int) -> None:
        self.len_min = n if self.len_min is None else min(self.len_min, n)
        self.len_max = n if self.len_max is None else max(self.len_max, n)

    def finish(self) -> dict[str, Any]:
        out: dict[str, Any] = {"seen": self.seen, "types": dict(sorted(self.types.items()))}
        if self.formats:
            out["string_formats"] = dict(sorted(self.formats.items()))
        if self.len_min is not None:
            out["length"] = [self.len_min, self.len_max]
        return out


def summarize(
    objects: Iterable[Any], *, opaque_keys: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """Summarize many samples of one response shape.

    Keys in ``opaque_keys`` are summarized by type and length but not entered,
    which keeps recursive structures such as comment ``children`` flat.

    :param objects: Samples of the same payload shape.
    :param opaque_keys: Keys whose values are not descended into.
    :returns: Sample count and, per key path, presence, types, string formats, and lengths.
    """
    entries: dict[str, _Entry] = {}
    samples = 0

    def walk(value: Any, path: str, recurse: bool) -> None:
        entry = entries.setdefault(path, _Entry())
        entry.seen += 1
        entry.types[_type_name(value)] += 1
        if isinstance(value, str):
            entry.formats[_string_format(value)] += 1
            entry.length(len(value))
        elif isinstance(value, list):
            entry.length(len(value))
            if recurse:
                for item in value:
                    walk(item, f"{path}[]", True)
        elif isinstance(value, dict) and recurse:
            for key, child in value.items():
                walk(child, f"{path}.{key}", key not in opaque_keys)

    for obj in objects:
        samples += 1
        walk(obj, "$", True)
    return {"samples": samples, "paths": {p: e.finish() for p, e in sorted(entries.items())}}
