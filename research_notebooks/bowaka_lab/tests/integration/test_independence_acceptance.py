"""Phase 10: independence acceptance test from [Report §4.2].

Temporarily move ``research_notebooks/market_lab`` to a holding location,
re-run ``import bowaka_lab`` + pytest on the bowaka_lab subset, then restore.

This is the final independence gate.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_bowaka_lab_imports_without_market_lab(repo_root: Path, bowaka_root: Path, tmp_path: Path):
    market_lab = repo_root / "research_notebooks" / "market_lab"
    if not market_lab.exists():
        pytest.skip("market_lab not present in this checkout; nothing to disable")

    holding = tmp_path / "market_lab_disabled"
    shutil.move(str(market_lab), str(holding))
    try:
        # Use a fresh Python invocation so module caches don't help.
        result = subprocess.run(
            [sys.executable, "-c", "import bowaka_lab; print(bowaka_lab.__version__)"],
            capture_output=True,
            text=True,
            cwd=str(bowaka_root),
            timeout=60,
        )
        assert result.returncode == 0, f"bowaka_lab import failed without market_lab: {result.stderr}"
        assert "0.1.0" in result.stdout
    finally:
        shutil.move(str(holding), str(market_lab))


def test_bowaka_lab_smoke_without_market_lab(repo_root: Path, bowaka_root: Path, tmp_path: Path):
    market_lab = repo_root / "research_notebooks" / "market_lab"
    if not market_lab.exists():
        pytest.skip("market_lab not present in this checkout; nothing to disable")
    holding = tmp_path / "market_lab_disabled"
    shutil.move(str(market_lab), str(holding))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bowaka_lab.cli", "smoke", "--offline-fixtures"],
            capture_output=True,
            text=True,
            cwd=str(bowaka_root),
            timeout=60,
        )
        assert result.returncode == 0
        assert "bowaka_lab_version" in result.stdout
    finally:
        shutil.move(str(holding), str(market_lab))
