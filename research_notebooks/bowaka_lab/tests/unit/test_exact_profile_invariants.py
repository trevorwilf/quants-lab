"""Phase fidelity-1: ``assert_exact_mode_invariants`` enforces source contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_lab.config import assert_exact_mode_invariants, load_config_file


HERE = Path(__file__).resolve().parents[2]  # research_notebooks/bowaka_lab/
EXACT_YAML = HERE / "configs" / "bowaka_exact_current_strategy.yml"
RESEARCH_YAML = HERE / "configs" / "bowaka_research_variant.yml"


@pytest.fixture(autouse=True)
def _stub_required_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://stub:stub@localhost:27017/quants_lab?authSource=admin")


def test_exact_profile_loads_and_passes_invariants():
    cfg = load_config_file(EXACT_YAML)
    assert cfg.project.fidelity_mode == "exact"
    assert cfg.is_exact_mode
    # required blocklist present
    assert {"TSLL", "CONL", "SMCX"}.issubset(set(cfg.universe.ticker_blocklist))
    # adv tiers non-empty
    assert cfg.realism.adv_tier_caps
    # signal_fade disabled
    assert not cfg.signal_fade.enabled
    # invariants must not raise
    assert_exact_mode_invariants(cfg)


def test_research_profile_short_circuits_invariants():
    cfg = load_config_file(RESEARCH_YAML)
    assert cfg.project.fidelity_mode == "research"
    # signal_fade enabled in research mode is fine — invariants ignore non-exact.
    assert_exact_mode_invariants(cfg)  # must not raise


def test_invariant_violation_missing_blocklist():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={"universe": cfg.universe.model_copy(update={"ticker_blocklist": []})})
    with pytest.raises(ValueError, match="ticker_blocklist non-empty"):
        assert_exact_mode_invariants(bad)


def test_invariant_violation_partial_blocklist():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(
        update={"universe": cfg.universe.model_copy(update={"ticker_blocklist": ["TSLL"]})}
    )
    with pytest.raises(ValueError, match="present in ticker_blocklist"):
        assert_exact_mode_invariants(bad)


def test_invariant_violation_empty_adv_tiers():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={"realism": cfg.realism.model_copy(update={"adv_tier_caps": []})})
    with pytest.raises(ValueError, match="adv_tier_caps non-empty"):
        assert_exact_mode_invariants(bad)


def test_invariant_violation_signal_fade_enabled():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(update={"signal_fade": cfg.signal_fade.model_copy(update={"enabled": True})})
    with pytest.raises(ValueError, match="signal_fade.enabled must be false"):
        assert_exact_mode_invariants(bad)


def test_invariant_violation_aggregates_all_errors():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(
        update={
            "universe": cfg.universe.model_copy(update={"ticker_blocklist": []}),
            "realism": cfg.realism.model_copy(update={"adv_tier_caps": []}),
            "signal_fade": cfg.signal_fade.model_copy(update={"enabled": True}),
        }
    )
    with pytest.raises(ValueError) as exc:
        assert_exact_mode_invariants(bad)
    msg = str(exc.value)
    assert "ticker_blocklist" in msg
    assert "adv_tier_caps" in msg
    assert "signal_fade" in msg


def test_invariant_violation_etp_etn_flags():
    cfg = load_config_file(EXACT_YAML)
    bad = cfg.model_copy(
        update={
            "universe": cfg.universe.model_copy(update={"exclude_leveraged_etp": False}),
        }
    )
    with pytest.raises(ValueError, match="exclude_leveraged_etp"):
        assert_exact_mode_invariants(bad)


def test_invariant_no_op_for_research_with_dirty_values():
    """research-mode configs are NEVER blocked by exact-mode invariants."""
    cfg = load_config_file(RESEARCH_YAML)
    bad_research = cfg.model_copy(
        update={
            "universe": cfg.universe.model_copy(update={"ticker_blocklist": [], "exclude_leveraged_etp": False}),
            "realism": cfg.realism.model_copy(update={"adv_tier_caps": []}),
            "signal_fade": cfg.signal_fade.model_copy(update={"enabled": True}),
        }
    )
    # research mode short-circuits, no raise
    assert_exact_mode_invariants(bad_research)
