"""§10i Path 4 — fast_realism golden: honest (participation-capped) fills on a
synthetic quote, the non-blocking mode policies, and CCP/IR fill behavior unchanged.

fast_realism = intended_realism's semantics + the T3 depth/impact fill, but
NON-blocking (synthetic zero-spread quote fallback, no fail-closed coverage/quote
gates). On a synthetic quote (ask_size=0) the T3 fill degrades to a minute-volume
participation cap — honest SIZE without a real quote.
"""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.config.models import SimulationConfig
from bowaka_v2_lab.data.data_quality import evaluate_startup_dq
from bowaka_v2_lab.sim.fills import ExecutionTier, detect_execution_tier, simulate_market_fill
from bowaka_v2_lab.sim.quote_model import synthesize_zero_spread_quote, QuoteSnapshot, SOURCE_HISTORICAL

_TS = pd.Timestamp("2025-11-03T14:32:00Z")


def _minute_bars(volume: float) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp": [_TS], "open": [10.0], "high": [10.1], "low": [9.9],
        "close": [10.0], "volume": [volume],
    })


def _fill(*, has_nbbo_depth: bool, quote, volume: float, qty: float = 577.0):
    return simulate_market_fill(
        side="buy", requested_qty=qty, quote=quote, minute_bars=_minute_bars(volume),
        scan_ts=_TS, has_nbbo_depth=has_nbbo_depth, participation_cap=0.10,
        market_impact_coef_bps=10.0, adv_dollar=5_000_000.0,
    )


def test_fast_realism_mode_resolves_nonblocking_policies():
    s = SimulationConfig.model_validate({"mode": "fast_realism"})
    # IR semantics for the signal/event window (search must agree with the IR gate)...
    assert s.intraday_window_policy == "regular_open_to_scan"
    assert s.accepted_event_sequencing == "post_submit"
    # ...but NON-blocking on the gates that key on require_real / fail_closed.
    assert s.quote_fallback_policy == "zero_spread"
    assert s.unknown_instrument_class_policy == "fail_open"


def test_synthetic_quote_routes_to_t3_only_under_fast_realism():
    q = synthesize_zero_spread_quote(signal_price=10.0, at=_TS)
    assert q.ask_size == 0.0 and not q.is_historical
    # has_nbbo_depth (fast_realism) wins over the synthetic->T0 fallback.
    assert detect_execution_tier(quote=q, minute_bars=_minute_bars(800), has_nbbo_depth=True) \
        == ExecutionTier.T3_NBBO_DEPTH
    # CCP (has_nbbo_depth=False) keeps the legacy T0 path on a synthetic quote.
    assert detect_execution_tier(quote=q, minute_bars=_minute_bars(800), has_nbbo_depth=False) \
        == ExecutionTier.T0_NO_QUOTES


def test_fast_realism_participation_cap_partial_fill_on_synthetic_quote():
    q = synthesize_zero_spread_quote(signal_price=10.0, at=_TS)
    # 10% of an 800-share minute = 80 shares; a 577-share order partials to 80.
    fr = _fill(has_nbbo_depth=True, quote=q, volume=800.0)
    assert fr.filled_qty == pytest.approx(80.0)
    # §2.2 fix: CCP no longer manufactures liquidity. With no ADV/liquidity proxy
    # AND a synthetic quote (ask_size=0 -> no displayed depth), the legacy market
    # fill is now bounded to zero -> no fill (was a full 577-share fabrication).
    ccp = _fill(has_nbbo_depth=False, quote=q, volume=800.0)
    assert ccp.filled is False
    assert ccp.filled_qty == pytest.approx(0.0)


def test_fast_realism_no_fill_when_no_minute_volume():
    q = synthesize_zero_spread_quote(signal_price=10.0, at=_TS)
    fr = _fill(has_nbbo_depth=True, quote=q, volume=0.0)
    assert fr.filled_qty == pytest.approx(0.0)


def test_fast_realism_uses_real_touch_when_historical_quote_present():
    # A real historical quote provides a touch floor: fillable = max(touch, cap).
    q = QuoteSnapshot(
        bid=9.99, ask=10.01, mid=10.0, spread_pct=0.002,
        quote_timestamp=_TS.isoformat(), quote_age_seconds=0.0,
        source=SOURCE_HISTORICAL, bid_size=100.0, ask_size=100.0,
    )
    fr = _fill(has_nbbo_depth=True, quote=q, volume=800.0)
    # touch 100 > participation cap 80 -> fills the displayed 100.
    assert fr.filled_qty == pytest.approx(100.0)


def test_fast_realism_dq_gate_is_adjustment_only_not_coverage():
    # A coverage_missing fail aborts intended_realism but NOT fast_realism.
    report = {
        "checks": [{"name": "coverage_missing", "status": "fail", "count": 999}],
        "required_failures": ["coverage_missing"],
        "adjustment_gating_failures": [],
    }
    assert evaluate_startup_dq(report, simulation_mode="intended_realism") is not None
    assert evaluate_startup_dq(report, simulation_mode="fast_realism") is None
    assert evaluate_startup_dq(report, simulation_mode="current_code_parity") is None
    # ...but an adjustment catastrophe still fails fast_realism closed (it's a real run).
    adj = {
        "checks": [{"name": "adjustment_mismatch", "status": "fail", "count": 1}],
        "required_failures": ["adjustment_mismatch"],
        "adjustment_gating_failures": ["adjustment_mismatch"],
    }
    assert evaluate_startup_dq(adj, simulation_mode="fast_realism") is not None
