"""JSONL readers split records at LF only, never inside text (session 16b; synthetic only).

``json.dumps(..., ensure_ascii=False)`` leaves U+2028 and U+2029 unescaped, and
``str.splitlines`` splits at both, so a record holding one broke in two.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from afterword import bench, label_records, labeling, shadow

SEPARATORS = f"synthetic a{chr(0x2028)}b{chr(0x2029)}c"


def jsonl(records: list[dict[str, Any]]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def label(comment_id: str) -> dict[str, Any]:
    return {
        "comment_id": comment_id,
        "pass": "initial",
        "batch_id": "b1",
        "corpus_set": "test",
        "labeled_at": "2026-08-19T10:00:00Z",
        "primary_class": "CONVERSATIONAL",
        "consequential_prospective": 1,
        "reason": f"typed reason {SEPARATORS}",
        "note": f"typed note {SEPARATORS}",
    }


def test_label_records_keep_separators_in_typed_reason_and_note(tmp_path: Path) -> None:
    out = label_records.label_dir(tmp_path, "unfrozen")
    out.mkdir(parents=True)
    (out / "initial.jsonl").write_text(jsonl([label("a"), label("b")]), encoding="utf-8")
    labels = label_records.read_labels(tmp_path, "unfrozen")
    assert [r["comment_id"] for r in labels] == ["a", "b"]
    assert labels[0]["reason"] == f"typed reason {SEPARATORS}"
    assert labels[1]["note"] == f"typed note {SEPARATORS}"


def test_the_labeling_tool_reads_its_own_records_back(tmp_path: Path) -> None:
    path = tmp_path / "initial.jsonl"
    for comment_id in ("a", "b"):
        labeling._append_jsonl(path, label(comment_id))
    assert labeling._labeled_ids(path) == {"a", "b"}
    batches = tmp_path / "batches.jsonl"
    labeling._append_jsonl(batches, {"batch_id": "b1", "note": f"typed note {SEPARATORS}"})
    labeling._append_jsonl(batches, {"batch_id": "b2", "note": f"typed note {SEPARATORS}"})
    assert labeling._batch_ids(batches) == {"b1", "b2"}


def test_sealed_records_keep_separators(tmp_path: Path) -> None:
    records = [
        {"condition": "b1", "comment_id": "a", "rule": SEPARATORS},
        {"condition": "b2", "comment_id": "a", "rule": SEPARATORS},
    ]
    path = tmp_path / "shadow-x.jsonl"
    path.write_bytes(shadow.canonical_bytes(records))
    read = shadow.read_sealed(path)
    assert [r["condition"] for r in read] == ["b1", "b2"] and read[0]["rule"] == SEPARATORS


def test_the_ledger_keeps_separators(tmp_path: Path) -> None:
    path = tmp_path / shadow.LEDGER_PATH
    path.parent.mkdir(parents=True)
    entries = [{"file": "a.jsonl", "note": SEPARATORS}, {"file": "b.jsonl", "note": SEPARATORS}]
    path.write_text(jsonl(entries), encoding="utf-8")
    assert [e["file"] for e in shadow.read_ledger(tmp_path)] == ["a.jsonl", "b.jsonl"]


def test_bench_reads_synthetic_cases_with_separators(tmp_path: Path) -> None:
    cases = [
        {"case_id": f"c{i}", "set": "adversarial", "provenance": "synthetic", "comment": SEPARATORS}
        for i in (1, 2)
    ]
    raw = jsonl(cases).encode("utf-8")
    corpus_dir = tmp_path / bench.CORPUS_DIR
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "adversarial.jsonl").write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    (tmp_path / bench.MANIFEST).write_text(
        f"| `adversarial.jsonl` | `adversarial` | 2 | synthetic | `{sha}` |\n", encoding="utf-8"
    )
    loaded = bench.load_cases(tmp_path, ["adversarial"])
    assert [c["case_id"] for c in loaded] == ["c1", "c2"] and loaded[0]["comment"] == SEPARATORS
