"""code_manifest builder: git sha captured (if present), source hash deterministic."""
from __future__ import annotations

from pathlib import Path

from bowaka_common.artifacts.code_manifest import build_code_manifest, code_manifest_hash


def test_build_with_repo_root(repo_root: Path) -> None:
    src_dir = repo_root / "research_notebooks" / "bowaka_common" / "src"
    m = build_code_manifest(repo_root=repo_root, source_paths=[src_dir])
    assert m["schema_version"] == 1
    assert m["source_tree_hash"]
    assert m["source_paths"]


def test_source_tree_hash_deterministic(repo_root: Path) -> None:
    src_dir = repo_root / "research_notebooks" / "bowaka_common" / "src"
    m1 = build_code_manifest(repo_root=repo_root, source_paths=[src_dir])
    m2 = build_code_manifest(repo_root=repo_root, source_paths=[src_dir])
    assert m1["source_tree_hash"] == m2["source_tree_hash"]


def test_code_manifest_hash_stable(repo_root: Path) -> None:
    src_dir = repo_root / "research_notebooks" / "bowaka_common" / "src"
    m = build_code_manifest(repo_root=repo_root, source_paths=[src_dir])
    h1 = code_manifest_hash(m)
    h2 = code_manifest_hash(m)
    assert h1 == h2


def test_git_sha_present_if_git_available(repo_root: Path) -> None:
    m = build_code_manifest(repo_root=repo_root, source_paths=[repo_root])
    # In CI without git, git_sha may be None — both states are acceptable; the test
    # asserts the field is present.
    assert "git_sha" in m
