"""Tests for the shared artifact contract."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from bowaka_lab.utils.artifacts import (
    ArtifactPaths,
    artifact_exists,
    load_json,
    load_parquet,
    save_json,
    save_parquet,
)


def test_artifact_paths_for_run_constructs_paths_under_run_id_dir(tmp_path: Path):
    paths = ArtifactPaths.for_run("bt_iex_default", tmp_path)
    assert paths.root == tmp_path / "bt_iex_default"
    assert paths.candidates == tmp_path / "bt_iex_default" / "candidates.parquet"
    assert paths.funnel == tmp_path / "bt_iex_default" / "funnel.json"
    assert paths.trades == tmp_path / "bt_iex_default" / "trades.parquet"
    assert paths.weekly_report_md == tmp_path / "bt_iex_default" / "weekly_report.md"


def test_artifact_paths_ensure_dir_creates_directory(tmp_path: Path):
    paths = ArtifactPaths.for_run("run1", tmp_path)
    assert not paths.root.exists()
    paths.ensure_dir()
    assert paths.root.is_dir()
    # Idempotent.
    paths.ensure_dir()
    assert paths.root.is_dir()


def test_save_load_json_roundtrip(tmp_path: Path):
    target = tmp_path / "a" / "b" / "x.json"
    data = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
    save_json(target, data)
    assert load_json(target) == data


def test_save_load_parquet_roundtrip(tmp_path: Path):
    df = pd.DataFrame({"k": ["a", "b"], "v": [1, 2]})
    target = tmp_path / "out" / "x.parquet"
    save_parquet(target, df)
    out = load_parquet(target)
    pd.testing.assert_frame_equal(out, df)


def test_save_parquet_handles_dict_columns(tmp_path: Path):
    df = pd.DataFrame({"k": ["a"], "diagnostics": [{}]})
    target = tmp_path / "x.parquet"
    save_parquet(target, df)
    out = load_parquet(target)
    assert out.iloc[0]["diagnostics"] == "{}"


def test_artifact_exists_returns_true_when_file_present(tmp_path: Path):
    paths = ArtifactPaths.for_run("run1", tmp_path)
    save_json(paths.config, {"x": 1})
    assert artifact_exists(paths, "config") is True


def test_artifact_exists_returns_false_when_file_missing(tmp_path: Path):
    paths = ArtifactPaths.for_run("run1", tmp_path)
    assert artifact_exists(paths, "config") is False


def test_artifact_exists_returns_false_for_unknown_name(tmp_path: Path):
    paths = ArtifactPaths.for_run("run1", tmp_path)
    assert artifact_exists(paths, "no_such_artifact") is False


def test_re_exports_available_from_utils_package():
    from bowaka_lab.utils import (
        ArtifactPaths as AP,
        artifact_exists as ae,
        load_json as lj,
        load_parquet as lp,
        save_json as sj,
        save_parquet as sp,
    )

    assert AP is ArtifactPaths
    assert ae is artifact_exists
    assert (lj, lp, sj, sp) == (load_json, load_parquet, save_json, save_parquet)
