"""The market-data lake's data is gitignored; its README is not."""
from __future__ import annotations

import subprocess


def _is_ignored(repo_root, relpath: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", relpath],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    # git check-ignore: exit 0 == ignored, exit 1 == not ignored.
    return result.returncode == 0


def test_lake_data_is_gitignored(repo_root):
    assert _is_ignored(repo_root, "research_notebooks/market_data/bars/X/part.parquet")
    assert _is_ignored(repo_root, "research_notebooks/market_data/_ingestion/manifest.json")
    assert _is_ignored(repo_root, "research_notebooks/market_data/assets/Y/assets.parquet")


def test_lake_readme_is_not_ignored(repo_root):
    assert not _is_ignored(repo_root, "research_notebooks/market_data/README.md")
