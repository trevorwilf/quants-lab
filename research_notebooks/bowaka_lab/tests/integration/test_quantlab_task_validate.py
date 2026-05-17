"""Phase 10: `make validate-config` succeeds for bowaka_lab_tasks.yml.

If the host repo Makefile doesn't have ``validate-config``, we still verify
that the YAML parses, that ``task_class: notebook`` is set, and that all
referenced notebook paths exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def test_bowaka_lab_tasks_yaml_parses(repo_root: Path):
    path = repo_root / "config" / "bowaka_lab_tasks.yml"
    if not path.exists():
        pytest.skip("config/bowaka_lab_tasks.yml not present in this checkout")
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "tasks" in spec
    assert "bowaka_lab_research_pipeline" in spec["tasks"]
    task = spec["tasks"]["bowaka_lab_research_pipeline"]
    assert task["task_class"] == "notebook"
    cfg = task["config"]
    assert cfg["kernel"] == "python3"
    assert isinstance(cfg["notebooks"], list)
    assert cfg["notebooks"]


def test_referenced_notebooks_exist(repo_root: Path):
    path = repo_root / "config" / "bowaka_lab_tasks.yml"
    if not path.exists():
        pytest.skip("config/bowaka_lab_tasks.yml not present in this checkout")
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    notebooks = spec["tasks"]["bowaka_lab_research_pipeline"]["config"]["notebooks"]
    for entry in notebooks:
        nb_path = repo_root / "research_notebooks" / entry["path"]
        assert nb_path.exists(), f"Missing notebook referenced from config: {nb_path}"
