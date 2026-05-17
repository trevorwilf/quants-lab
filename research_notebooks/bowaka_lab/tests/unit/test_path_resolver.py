"""Phase 1: PathResolver tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.utils.io import PathResolver


def _make_standalone_bowaka(tmp_path: Path) -> Path:
    root = tmp_path / "bowaka_lab"
    (root / "src").mkdir(parents=True)
    return root


def _make_quantlab_host(tmp_path: Path) -> Path:
    repo = tmp_path / "quants-lab"
    (repo / "app" / "data").mkdir(parents=True)
    (repo / "app" / "outputs").mkdir(parents=True)
    (repo / "research_notebooks" / "bowaka_lab" / "src").mkdir(parents=True)
    return repo / "research_notebooks" / "bowaka_lab"


def test_standalone_detection(tmp_path):
    bowaka = _make_standalone_bowaka(tmp_path)
    pr = PathResolver(bowaka_root=bowaka, env={})
    res = pr.resolve()
    assert res.is_quantlab_host is False
    assert res.data_root == bowaka / "data"
    assert res.output_root == bowaka / "artifacts"


def test_quantlab_host_detection(tmp_path):
    bowaka = _make_quantlab_host(tmp_path)
    pr = PathResolver(bowaka_root=bowaka, env={})
    res = pr.resolve()
    assert res.is_quantlab_host is True
    assert res.data_root == bowaka.parent.parent / "app" / "data" / "bowaka_lab"
    assert res.output_root == bowaka.parent.parent / "app" / "outputs" / "bowaka_lab"


def test_env_vars_override(tmp_path):
    bowaka = _make_quantlab_host(tmp_path)
    override_data = tmp_path / "custom_data"
    override_out = tmp_path / "custom_out"
    pr = PathResolver(
        bowaka_root=bowaka,
        env={"BOWAKA_DATA_ROOT": str(override_data), "BOWAKA_OUTPUT_ROOT": str(override_out)},
    )
    res = pr.resolve()
    assert res.data_root == override_data
    assert res.output_root == override_out


def test_explicit_args_override_env(tmp_path):
    bowaka = _make_standalone_bowaka(tmp_path)
    explicit = tmp_path / "explicit"
    pr = PathResolver(
        bowaka_root=bowaka,
        data_root=explicit,
        env={"BOWAKA_DATA_ROOT": str(tmp_path / "env_root")},
    )
    res = pr.resolve()
    assert res.data_root == explicit


def test_ensure_dirs_creates(tmp_path):
    bowaka = _make_standalone_bowaka(tmp_path)
    pr = PathResolver(bowaka_root=bowaka, env={})
    res = pr.ensure_dirs()
    assert res.data_root.is_dir()
    assert res.output_root.is_dir()
