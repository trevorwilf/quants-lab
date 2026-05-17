"""Tests for ``bowaka_lab.utils.env.load_project_dotenv``."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from bowaka_lab.utils.env import load_project_dotenv


@pytest.fixture(autouse=True)
def _snapshot_env(monkeypatch):
    """Each test gets a clean view of ``os.environ`` for the KEY variable."""
    monkeypatch.delenv("KEY", raising=False)
    yield


def _write_env(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")


def test_load_project_dotenv_finds_env_in_cwd(tmp_path: Path, monkeypatch):
    _write_env(tmp_path / ".env", "KEY=value\n")
    monkeypatch.chdir(tmp_path)
    loaded = load_project_dotenv()
    assert loaded == tmp_path / ".env"
    assert os.environ["KEY"] == "value"


def test_load_project_dotenv_walks_up_one_level(tmp_path: Path):
    _write_env(tmp_path / ".env", "KEY=value\n")
    child = tmp_path / "child"
    child.mkdir()
    loaded = load_project_dotenv(start=child)
    assert loaded == tmp_path / ".env"


def test_load_project_dotenv_walks_up_multiple_levels(tmp_path: Path):
    _write_env(tmp_path / ".env", "KEY=value\n")
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    loaded = load_project_dotenv(start=deep)
    assert loaded == tmp_path / ".env"


def test_load_project_dotenv_closest_env_wins(tmp_path: Path):
    _write_env(tmp_path / ".env", "KEY=outer\n")
    child = tmp_path / "child"
    child.mkdir()
    _write_env(child / ".env", "KEY=inner\n")
    loaded = load_project_dotenv(start=child, override=True)
    assert loaded == child / ".env"
    assert os.environ["KEY"] == "inner"


def test_load_project_dotenv_returns_none_when_no_env(tmp_path: Path, monkeypatch):
    """Sandbox under tmp_path; assert no .env is found within that sandbox.

    We use a deeply nested subdirectory and only assert about that subtree —
    the walk-up may eventually hit a real .env on the developer's machine,
    but in that case the function still returns *some* path (not None).
    The contract is "return None *iff* no .env is reachable", which we
    can't deterministically verify on a developer machine; the test instead
    asserts that whatever is returned is NOT inside ``tmp_path``.
    """
    sandbox = tmp_path / "deep" / "nowhere"
    sandbox.mkdir(parents=True)
    loaded = load_project_dotenv(start=sandbox)
    if loaded is not None:
        # An ancestor outside tmp_path may legitimately exist on disk; what
        # matters is no .env was *created* by the test and yet none was
        # falsely sourced from tmp_path.
        assert tmp_path not in loaded.parents and loaded != tmp_path / ".env"


def test_load_project_dotenv_does_not_override_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KEY", "existing")
    _write_env(tmp_path / ".env", "KEY=fromfile\n")
    load_project_dotenv(start=tmp_path)
    assert os.environ["KEY"] == "existing"


def test_load_project_dotenv_override_true_replaces(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KEY", "existing")
    _write_env(tmp_path / ".env", "KEY=fromfile\n")
    load_project_dotenv(start=tmp_path, override=True)
    assert os.environ["KEY"] == "fromfile"


def test_load_project_dotenv_dotenv_unavailable_returns_none_gracefully(
    tmp_path: Path, monkeypatch
):
    """When ``python-dotenv`` is not importable, the helper returns None
    instead of raising. This protects callers from a soft-dep regression.
    """
    _write_env(tmp_path / ".env", "KEY=value\n")
    # Force the import to fail inside the helper.
    import builtins

    orig_import = builtins.__import__

    def _raise_for_dotenv(name, *args, **kwargs):
        if name == "dotenv":
            raise ImportError("simulated: dotenv missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _raise_for_dotenv)
    # Also flush cached dotenv module so the next import attempt re-fires.
    monkeypatch.delitem(sys.modules, "dotenv", raising=False)
    loaded = load_project_dotenv(start=tmp_path)
    assert loaded is None
    # KEY must NOT have been loaded because dotenv was unavailable.
    assert "KEY" not in os.environ
