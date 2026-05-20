"""Repo-level pytest fixtures.

Provides a ``repo_root`` fixture that walks upward from this file to locate the
repository root (identified by the presence of ``Makefile`` and
``docker-compose-db.yml``).
"""
from __future__ import annotations

from pathlib import Path

import pytest


def _find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "Makefile").is_file() and (cur / "docker-compose-db.yml").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError(f"could not locate repo root walking up from {start}")


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _find_repo_root(Path(__file__))
