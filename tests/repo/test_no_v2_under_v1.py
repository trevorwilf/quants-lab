"""Hard guarantee: no v2 path components leak into v1.

Catches accidental copy-paste artifacts during the v1→common→v2 refactor.
"""
from __future__ import annotations

from pathlib import Path


def test_no_v2_path_components_under_v1(repo_root: Path) -> None:
    v1_root = repo_root / "research_notebooks" / "bowaka_lab"
    if not v1_root.exists():
        return
    offenders = [
        p for p in v1_root.rglob("*bowaka_v2*") if p.is_file() or p.is_dir()
    ]
    # Exclude .pytest_cache / .ruff_cache / __pycache__ noise, plus the read-only
    # ``reference/`` mirror which legitimately contains v2 documentation snapshots.
    excluded = {".pytest_cache", ".ruff_cache", "__pycache__", "reference"}
    offenders = [
        p for p in offenders
        if not any(part in excluded for part in p.relative_to(v1_root).parts)
    ]
    assert not offenders, f"v1 directory contains v2 path components: {offenders}"
