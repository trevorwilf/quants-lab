"""resolve_market_data_root precedence: explicit > env > in-repo default."""
from __future__ import annotations

from pathlib import Path

from bowaka_common.marketdata.store import (
    default_market_data_root,
    resolve_market_data_root,
)


def test_explicit_arg_wins(tmp_path):
    assert resolve_market_data_root(tmp_path, create=False) == tmp_path


def test_env_var_used_when_no_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("MARKET_DATA_ROOT", str(tmp_path))
    assert resolve_market_data_root(create=False) == tmp_path


def test_explicit_beats_env(tmp_path, monkeypatch):
    other = tmp_path / "env_lake"
    monkeypatch.setenv("MARKET_DATA_ROOT", str(other))
    explicit = tmp_path / "explicit_lake"
    assert resolve_market_data_root(explicit, create=False) == explicit


def test_default_is_in_repo_market_data(monkeypatch):
    monkeypatch.delenv("MARKET_DATA_ROOT", raising=False)
    root = resolve_market_data_root(create=False)
    assert root.name == "market_data"
    assert root.parent.name == "research_notebooks"
    assert root == default_market_data_root()


def test_blank_env_falls_through_to_default(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_ROOT", "   ")
    root = resolve_market_data_root(create=False)
    assert root.name == "market_data"


def test_create_makes_the_directory(tmp_path):
    target = tmp_path / "fresh" / "lake"
    assert not target.exists()
    resolved = resolve_market_data_root(target, create=True)
    assert resolved.is_dir()
