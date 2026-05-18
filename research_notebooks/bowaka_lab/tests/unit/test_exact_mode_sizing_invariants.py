"""Phase fidelity-5: exact-mode sizing invariants."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.config import assert_exact_mode_invariants, load_config_file


EXACT_YAML = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "bowaka_exact_current_strategy.yml"
)


@pytest.fixture(autouse=True)
def _stub_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://stub:stub@localhost:27017/db?authSource=admin")


def test_exact_profile_passes_phase5_invariants():
    cfg = load_config_file(EXACT_YAML)
    assert cfg.portfolio.sizing_mode == "equal_slice"
    assert cfg.portfolio.bankroll_dollars == 90000
    assert cfg.portfolio.equal_slice_bankroll_fraction == 0.80
    assert_exact_mode_invariants(cfg)


def test_exact_mode_requires_equal_slice():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={
        "portfolio": cfg.portfolio.model_copy(update={"sizing_mode": "risk_per_trade"}),
    })
    with pytest.raises(ValueError, match="sizing_mode must be 'equal_slice'"):
        assert_exact_mode_invariants(bad)


def test_exact_mode_requires_bankroll_dollars():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={
        "portfolio": cfg.portfolio.model_copy(update={"bankroll_dollars": None}),
    })
    with pytest.raises(ValueError, match="bankroll_dollars must be set"):
        assert_exact_mode_invariants(bad)


def test_exact_mode_requires_explicit_fraction():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={
        "portfolio": cfg.portfolio.model_copy(update={"equal_slice_bankroll_fraction": None}),
    })
    with pytest.raises(ValueError, match="equal_slice_bankroll_fraction must be explicit"):
        assert_exact_mode_invariants(bad)
