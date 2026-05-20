"""BowakaV2Paths.assert_strategy_isolation invariants."""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths


def _paths(data: str, art: str, lab: str = "research_notebooks/bowaka_v2_lab") -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=Path(lab),
        data_root=Path(data),
        artifact_root=Path(art),
        config_path=Path("ignored.yml"),
    )


def test_default_paths_pass_isolation(tmp_path: Path) -> None:
    p = _paths(
        data="research_notebooks/bowaka_v2_lab/data",
        art="research_notebooks/bowaka_v2_lab/artifacts",
    )
    p.assert_strategy_isolation()


def test_paths_reject_v1_lab_root() -> None:
    p = _paths(
        data="research_notebooks/bowaka_lab/data",
        art="research_notebooks/bowaka_v2_lab/artifacts",
    )
    with pytest.raises(ValueError, match="bowaka_lab"):
        p.assert_strategy_isolation()


def test_paths_reject_source_archive_scripts_data() -> None:
    # Use a path that contains both 'bowaka_v2_lab' and 'scripts/data/bowaka_v2'.
    p = _paths(
        data="research_notebooks/bowaka_v2_lab/scripts/data/bowaka_v2/x",
        art="research_notebooks/bowaka_v2_lab/artifacts",
    )
    with pytest.raises(ValueError, match="scripts/data/bowaka_v2"):
        p.assert_strategy_isolation()


def test_paths_reject_missing_v2_lab_component(tmp_path: Path) -> None:
    p = _paths(
        data="/tmp/randomplace/data",
        art="/tmp/randomplace/artifacts",
        lab="/tmp/randomplace",
    )
    with pytest.raises(ValueError, match="bowaka_v2_lab"):
        p.assert_strategy_isolation()


def test_default_factory_constructs_valid_paths(repo_root: Path) -> None:
    p = BowakaV2Paths.default(repo_root)
    p.assert_strategy_isolation()
