"""v2 task config parses; every CONFIG_PATH exists; every notebook path exists."""
from __future__ import annotations

from pathlib import Path

import yaml


def _iter_config_paths(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "CONFIG_PATH" and isinstance(v, str):
                yield v
            else:
                yield from _iter_config_paths(v)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_config_paths(item)


def _iter_notebook_paths(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "notebooks" and isinstance(v, list):
                for nb in v:
                    p = nb.get("path") if isinstance(nb, dict) else None
                    if p:
                        yield p
            else:
                yield from _iter_notebook_paths(v)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_notebook_paths(item)


def test_v2_lab_task_config_paths_exist(repo_root: Path) -> None:
    cfg_path = repo_root / "config" / "bowaka_v2_lab_tasks.yml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_paths = list(_iter_config_paths(data))
    assert cfg_paths
    missing = [p for p in cfg_paths if not (repo_root / p).exists()]
    assert not missing, f"CONFIG_PATH entries do not exist: {missing}"


def test_v2_lab_notebook_paths_exist(repo_root: Path) -> None:
    cfg_path = repo_root / "config" / "bowaka_v2_lab_tasks.yml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    nb_paths = list(_iter_notebook_paths(data))
    assert nb_paths
    research_root = repo_root / "research_notebooks"
    missing = [p for p in nb_paths if not (research_root / p).exists()]
    assert not missing, f"notebook paths do not exist under research_notebooks/: {missing}"


def test_v2_smoke_task_config_paths_exist(repo_root: Path) -> None:
    cfg_path = repo_root / "config" / "bowaka_v2_smoke_tasks.yml"
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_paths = list(_iter_config_paths(data))
    assert cfg_paths
    missing = [p for p in cfg_paths if not (repo_root / p).exists()]
    assert not missing, f"CONFIG_PATH entries do not exist: {missing}"
    nb_paths = list(_iter_notebook_paths(data))
    research_root = repo_root / "research_notebooks"
    missing_nb = [p for p in nb_paths if not (research_root / p).exists()]
    assert not missing_nb, f"smoke notebook paths missing: {missing_nb}"
