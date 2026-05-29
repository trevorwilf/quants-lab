"""Phase 1 (audit 2026-05-29 §8.5) — additive slippage offset shifts the fill.

``slippage_bps_offset`` adds N bps of the mid to the fill price (worse for a
buy). It is a no-op at 0 (the unstressed path).
"""
from __future__ import annotations

from bowaka_v2_lab.sim.fills import simulate_market_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        bid=99.0, ask=101.0, mid=100.0, spread_pct=0.02,
        quote_timestamp="2024-08-01T14:30:00+00:00", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def test_slippage_offset_adds_bps_of_mid() -> None:
    q = _quote()
    base = simulate_market_fill(
        side="buy", requested_qty=100, quote=q, cost_stress="base",
        slippage_bps_offset=0,
    )
    stressed = simulate_market_fill(
        side="buy", requested_qty=100, quote=q, cost_stress="base",
        slippage_bps_offset=50,
    )
    assert base.filled and stressed.filled
    expected = round(base.avg_fill_price + 0.005 * q.mid, 4)  # 50 bps of mid
    assert stressed.avg_fill_price == expected
    assert stressed.slippage_bps_offset == 50
    assert base.slippage_bps_offset == 0
