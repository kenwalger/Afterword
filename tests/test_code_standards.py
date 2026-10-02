"""Code standards that ruff and mypy do not enforce (CLAUDE.md, Code standards)."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def checked_files() -> list[Path]:
    return sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "scripts").rglob("*.py")])


def test_module_level_variables_are_annotated():
    unannotated = [
        f"{path.relative_to(ROOT)}:{node.lineno}"
        for path in checked_files()
        for node in ast.parse(path.read_text(encoding="utf-8")).body
        if isinstance(node, ast.Assign | ast.AugAssign)
    ]
    assert unannotated == []
