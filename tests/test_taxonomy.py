from __future__ import annotations

import re
from pathlib import Path

from afterword import labeling, policy, taxonomy

DOC = (Path(__file__).resolve().parents[1] / "docs" / "TAXONOMY.md").read_text(encoding="utf-8")


def test_version_matches_the_document():
    assert f"`{taxonomy.TAXONOMY_VERSION}`" in DOC.split("\n", 4)[2]


def test_classes_follow_the_documented_precedence_then_uncertain():
    section = DOC.split("## Precedence rule", 1)[1].split("##", 1)[0]
    documented = re.findall(r"^\d+\. `([A-Z_]+)`", section, re.MULTILINE)
    assert (*documented, "UNCERTAIN") == taxonomy.CLASSES


def test_flags_match_the_documented_table_in_order():
    section = DOC.split("## Flags", 1)[1]
    documented = tuple(re.findall(r"^\| `([A-Z_]+)` \|", section, re.MULTILINE))
    assert documented == taxonomy.FLAGS


def test_every_name_has_a_one_line_definition():
    assert set(taxonomy.CLASS_DEFINITIONS) == set(taxonomy.CLASSES)
    assert set(taxonomy.FLAG_DEFINITIONS) == set(taxonomy.FLAGS)
    for text in (*taxonomy.CLASS_DEFINITIONS.values(), *taxonomy.FLAG_DEFINITIONS.values()):
        assert text and "\n" not in text and len(text) <= 90


def test_flag_definitions_agree_with_the_document_table():
    for name in taxonomy.FLAGS:
        row = re.search(rf"^\| `{name}` \| (.+?) \|$", DOC, re.MULTILINE)
        assert row is not None
        # The help line may shorten the row but must start from the same idea.
        first_word = taxonomy.FLAG_DEFINITIONS[name].split()[0].lower()
        assert first_word in row.group(1).lower()


def test_labeling_and_policy_use_the_same_names():
    assert labeling.CLASSES == taxonomy.CLASSES
    assert set(labeling.LABELER_FLAGS) == set(taxonomy.FLAGS) - taxonomy.STRUCTURAL_FLAGS
    assert set(policy.CLASS_DEFAULTS) == set(taxonomy.CLASSES)
