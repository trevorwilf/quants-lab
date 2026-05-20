"""Repo-level separation invariants between v1 / v2 / common.

Per Report §5.2:
1. No file under ``research_notebooks/bowaka_v2_lab/`` imports from ``bowaka_lab``.
2. No file under ``research_notebooks/bowaka_lab/`` imports from ``bowaka_v2_lab``.
3. No file under ``research_notebooks/bowaka_common/src/`` imports from either strategy lab.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_IMPORT_PATTERNS = {
    "bowaka_lab": re.compile(r"^\s*(?:from|import)\s+bowaka_lab(?:\b|\.)", re.MULTILINE),
    "bowaka_v2_lab": re.compile(r"^\s*(?:from|import)\s+bowaka_v2_lab(?:\b|\.)", re.MULTILINE),
}


def _scan(root: Path, pattern: re.Pattern, *, allow_paths: tuple[str, ...] = ()) -> list[tuple[Path, int]]:
    hits: list[tuple[Path, int]] = []
    if not root.exists():
        return hits
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not pattern.search(text):
            continue
        # Suppress paths the test deliberately allows (e.g. dev re-export shims tested elsewhere).
        if any(str(path).replace("\\", "/").endswith(suffix) for suffix in allow_paths):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.match(line):
                hits.append((path, lineno))
    return hits


def test_v2_lab_does_not_import_v1(repo_root: Path) -> None:
    v2_root = repo_root / "research_notebooks" / "bowaka_v2_lab"
    hits = _scan(v2_root, _IMPORT_PATTERNS["bowaka_lab"])
    assert not hits, f"bowaka_v2_lab must not import from bowaka_lab; offenders: {hits}"


def test_v1_lab_does_not_import_v2(repo_root: Path) -> None:
    v1_root = repo_root / "research_notebooks" / "bowaka_lab"
    hits = _scan(v1_root, _IMPORT_PATTERNS["bowaka_v2_lab"])
    assert not hits, f"bowaka_lab must not import from bowaka_v2_lab; offenders: {hits}"


def test_common_does_not_import_either_strategy_lab(repo_root: Path) -> None:
    common_root = repo_root / "research_notebooks" / "bowaka_common" / "src"
    hits: list[tuple[Path, int]] = []
    hits.extend(_scan(common_root, _IMPORT_PATTERNS["bowaka_lab"]))
    hits.extend(_scan(common_root, _IMPORT_PATTERNS["bowaka_v2_lab"]))
    assert not hits, f"bowaka_common must not import from any strategy lab; offenders: {hits}"
