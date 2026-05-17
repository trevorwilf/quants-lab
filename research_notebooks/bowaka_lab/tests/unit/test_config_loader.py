"""Phase 1: YAML loader + env substitution tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.config.loader import load_config_file, load_yaml, substitute_env


def test_substitute_required_var(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert substitute_env("${FOO}") == "bar"
    assert substitute_env({"k": "${FOO}/path"}) == {"k": "bar/path"}


def test_substitute_required_missing_raises(monkeypatch):
    monkeypatch.delenv("MISSING_VAR_XYZ", raising=False)
    with pytest.raises(KeyError):
        substitute_env("${MISSING_VAR_XYZ}")


def test_substitute_default_used_when_missing(monkeypatch):
    monkeypatch.delenv("UNSET_VAR_ABC", raising=False)
    assert substitute_env("${UNSET_VAR_ABC:-fallback}") == "fallback"


def test_substitute_default_overridden_when_set(monkeypatch):
    monkeypatch.setenv("SET_VAR", "winner")
    assert substitute_env("${SET_VAR:-loser}") == "winner"


def test_substitute_in_list():
    out = substitute_env(["${X:-a}", "${Y:-b}"], env={})
    assert out == ["a", "b"]


def test_substitute_in_nested_dict():
    out = substitute_env({"x": {"y": "${Z:-z}"}}, env={})
    assert out == {"x": {"y": "z"}}


def test_load_yaml_with_substitution(tmp_path, monkeypatch):
    monkeypatch.setenv("ENV_VAL", "env-resolved")
    yaml_file = tmp_path / "test.yml"
    yaml_file.write_text("key: ${ENV_VAL}\nlist: ['${MISSING:-default}']\n")
    out = load_yaml(yaml_file)
    assert out == {"key": "env-resolved", "list": ["default"]}


def test_load_config_file_uses_defaults(tmp_path):
    yaml = """
project:
  name: bowaka_lab
  run_label: test
data:
  vendor: alpaca
  feed: iex
  start_date: "2026-01-01"
  end_date: "2026-05-15"
"""
    config_file = tmp_path / "cfg.yml"
    config_file.write_text(yaml)
    cfg = load_config_file(config_file)
    assert cfg.project.name == "bowaka_lab"
    assert cfg.data.vendor == "alpaca"
    assert cfg.data.feed == "iex"
    # Defaults should fill in.
    assert cfg.exits.stop_pct == 0.08


def test_load_config_unknown_top_level_key_raises(tmp_path):
    yaml = """
project:
  run_label: test
data:
  vendor: alpaca
  feed: iex
  start_date: "2026-01-01"
  end_date: "2026-05-15"
unknown_section:
  foo: bar
"""
    config_file = tmp_path / "cfg.yml"
    config_file.write_text(yaml)
    with pytest.raises(Exception):
        load_config_file(config_file)


def test_load_config_unknown_nested_key_raises(tmp_path):
    yaml = """
data:
  vendor: alpaca
  feed: iex
  start_date: "2026-01-01"
  end_date: "2026-05-15"
exits:
  stop_pct: 0.08
  bogus_field: 1
"""
    config_file = tmp_path / "cfg.yml"
    config_file.write_text(yaml)
    with pytest.raises(Exception):
        load_config_file(config_file)


def test_real_iex_exploratory_config_loads(monkeypatch, bowaka_root):
    monkeypatch.setenv("MONGO_URI", "mongodb://test:test@localhost:27017/db?authSource=admin")
    cfg = load_config_file(bowaka_root / "configs" / "bowaka_backtest_iex_exploratory.yml")
    assert cfg.project.name == "bowaka_lab"
    assert cfg.data.feed == "iex"
    assert cfg.storage.mongo_uri.startswith("mongodb://")
