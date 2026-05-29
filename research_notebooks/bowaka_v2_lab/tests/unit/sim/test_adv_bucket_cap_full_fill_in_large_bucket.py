"""Phase 1 (audit 2026-05-29 §8.5) — large-ADV name at base stress fills fully.

The base cap is 1.0 for every bucket (the parity anchor), so a large-ADV name
under ``base`` stress fills in full.
"""
from __future__ import annotations

from bowaka_v2_lab.sim.adv_buckets import bucket_for_adv, fill_cap_for
from bowaka_v2_lab.sim.fills import simulate_market_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        bid=49.95, ask=50.05, mid=50.0, spread_pct=0.002,
        quote_timestamp="2024-08-01T14:30:00+00:00", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def test_large_bucket_base_cap_full_fill() -> None:
    adv_large = 1.0e8  # >= 5.0e7 -> large bucket
    assert bucket_for_adv(adv_large).name == "large"
    assert fill_cap_for(adv_large, "base") == 1.0

    fill = simulate_market_fill(
        side="buy", requested_qty=1000, quote=_quote(),
        liquidity_proxy_shares=1000.0, cost_stress="base",
        min_order_notional=0.0, adv_dollar=adv_large,
    )
    assert fill.filled
    assert fill.filled_qty == 1000
    assert not fill.is_partial
