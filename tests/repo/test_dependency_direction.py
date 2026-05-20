"""Repo-level dependency-direction invariant.

bowaka_common src/ must not reference bowaka_lab or bowaka_v2_lab.
bowaka_v2_lab src/ must not reference bowaka_lab.
"""
from __future__ import annotations

import re
from pathlib import Path

_FROM_BOWAKA_LAB = re.compile(r"^\s*(?:from|import)\s+bowaka_lab(?:\b|\.)", re.MULTILINE)
_FROM_BOWAKA_V2 = re.compile(r"^\s*(?:from|import)\s+bowaka_v2_lab(?:\b|\.)", re.MULTILINE)


def _scan(root: Path, pattern: re.Pattern) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    if not root.exists():
        return hits
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not pattern.search(text):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.match(line):
                hits.append((path, lineno, line.strip()))
    return hits


def test_bowaka_common_src_does_not_import_v1(repo_root: Path) -> None:
    common_src = repo_root / "research_notebooks" / "bowaka_common" / "src"
    hits = _scan(common_src, _FROM_BOWAKA_LAB)
    assert not hits, f"bowaka_common src must not import bowaka_lab; offenders: {hits}"


def test_bowaka_common_src_does_not_import_v2(repo_root: Path) -> None:
    common_src = repo_root / "research_notebooks" / "bowaka_common" / "src"
    hits = _scan(common_src, _FROM_BOWAKA_V2)
    assert not hits, f"bowaka_common src must not import bowaka_v2_lab; offenders: {hits}"


def test_bowaka_v2_lab_src_does_not_import_v1(repo_root: Path) -> None:
    v2_src = repo_root / "research_notebooks" / "bowaka_v2_lab" / "src"
    hits = _scan(v2_src, _FROM_BOWAKA_LAB)
    assert not hits, f"bowaka_v2_lab src must not import bowaka_lab; offenders: {hits}"
