"""Config loader: YAML + env expansion + unknown-key rejection."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from bowaka_v2_lab.config.loader import load_config


def test_loads_smoke_config(lab_root: Path) -> None:
    cfg = load_config(lab_root / "configs" / "bowaka_v2_backtest_smoke.yml")
    assert cfg["strategy_id"] == "bowaka_v2"
    assert cfg["market_data"]["feed"] == "iex"
    assert cfg["_source_path"].endswith("bowaka_v2_backtest_smoke.yml")


def test_env_default_used_when_var_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPTUNA_STORAGE", raising=False)
    p = tmp_path / "x.yml"
    p.write_text(
        "strategy_id: bowaka_v2\n"
        "strategy_version: '0.0.1'\n"
        "market_data:\n  feed: iex\n"
        "paths:\n"
        "  lab_root: research_notebooks/bowaka_v2_lab\n"
        "  data_root: research_notebooks/bowaka_v2_lab/data\n"
        "  artifact_root: research_notebooks/bowaka_v2_lab/artifacts\n"
        "optuna:\n  storage: ${OPTUNA_STORAGE:-sqlite:///fallback.db}\n  n_trials: 1\n",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg["optuna"]["storage"] == "sqlite:///fallback.db"


def test_env_var_used_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_TEST_DB", "postgresql://localhost/x")
    p = tmp_path / "x.yml"
    p.write_text(
        "strategy_id: bowaka_v2\n"
        "market_data:\n  feed: iex\n"
        "paths:\n"
        "  lab_root: research_notebooks/bowaka_v2_lab\n"
        "  data_root: research_notebooks/bowaka_v2_lab/data\n"
        "  artifact_root: research_notebooks/bowaka_v2_lab/artifacts\n"
        "optuna:\n  storage: ${MY_TEST_DB}\n  n_trials: 1\n",
        encoding="utf-8",
    )
    cfg = load_config(p)
    assert cfg["optuna"]["storage"] == "postgresql://localhost/x"


def test_unknown_top_level_key_rejected(tmp_path: Path) -> None:
    p = tmp_path / "x.yml"
    p.write_text(
        "strategy_id: bowaka_v2\n"
        "market_data:\n  feed: iex\n"
        "paths:\n"
        "  lab_root: research_notebooks/bowaka_v2_lab\n"
        "  data_root: research_notebooks/bowaka_v2_lab/data\n"
        "  artifact_root: research_notebooks/bowaka_v2_lab/artifacts\n"
        "weird_section: {value: 1}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown top-level keys"):
        load_config(p)
