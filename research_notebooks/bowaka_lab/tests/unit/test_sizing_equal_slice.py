"""Phase fidelity-5: equal_slice sizing math."""

from __future__ import annotations

import pytest

from bowaka_lab.config.models import PortfolioConfig
from bowaka_lab.sim.sizing import (
    resolve_per_trade_dollars,
    resolve_qty_risk_per_trade,
)


def test_equal_slice_explicit_fraction():
    p = PortfolioConfig(
        sizing_mode="equal_slice",
        bankroll_dollars=90_000,
        equal_slice_bankroll_fraction=0.80,
        max_concurrent_positions=18,
    )
    assert resolve_per_trade_dollars(p) == pytest.approx(4_000.0)


def test_equal_slice_auto_couples_to_max_gross_exposure_pct():
    p = PortfolioConfig(
        sizing_mode="equal_slice",
        bankroll_dollars=90_000,
        equal_slice_bankroll_fraction=None,
        max_concurrent_positions=18,
        max_gross_exposure_pct=0.80,
    )
    # fraction defaults to min(1.0, mge) = 0.80
    assert resolve_per_trade_dollars(p) == pytest.approx(4_000.0)


def test_equal_slice_falls_back_to_per_trade_notional_when_no_bankroll():
    """Back-compat: pre-Phase-5 configs without bankroll keep working."""
    p = PortfolioConfig(
        sizing_mode="equal_slice",
        per_trade_notional=5_000,
        bankroll_dollars=None,
        max_concurrent_positions=18,
    )
    assert resolve_per_trade_dollars(p) == 5_000.0


def test_equal_slice_rejects_bad_fraction():
    p = PortfolioConfig(
        sizing_mode="equal_slice",
        bankroll_dollars=90_000,
        equal_slice_bankroll_fraction=1.5,
        max_concurrent_positions=18,
    )
    with pytest.raises(ValueError, match="must be in"):
        resolve_per_trade_dollars(p)


def test_risk_per_trade_qty_math():
    qty = resolve_qty_risk_per_trade(
        target_risk_dollars=200.0,
        close=10.0,
        stop_pct=0.08,
        expected_stop_slippage_pct=0.015,
    )
    # floor(200 / (10 * 0.095)) = floor(210.526) = 210
    assert qty == 210


def test_risk_per_trade_zero_close_returns_zero():
    qty = resolve_qty_risk_per_trade(
        target_risk_dollars=200.0, close=0.0, stop_pct=0.08,
        expected_stop_slippage_pct=0.015,
    )
    assert qty == 0


def test_legacy_fixed_notional_back_compat():
    p = PortfolioConfig(
        sizing_mode="legacy_fixed_notional",
        per_trade_notional=2_500,
        max_concurrent_positions=18,
    )
    assert resolve_per_trade_dollars(p) == 2_500.0


def test_legacy_fixed_notional_requires_notional():
    p = PortfolioConfig(
        sizing_mode="legacy_fixed_notional",
        per_trade_notional=None,
    )
    with pytest.raises(ValueError, match="per_trade_notional"):
        resolve_per_trade_dollars(p)


def test_resolve_per_trade_dollars_rejects_risk_per_trade_mode():
    p = PortfolioConfig(sizing_mode="risk_per_trade")
    with pytest.raises(NotImplementedError):
        resolve_per_trade_dollars(p)
