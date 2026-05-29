"""Phase 1 (audit 2026-05-29 §8.5) — spread multiplier widens the half-spread.

A 2x spread doubles the half-spread paid: the marketable-limit buy fills at a
price whose distance from the mid is twice the unstressed distance.
"""
from __future__ import annotations

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot


def _quote() -> QuoteSnapshot:
    # 10 bps spread around mid=100 -> half-spread 5 bps.
    return QuoteSnapshot(
        bid=99.95, ask=100.05, mid=100.0, spread_pct=0.001,
        quote_timestamp="2024-08-01T14:30:00+00:00", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def test_spread_multiplier_doubles_half_spread_paid() -> None:
    q = _quote()
    base = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q, cost_stress="base",
        spread_multiplier=1.0,
    )
    stressed = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q, cost_stress="base",
        spread_multiplier=2.0,
    )
    assert base.filled and stressed.filled
    base_dist = base.avg_fill_price - q.mid
    stressed_dist = stressed.avg_fill_price - q.mid
    assert base_dist > 0
    assert abs(stressed_dist - 2.0 * base_dist) < 1e-6
    assert stressed.spread_multiplier == 2.0
