"""market_data.shared_root is config-only — it never feeds BowakaV2Paths."""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.models import MarketDataConfig
from bowaka_v2_lab.config.paths import BowakaV2Paths


def test_market_data_config_shared_root_is_optional():
    assert MarketDataConfig(feed="iex").shared_root is None
    assert MarketDataConfig(feed="iex", shared_root="/some/lake").shared_root == "/some/lake"


def test_shared_root_is_not_a_bowakav2paths_field():
    fields = set(BowakaV2Paths.__dataclass_fields__)
    assert "shared_root" not in fields
    assert "market_data" not in fields
    assert fields == {"lab_root", "data_root", "artifact_root", "config_path"}


def test_isolation_still_rejects_a_v1_path():
    bad = BowakaV2Paths(
        lab_root=Path("research_notebooks/bowaka_v2_lab"),
        data_root=Path("research_notebooks/bowaka_lab/data"),
        artifact_root=Path("research_notebooks/bowaka_v2_lab/artifacts"),
        config_path=Path(""),
    )
    with pytest.raises(ValueError):
        bad.assert_strategy_isolation()


def test_isolation_passes_for_clean_v2_paths():
    ok = BowakaV2Paths(
        lab_root=Path("research_notebooks/bowaka_v2_lab"),
        data_root=Path("research_notebooks/bowaka_v2_lab/data"),
        artifact_root=Path("research_notebooks/bowaka_v2_lab/artifacts"),
        config_path=Path(""),
    )
    ok.assert_strategy_isolation()  # must not raise
