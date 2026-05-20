"""Ensure every CONFIG_PATH referenced by ``config/bowaka_lab_tasks.yml`` exists on disk.

Catches stale-path bugs like the one fixed in Phase 0 (six references to a non-existent
``bowaka_backtest_iex_exploratory.yml`` that should be ``bowaka_research_variant.yml``).
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _iter_config_paths(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "CONFIG_PATH" and isinstance(value, str):
                yield value
            else:
                yield from _iter_config_paths(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_config_paths(item)


def test_v1_task_config_parses_and_paths_exist(repo_root: Path) -> None:
    cfg_path = repo_root / "config" / "bowaka_lab_tasks.yml"
    assert cfg_path.is_file(), f"missing {cfg_path}"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    paths = list(_iter_config_paths(data))
    assert paths, "no CONFIG_PATH entries found in v1 task config"
    missing = [p for p in paths if not (repo_root / p).exists()]
    assert not missing, f"CONFIG_PATH entries do not exist: {missing}"


def test_v1_notebooks_exist(repo_root: Path) -> None:
    cfg_path = repo_root / "config" / "bowaka_lab_tasks.yml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    nb_paths: list[str] = []
    for task in data.get("tasks", {}).values():
        for nb in task.get("config", {}).get("notebooks", []):
            p = nb.get("path")
            if p:
                nb_paths.append(p)
    assert nb_paths, "no notebooks found in v1 task config"
    # The 'path' values are relative to the research_notebooks root.
    research_root = repo_root / "research_notebooks"
    missing = [p for p in nb_paths if not (research_root / p).exists()]
    assert not missing, f"notebook paths do not exist under research_notebooks/: {missing}"
