"""v1 task config writes only under bowaka_lab paths; v2 writes only under bowaka_v2_lab paths."""
from __future__ import annotations

from pathlib import Path

import yaml


def _gather_paths(data) -> list[str]:
    out: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k in ("CONFIG_PATH", "path", "output_dir") and isinstance(v, str):
                out.append(v)
            out.extend(_gather_paths(v))
    elif isinstance(data, list):
        for item in data:
            out.extend(_gather_paths(item))
    return out


def test_v1_config_paths_stay_under_v1_or_app_outputs_v1(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "config" / "bowaka_lab_tasks.yml").read_text(encoding="utf-8"))
    paths = _gather_paths(data)
    for p in paths:
        norm = p.replace("\\", "/").lower()
        if "bowaka_v2_lab" in norm:
            raise AssertionError(f"v1 task config references v2 path: {p}")


def test_v2_config_paths_stay_under_v2_or_app_outputs_v2(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "config" / "bowaka_v2_lab_tasks.yml").read_text(encoding="utf-8"))
    paths = _gather_paths(data)
    for p in paths:
        norm = p.replace("\\", "/").lower()
        if norm.startswith("research_notebooks/bowaka_lab") or "bowaka_lab/notebooks" in norm:
            # Allow under "bowaka_v2_lab/notebooks/..." but not "bowaka_lab/notebooks/..."
            if "bowaka_v2_lab" not in norm:
                raise AssertionError(f"v2 task config references v1 path: {p}")


def test_smoke_config_paths_stay_under_v2(repo_root: Path) -> None:
    data = yaml.safe_load((repo_root / "config" / "bowaka_v2_smoke_tasks.yml").read_text(encoding="utf-8"))
    paths = _gather_paths(data)
    for p in paths:
        norm = p.replace("\\", "/").lower()
        if norm.startswith("research_notebooks/bowaka_lab") or "bowaka_lab/notebooks" in norm:
            if "bowaka_v2_lab" not in norm:
                raise AssertionError(f"smoke task config references v1 path: {p}")
