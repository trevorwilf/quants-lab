"""Audit P0-006 — T0 (no real quotes) hard-fails ``intended_realism``.

T0 means no historical quote (the synthetic-quote / zero-spread fallback). Per
the audit, ``intended_realism`` cannot rely on a synthetic book — the fill
model returns a no-fill with reason
``t0_no_quotes_disallowed_under_intended_realism``.

``current_code_parity`` still allows T0 (research-only); the suitability cap is
enforced by ``promotion/suitability.py``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import (
    ExecutionTier,
    detect_execution_tier,
    simulate_marketable_limit_fill,
)
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot


def _synthetic_quote() -> QuoteSnapshot:
    """A zero-spread synthetic quote — matches the live fallback under parity."""
    return QuoteSnapshot(
        bid=10.0, ask=10.0, mid=10.0, spread_pct=0.0,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.0,
        source="synthetic_zero_spread", bid_size=0, ask_size=0,
    )


def test_t0_detected_for_synthetic_quote() -> None:
    """Synthetic quote → T0 tier."""
    q = _synthetic_quote()
    tier = detect_execution_tier(quote=q, minute_bars=None)
    assert tier == ExecutionTier.T0_NO_QUOTES


def test_t0_hard_fails_intended_realism() -> None:
    """T0 + ``intended_realism`` → no-fill with the canonical T0 reject reason."""
    q = _synthetic_quote()
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=30,
        minute_bars=None,
        scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        cost_stress="base",
        simulation_mode="intended_realism",
    )
    assert fill.filled is False
    assert fill.reason == "t0_no_quotes_disallowed_under_intended_realism"
    assert fill.execution_tier == ExecutionTier.T0_NO_QUOTES.value


def test_t0_allowed_under_current_code_parity() -> None:
    """T0 + ``current_code_parity`` → fills (parity with the live wart)."""
    q = _synthetic_quote()
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=30,
        minute_bars=None,
        scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        liquidity_proxy_shares=10_000, cost_stress="base",
        simulation_mode="current_code_parity",
    )
    assert fill.filled is True
    assert fill.execution_tier == ExecutionTier.T0_NO_QUOTES.value
