"""bowaka_common test fixtures."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    cur = Path(__file__).resolve()
    for _ in range(10):
        if (cur / "Makefile").is_file() and (cur / "docker-compose-db.yml").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("could not locate repo root")
