"""Phase 5: counterfactual grid generation."""

from __future__ import annotations

from bowaka_lab.config.models import CounterfactualConfig
from bowaka_lab.sim.counterfactuals import build_variant_grid


def test_full_cartesian_product_size():
    cfg = CounterfactualConfig(
        entry_rules=["fixed_time_0935", "fixed_time_0945"],
        stop_pct=[0.05, 0.08],
        target_pct=[0.10, 0.15],
        max_hold_days=[2, 3],
        signal_fade_thresholds=[None, 7, 9],
        stop_manager_models=["none", "breakeven_after_5pct"],
    )
    variants = build_variant_grid(cfg)
    # 2 × 2 × 2 × 2 × 3 × 2 = 96
    assert len(variants) == 96


def test_none_signal_fade_preserved_as_None():
    cfg = CounterfactualConfig(
        entry_rules=["fixed_time_0945"],
        stop_pct=[0.08],
        target_pct=[0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None, 7],
        stop_manager_models=["none"],
    )
    variants = build_variant_grid(cfg)
    fades = {v.signal_fade_threshold for v in variants}
    assert None in fades
    assert 7 in fades


def test_variant_hashable_in_dict_id():
    cfg = CounterfactualConfig(
        entry_rules=["fixed_time_0945"],
        stop_pct=[0.08],
        target_pct=[0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None],
        stop_manager_models=["none"],
    )
    [v] = build_variant_grid(cfg)
    d = v.as_dict()
    assert d["entry_rule"] == "fixed_time_0945"
    assert d["stop_pct"] == 0.08
