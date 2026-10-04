"""The committed synthetic sets: schema, provenance, and the pre-check contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from afterword import heuristic, taxonomy
from afterword.normalize import content_flags, normalize
from afterword.policy import PolicyInput, Tier, assign
from afterword.precheck import precheck

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "fixtures" / "corpus"
SETS = {
    "adversarial": CORPUS / "adversarial.jsonl",
    "synthetic-bench": CORPUS / "synthetic-bench.jsonl",
    "synthetic-bench-v2": CORPUS / "synthetic-bench-v2.jsonl",
}
KEYS = {
    "case_id",
    "set",
    "category",
    "provenance",
    "post_title",
    "parent",
    "reply_to_author",
    "body_html",
    "body_source_format",
    "intended",
    "injection",
    "expect_precheck",
    "notes",
}
EVALUATION_CATEGORIES = {
    "short_correction",
    "long_low_information_praise",
    "polite_disagreement_with_falsifier",
    "technical_detail_in_casual_conversation",
    "question_depends_on_parent",
    "sarcasm",
    "hostile_tone_valid_correction",
    "recurring_participant_context",
    "prompt_injection",
}


def cases(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in SETS[name].read_text(encoding="utf-8").splitlines()]


def all_cases() -> list[dict[str, Any]]:
    return cases("adversarial") + cases("synthetic-bench") + cases("synthetic-bench-v2")


@pytest.mark.parametrize("case", all_cases(), ids=lambda c: c["case_id"])
def test_schema(case):
    assert set(case) == KEYS
    assert case["provenance"] == "synthetic"
    assert case["body_source_format"] == "HTML"
    assert case["intended"]["primary_class"] in taxonomy.CLASSES
    assert set(case["intended"]["flags"]) <= set(taxonomy.FLAGS)
    assert case["intended"]["consequential"] in (0, 1, 2, 3)
    assert case["reply_to_author"] == ("REPLY_TO_AUTHOR" in case["intended"]["flags"])
    if case["parent"] is not None:
        assert set(case["parent"]) == {"body_html", "by_content_author"}


def test_case_ids_are_unique_within_each_version():
    for current in (cases("adversarial") + cases("synthetic-bench"), cases("synthetic-bench-v2")):
        ids = [c["case_id"] for c in current]
        assert len(ids) == len(set(ids))


def test_bench_v2_keeps_every_v1_case_and_adds_the_tax_v0_2_boundaries():
    old, new = cases("synthetic-bench"), cases("synthetic-bench-v2")
    assert [c | {"set": "synthetic-bench-v2"} for c in old] == new[: len(old)]
    added = new[len(old) :]
    assert [c["case_id"] for c in added] == [f"bench-{n:03d}" for n in range(31, 36)]
    assert [c["intended"]["primary_class"] for c in added] == [
        "LIKELY_SPAM_OR_NOISE",
        "TECHNICAL_EXTENSION",
        "OPPORTUNITY",
        "CORRECTION",
        "LIGHTWEIGHT_ACKNOWLEDGMENT",
    ]
    for c in added:  # tax-v0.2: intended content flags are exactly what normalization sets
        intended = set(c["intended"]["flags"]) & taxonomy.CONTENT_FLAGS
        assert intended == content_flags(normalize(c["body_html"], "HTML"))
    assert "REFERENCES_SPECIFIC_CLAIM" in added[3]["intended"]["flags"]
    assert "REFERENCES_SPECIFIC_CLAIM" not in added[4]["intended"]["flags"]


def test_adversarial_set_covers_every_evaluation_category():
    assert {c["category"] for c in cases("adversarial")} >= EVALUATION_CATEGORIES
    injections = [c for c in cases("adversarial") if c["injection"]]
    assert len(injections) >= 8
    assert all(c["category"] == "prompt_injection" for c in injections)


def test_bench_set_is_class_balanced():
    counts: dict[str, int] = {}
    for c in cases("synthetic-bench"):
        counts[c["intended"]["primary_class"]] = counts.get(c["intended"]["primary_class"], 0) + 1
    assert set(counts) == set(taxonomy.CLASSES)
    assert len(set(counts.values())) == 1


@pytest.mark.parametrize("case", all_cases(), ids=lambda c: c["case_id"])
def test_precheck_matches_each_cases_expectation(case):
    assert precheck(normalize(case["body_html"], "HTML").text).flagged is case["expect_precheck"]


@pytest.mark.parametrize(
    "case", [c for c in cases("adversarial") if c["expect_precheck"]], ids=lambda c: c["case_id"]
)
def test_flagged_cases_surface_whatever_the_classifier_says(case):
    flags = frozenset({"POSSIBLE_INSTRUCTION_TEXT"})
    for cls in taxonomy.CLASSES:
        assert assign(PolicyInput("OK", cls, flags, "HIGH", False)).tier is Tier.SURFACE


@pytest.mark.parametrize("case", all_cases(), ids=lambda c: c["case_id"])
def test_b1_runs_end_to_end(case):
    normalized = normalize(case["body_html"], "HTML")
    result = heuristic.classify(normalized)
    flags = set(result.flags) | content_flags(normalized)
    if precheck(normalized.text).flagged:
        flags.add(taxonomy.POSSIBLE_INSTRUCTION_TEXT)
    if case["reply_to_author"]:
        flags.add(taxonomy.REPLY_TO_AUTHOR)
    decision = assign(PolicyInput("OK", result.primary_class, frozenset(flags), None, False))
    assert decision.rule_applied in decision.rules_fired


def test_text_rules_hold_for_committed_fixtures():
    for path in SETS.values():
        raw = path.read_text(encoding="utf-8")
        assert chr(0x2014) not in raw  # no em-dash
        bidi = f"[{chr(0x202A)}-{chr(0x202E)}{chr(0x2066)}-{chr(0x2069)}]"
        assert not re.search(bidi, raw)  # bidi characters only as entities


def test_manifest_lists_current_hashes():
    manifest = (CORPUS / "MANIFEST.md").read_text(encoding="utf-8")
    for path in SETS.values():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert f"`{path.name}`" in manifest
        assert digest in manifest, f"update the hash for {path.name} in MANIFEST.md"
