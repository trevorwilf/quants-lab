"""Code-manifest builder.

Captures the git SHA and a deterministic hash of selected source-tree paths.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Iterable, Optional


CODE_MANIFEST_SCHEMA_VERSION = 1


def _git_sha(repo_root: Path) -> Optional[str]:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            return None
        sha = proc.stdout.strip()
        return sha or None
    except Exception:
        return None


def _git_dirty(repo_root: Path) -> Optional[bool]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            return None
        return bool(proc.stdout.strip())
    except Exception:
        return None


def _hash_tree(paths: Iterable[Path]) -> str:
    h = hashlib.sha256()
    file_list = []
    for p in paths:
        if p.is_file():
            file_list.append(p)
        elif p.is_dir():
            file_list.extend(sorted(p.rglob("*.py")))
    file_list = sorted(set(file_list))
    for f in file_list:
        h.update(str(f).encode("utf-8"))
        h.update(b"\0")
        try:
            data = f.read_bytes()
            h.update(hashlib.sha256(data).digest())
        except Exception:
            h.update(b"<unreadable>")
    return h.hexdigest()


def build_code_manifest(
    *,
    repo_root: Path,
    source_paths: Iterable[Path] | None = None,
) -> dict[str, Any]:
    """Build a code-manifest dict.

    ``source_paths`` defaults to ``[repo_root]`` if not supplied; callers should
    pass narrower lists (e.g. ``[repo_root / "research_notebooks" / "bowaka_v2_lab" / "src"]``).
    """
    if source_paths is None:
        source_paths = [repo_root]
    paths = [Path(p).resolve() for p in source_paths]
    source_tree_hash = _hash_tree(paths)
    sha = _git_sha(repo_root)
    dirty = _git_dirty(repo_root)
    return {
        "schema_version": CODE_MANIFEST_SCHEMA_VERSION,
        "git_sha": sha,
        "git_dirty": dirty,
        "source_tree_hash": source_tree_hash,
        "source_paths": [str(p) for p in paths],
    }


def code_manifest_hash(manifest: dict[str, Any]) -> str:
    """Stable short hash of the manifest itself (for use in run_manifest)."""
    import json

    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
