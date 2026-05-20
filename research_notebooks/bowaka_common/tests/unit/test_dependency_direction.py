"""bowaka_common must not import from any strategy lab."""
from __future__ import annotations

import re
from pathlib import Path

import pytest


_FORBIDDEN = re.compile(r"^\s*(?:from|import)\s+bowaka_(?:lab|v2_lab)(?:\b|\.)", re.MULTILINE)


def test_common_src_has_no_strategy_lab_imports(repo_root: Path) -> None:
    src = repo_root / "research_notebooks" / "bowaka_common" / "src"
    hits: list[tuple[Path, int]] = []
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if _FORBIDDEN.search(text):
            for lineno, line in enumerate(text.splitlines(), 1):
                if _FORBIDDEN.match(line):
                    hits.append((path, lineno))
    assert not hits, f"bowaka_common imports from a strategy lab: {hits}"


def test_common_tests_have_no_strategy_lab_imports(repo_root: Path) -> None:
    tests = repo_root / "research_notebooks" / "bowaka_common" / "tests"
    hits: list[tuple[Path, int]] = []
    for path in tests.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if _FORBIDDEN.search(text):
            for lineno, line in enumerate(text.splitlines(), 1):
                if _FORBIDDEN.match(line):
                    hits.append((path, lineno))
    assert not hits, f"bowaka_common tests import from a strategy lab: {hits}"
