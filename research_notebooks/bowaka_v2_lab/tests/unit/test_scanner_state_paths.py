"""Scanner state path resolves via BowakaV2Paths; rejects v1 / archive paths."""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.scanner.state import ScannerStateStore


def test_state_path_lives_under_v2_artifacts(repo_root: Path) -> None:
    paths = BowakaV2Paths.default(repo_root)
    store = ScannerStateStore(paths)
    assert "bowaka_v2_lab" in str(store.state_path).replace("\\", "/")
    assert str(store.state_path).endswith("scanner_state.json")


def test_state_store_rejects_v1_paths() -> None:
    bad = BowakaV2Paths(
        lab_root=Path("research_notebooks/bowaka_lab"),
        data_root=Path("research_notebooks/bowaka_lab/data"),
        artifact_root=Path("research_notebooks/bowaka_lab/artifacts"),
        config_path=Path("ignored.yml"),
    )
    with pytest.raises(ValueError, match="bowaka_v2_lab"):
        ScannerStateStore(bad)


def test_state_store_rejects_scripts_data_path() -> None:
    bad = BowakaV2Paths(
        lab_root=Path("research_notebooks/bowaka_v2_lab"),
        data_root=Path("research_notebooks/bowaka_v2_lab/scripts/data/bowaka_v2/x"),
        artifact_root=Path("research_notebooks/bowaka_v2_lab/artifacts"),
        config_path=Path("ignored.yml"),
    )
    with pytest.raises(ValueError, match="scripts/data/bowaka_v2"):
        ScannerStateStore(bad)


def test_state_roundtrip(tmp_path: Path) -> None:
    # Use a synthetic v2-rooted path so isolation passes.
    fake_lab = tmp_path / "research_notebooks" / "bowaka_v2_lab"
    paths = BowakaV2Paths(
        lab_root=fake_lab,
        data_root=fake_lab / "data",
        artifact_root=fake_lab / "artifacts",
        config_path=Path("ignored.yml"),
    )
    store = ScannerStateStore(paths)
    s1 = store.load_or_init("2024-09-04")
    assert s1["session_date"] == "2024-09-04"
    s1["entered_symbols_today"].append("AAA")
    store.save(s1)
    s2 = store.load_or_init("2024-09-04")
    assert s2["entered_symbols_today"] == ["AAA"]
    # Day rollover → reset.
    s3 = store.load_or_init("2024-09-05")
    assert s3["entered_symbols_today"] == []
