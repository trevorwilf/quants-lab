"""Phase fidelity-1: ``bowaka_research_variant.yml`` loads cleanly."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.config import load_config_file

HERE = Path(__file__).resolve().parents[2]
RESEARCH_YAML = HERE / "configs" / "bowaka_research_variant.yml"


@pytest.fixture(autouse=True)
def _stub_required_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://stub:stub@localhost:27017/quants_lab?authSource=admin")


def test_research_variant_loads():
    cfg = load_config_file(RESEARCH_YAML)
    assert cfg.project.fidelity_mode == "research"
    assert cfg.project.run_label == "bowaka_research_variant_v1"
    assert cfg.signal_fade.enabled is True
    assert cfg.portfolio.per_trade_notional == 5000
