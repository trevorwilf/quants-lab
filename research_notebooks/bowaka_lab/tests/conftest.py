"""Shared pytest fixtures for bowaka_lab tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _bowaka_root_from_here() -> Path:
    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if ancestor.name == "bowaka_lab" and (ancestor / "src").is_dir():
            return ancestor
    return here.parents[1]


# Ensure the bowaka_lab project root is importable so `db_tools` (a sibling of
# `src/`, not part of the installed package) can be `import`-ed by tests.
_BOWAKA_ROOT = _bowaka_root_from_here()
if str(_BOWAKA_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOWAKA_ROOT))


def _detect_repo_root() -> Path:
    """Walk up from this file until we find both `app/` and `research_notebooks/`.

    Bowaka tests can run inside the host QuantLab repo or as a standalone checkout.
    """
    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if (ancestor / "app").is_dir() and (ancestor / "research_notebooks").is_dir():
            return ancestor
    return here.parents[2]


def _detect_bowaka_root() -> Path:
    here = Path(__file__).resolve()
    for ancestor in [here, *here.parents]:
        if ancestor.name == "bowaka_lab" and (ancestor / "src").is_dir():
            return ancestor
    return here.parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _detect_repo_root()


@pytest.fixture(scope="session")
def bowaka_root() -> Path:
    return _detect_bowaka_root()


@pytest.fixture(scope="session")
def configs_dir(bowaka_root: Path) -> Path:
    return bowaka_root / "configs"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Ensure each test starts with a known-clean Bowaka env namespace.

    We do NOT unset MONGO_URI (live_mongo tests rely on it) but we strip Alpaca
    credentials so accidentally-marked unit tests cannot make outbound calls.
    """
    for var in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        monkeypatch.delenv(var, raising=False)
    yield


def pytest_collection_modifyitems(config, items):
    """Auto-skip live_alpaca tests when creds are missing.

    Keeps `pytest -m live_alpaca --collect-only` non-empty so the CI can verify
    the tests still parse, while normal runs skip them with a clear reason.
    """
    if os.environ.get("ALPACA_API_KEY_ID") and os.environ.get("ALPACA_API_SECRET_KEY"):
        return
    skip_marker = pytest.mark.skip(reason="live_alpaca tests require ALPACA_API_KEY_ID and ALPACA_API_SECRET_KEY")
    for item in items:
        if "live_alpaca" in item.keywords:
            item.add_marker(skip_marker)
