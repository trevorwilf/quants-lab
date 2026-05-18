"""Phase fidelity-1: ``ProjectConfig.fidelity_mode`` field."""

from __future__ import annotations

import yaml

from bowaka_lab.config.models import BowakaBacktestConfig, ProjectConfig


def _minimal_data() -> dict:
    return {"data": {"start_date": "2025-01-01", "end_date": "2025-01-02"}}


def test_fidelity_mode_defaults_to_research():
    p = ProjectConfig()
    assert p.fidelity_mode == "research"


def test_fidelity_mode_round_trips_through_yaml(tmp_path):
    yaml_text = yaml.safe_dump(
        {
            **_minimal_data(),
            "project": {"name": "bowaka_lab", "fidelity_mode": "exact"},
        }
    )
    cfg = BowakaBacktestConfig.model_validate(yaml.safe_load(yaml_text))
    assert cfg.project.fidelity_mode == "exact"
    assert cfg.is_exact_mode is True


def test_research_mode_is_exact_mode_false():
    cfg = BowakaBacktestConfig.model_validate(_minimal_data())
    assert cfg.project.fidelity_mode == "research"
    assert cfg.is_exact_mode is False


def test_invalid_fidelity_mode_rejected():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BowakaBacktestConfig.model_validate(
            {
                **_minimal_data(),
                "project": {"name": "bowaka_lab", "fidelity_mode": "live"},
            }
        )
