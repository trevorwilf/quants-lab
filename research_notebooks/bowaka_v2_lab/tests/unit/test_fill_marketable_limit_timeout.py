"""Phase 6 — marketable-limit order: quote chases past the limit → no position.

A marketable-limit buy order's limit is ``quote.ask * (1 + slippage_pct)``. If
the quote runs away — every forward minute bar's high is above the limit within
the timeout window — the order times out unfilled and no position is created.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot


def _quote(ask: float) -> QuoteSnapshot:
    bid = ask - 0.04
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source="historical", bid_size=10_000, ask_size=10_000,
    )


def _forward_bars(symbol: str, scan_ts, highs: list[float]) -> pd.DataFrame:
    start = pd.Timestamp(scan_ts)
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(highs),
            "timestamp": [start + pd.Timedelta(minutes=i) for i in range(len(highs))],
            "open": highs, "high": highs, "low": highs, "close": highs,
            "volume": [5000.0] * len(highs),
        }
    )


def test_marketable_limit_times_out_when_quote_chases_past_limit():
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    q = _quote(ask=100.0)  # limit = 100.0 * 1.005 = 100.50
    # Every forward bar high is above 100.50 → the quote ran away.
    bars = _forward_bars("AAA", scan_ts, [101.0, 101.5, 102.0])
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=60,
        minute_bars=bars, scan_ts=scan_ts,
        liquidity_proxy_shares=100_000, cost_stress="base",
    )
    assert fill.filled is False
    assert fill.reason == "marketable_limit_timeout"
    assert fill.filled_qty == 0


def test_marketable_limit_fills_when_quote_stays_within_limit():
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    q = _quote(ask=100.0)  # limit = 100.50
    # The first forward bar high is below the limit → the order can fill.
    bars = _forward_bars("AAA", scan_ts, [100.20, 100.30, 100.40])
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=60,
        minute_bars=bars, scan_ts=scan_ts,
        liquidity_proxy_shares=100_000, cost_stress="base",
    )
    assert fill.filled is True
    assert fill.filled_qty == 100
    # Realism remediation 2 Phase 5 (audit P0-006): T2 fills at the ask when
    # ``ask_size >= qty`` (not at the full limit price). The quote here has
    # ``ask_size=10_000 >= qty=100`` so the whole order takes at the ask.
    assert fill.avg_fill_price == 100.0
    assert fill.slippage_vs_ask_bps == 0.0
    assert fill.execution_tier in ("T1_TOP_OF_BOOK", "T2_QUOTES_AND_VOLUME")


def test_marketable_limit_fills_when_no_forward_bars_supplied():
    """With no forward-bar path the order cannot time out → it fills."""
    q = _quote(ask=50.0)
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=30,
        minute_bars=None, scan_ts=pd.Timestamp("2024-09-04 14:00:00", tz="UTC"),
        liquidity_proxy_shares=100_000, cost_stress="base",
    )
    assert fill.filled is True
