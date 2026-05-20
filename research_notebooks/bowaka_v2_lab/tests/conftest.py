"""Shared fixtures for bowaka_v2_lab tests."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Auto-discover repo-root .env (walks up looking for Makefile + docker-compose-db.yml).
def _find_repo_root(start: Path) -> Path | None:
    cur = start.resolve()
    for _ in range(10):
        if (cur / "Makefile").is_file() and (cur / "docker-compose-db.yml").is_file():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
    return None


_REPO_ROOT = _find_repo_root(Path(__file__))

if _REPO_ROOT is not None:
    env_path = _REPO_ROOT / ".env"
    if env_path.is_file():
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv(env_path, override=False)
        except ImportError:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    assert _REPO_ROOT is not None, "could not locate repo root from test fixtures"
    return _REPO_ROOT


@pytest.fixture(scope="session")
def lab_root(repo_root: Path) -> Path:
    return repo_root / "research_notebooks" / "bowaka_v2_lab"


@pytest.fixture
def tmp_run_dir(tmp_path: Path) -> Path:
    rd = tmp_path / "run"
    rd.mkdir(parents=True, exist_ok=True)
    return rd
