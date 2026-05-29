"""Phase 1 (audit 2026-05-29 §8.5) — ADV-bucket partial-fill cap.

A micro-ADV name under ``conservative`` stress caps the fill at the bucket's
0.25 fraction of the liquidity proxy.
"""
from __future__ import annotations

from bowaka_v2_lab.sim.adv_buckets import bucket_for_adv, fill_cap_for
from bowaka_v2_lab.sim.fills import simulate_market_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        bid=9.95, ask=10.05, mid=10.0, spread_pct=0.01,
        quote_timestamp="2024-08-01T14:30:00+00:00", quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def test_micro_bucket_conservative_cap_partial_fill() -> None:
    adv_micro = 5.0e5  # in [2.5e5, 1.0e6) -> micro bucket
    assert bucket_for_adv(adv_micro).name == "micro"
    assert fill_cap_for(adv_micro, "conservative") == 0.25

    fill = simulate_market_fill(
        side="buy", requested_qty=1000, quote=_quote(),
        liquidity_proxy_shares=1000.0, cost_stress="conservative",
        min_order_notional=0.0, adv_dollar=adv_micro,
    )
    assert fill.filled
    assert fill.filled_qty == 250  # int(1000 * 0.25)
    assert fill.is_partial
