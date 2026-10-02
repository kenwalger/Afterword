from __future__ import annotations

import json

from afterword.adapters.dev.shapes import summarize


def test_summary_contains_no_values():
    sample = {
        "body_html": "<p>private words from a commenter</p>",
        "user": {"name": "Real Person Name", "user_id": 987654},
        "created_at": "2026-01-02T03:04:05Z",
        "flag": True,
    }
    out = json.dumps(summarize([sample]))
    for value in ("private words", "Real Person Name", "987654", "2026-01-02"):
        assert value not in out


def test_paths_types_formats_and_presence():
    out = summarize(
        [
            {"id_code": "ab1", "created_at": "2026-01-02T03:04:05Z", "body_html": "<p>x</p>"},
            {"id_code": "ab2", "created_at": "2026-01-02T03:04:05Z"},
        ]
    )
    paths = out["paths"]
    assert out["samples"] == 2
    assert paths["$.id_code"]["seen"] == 2
    assert paths["$.body_html"]["seen"] == 1
    assert paths["$.created_at"]["string_formats"] == {"timestamp-tz": 2}
    assert paths["$.body_html"]["string_formats"] == {"html": 1}


def test_opaque_keys_are_not_entered():
    tree = {"id_code": "a", "children": [{"id_code": "b", "children": []}]}
    paths = summarize([tree], opaque_keys=frozenset({"children"}))["paths"]
    assert paths["$.children"]["types"] == {"list": 1}
    assert paths["$.children"]["length"] == [1, 1]
    assert not any(p.startswith("$.children[]") for p in paths)
