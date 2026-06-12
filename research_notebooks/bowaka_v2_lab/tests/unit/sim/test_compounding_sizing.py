"""Live ``sizing.compounding`` overlay — pure-math sizing tests.

Replicates prod's compounding (bowaka_v2_strategy._sizing_bankroll / _below_floor):
the equal-slice bankroll grows with lifetime GROSS realized PnL, clamped to
``[0, cap_multiple*base]``; below ``floor_fraction*base`` effective equity all new
entries halt. Default-off reproduces the legacy fixed-bankroll sizing exactly.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.sim.strategy_consumer import compute_target_notional, resolve_compounding

# Prod winner-#3155 sizing values.
_BASE = 90_000.0
_SIZING = {
    "sizing_mode": "equal_slice",
    "bankroll_fixed_dollars": _BASE,
    "max_concurrent_positions": 1,
    "equal_slice_bankroll_fraction": 0.7016473758770456,
    "min_order_notional": 500.0,
    "compounding": {"enabled": True, "base_dollars": None, "floor_fraction": 0.50, "cap_multiple": 4.0},
}


def _legacy(sizing):
    return {k: v for k, v in sizing.items() if k != "compounding"}


def test_disabled_is_legacy_none():
    bankroll, halt = resolve_compounding(_legacy(_SIZING), gross_realized=12345.0)
    assert bankroll is None and halt is False
    # compute_target_notional with None == the static fixed-bankroll slice.
    legacy_target = compute_target_notional(_legacy(_SIZING))
    assert legacy_target == pytest.approx(0.7016473758770456 * _BASE / 1)


def test_compounding_grows_with_realized_pnl():
    # +$10k realized -> effective 100k -> bankroll 100k (below cap 360k).
    bankroll, halt = resolve_compounding(_SIZING, gross_realized=10_000.0)
    assert bankroll == pytest.approx(100_000.0)
    assert halt is False
    target = compute_target_notional(_SIZING, compounding_bankroll=bankroll)
    assert target == pytest.approx(0.7016473758770456 * 100_000.0)


def test_zero_pnl_equals_base():
    bankroll, halt = resolve_compounding(_SIZING, gross_realized=0.0)
    assert bankroll == pytest.approx(_BASE)   # base + 0, below cap
    assert halt is False


def test_cap_clamps_bankroll():
    # +$300k -> effective 390k -> clamped to 4*base = 360k.
    bankroll, _ = resolve_compounding(_SIZING, gross_realized=300_000.0)
    assert bankroll == pytest.approx(360_000.0)


def test_floor_halt_at_and_below_threshold():
    # floor = 0.50 * 90k = 45k effective equity.
    # gross -45_000 -> effective exactly 45_000 -> halt (<=).
    _, halt_at = resolve_compounding(_SIZING, gross_realized=-45_000.0)
    assert halt_at is True
    # gross -45_001 -> effective 44_999 -> halt.
    _, halt_below = resolve_compounding(_SIZING, gross_realized=-45_001.0)
    assert halt_below is True
    # gross -44_999 -> effective 45_001 -> NO halt.
    _, halt_above = resolve_compounding(_SIZING, gross_realized=-44_999.0)
    assert halt_above is False


def test_base_dollars_override():
    sizing = dict(_SIZING, compounding={"enabled": True, "base_dollars": 50_000.0,
                                        "floor_fraction": 0.50, "cap_multiple": 4.0})
    # base=50k; +$5k -> effective 55k (below cap 200k).
    bankroll, halt = resolve_compounding(sizing, gross_realized=5_000.0)
    assert bankroll == pytest.approx(55_000.0)
    assert halt is False
    # floor = 25k; gross -25k -> effective 25k -> halt.
    _, halt2 = resolve_compounding(sizing, gross_realized=-25_000.0)
    assert halt2 is True


def test_effective_equity_clamped_at_zero():
    # Catastrophic drawdown below -base: effective < 0 -> bankroll floored at 0
    # (the floor-halt would already have blocked entries long before).
    bankroll, halt = resolve_compounding(_SIZING, gross_realized=-200_000.0)
    assert bankroll == pytest.approx(0.0)
    assert halt is True
