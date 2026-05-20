"""Pydantic validation for BowakaV2Config."""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.models import BowakaV2Config


def test_iex_smoke_validates(lab_root: Path) -> None:
    cfg = load_config(lab_root / "configs" / "bowaka_v2_backtest_smoke.yml")
    validated = BowakaV2Config.model_validate(cfg)
    assert validated.strategy_id == "bowaka_v2"
    assert validated.market_data.feed == "iex"


def test_sip_config_validates(lab_root: Path) -> None:
    cfg = load_config(lab_root / "configs" / "bowaka_v2_research_sip.yml")
    validated = BowakaV2Config.model_validate(cfg)
    assert validated.market_data.feed == "sip"
    assert validated.market_data.allow_non_sip_for_research_only is False


def test_missing_strategy_id_rejected() -> None:
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            {
                "market_data": {"feed": "iex"},
                "paths": {
                    "lab_root": "research_notebooks/bowaka_v2_lab",
                    "data_root": "research_notebooks/bowaka_v2_lab/data",
                    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
                },
            }
        )


def test_wrong_strategy_id_rejected() -> None:
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            {
                "strategy_id": "not_bowaka_v2",
                "market_data": {"feed": "iex"},
                "paths": {
                    "lab_root": "research_notebooks/bowaka_v2_lab",
                    "data_root": "research_notebooks/bowaka_v2_lab/data",
                    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
                },
            }
        )


def test_missing_feed_rejected() -> None:
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            {
                "strategy_id": "bowaka_v2",
                "market_data": {},
                "paths": {
                    "lab_root": "research_notebooks/bowaka_v2_lab",
                    "data_root": "research_notebooks/bowaka_v2_lab/data",
                    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
                },
            }
        )


def test_invalid_feed_value_rejected() -> None:
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            {
                "strategy_id": "bowaka_v2",
                "market_data": {"feed": "polygon"},
                "paths": {
                    "lab_root": "research_notebooks/bowaka_v2_lab",
                    "data_root": "research_notebooks/bowaka_v2_lab/data",
                    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
                },
            }
        )


def test_extra_top_level_key_rejected_by_model() -> None:
    with pytest.raises(ValidationError):
        BowakaV2Config.model_validate(
            {
                "strategy_id": "bowaka_v2",
                "market_data": {"feed": "iex"},
                "paths": {
                    "lab_root": "research_notebooks/bowaka_v2_lab",
                    "data_root": "research_notebooks/bowaka_v2_lab/data",
                    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
                },
                "weird_section": {"x": 1},
            }
        )
