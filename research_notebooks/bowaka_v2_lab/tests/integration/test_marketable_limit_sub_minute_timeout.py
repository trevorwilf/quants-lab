"""Audit P0-006 — marketable-limit timeout is honoured at SECONDS resolution.

The pre-fix code rounded ``marketable_limit_timeout_seconds`` up to whole
minutes (minimum 1 minute). A 30-second timeout effectively became 60 seconds.

The fix uses seconds-resolution windowing: a 30-second timeout examines only
the bars with ``timestamp <= submit_ts + 30s``. A bar at ``submit_ts + 45s``
with a runaway price does NOT contribute to the timeout decision.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot, SOURCE_HISTORICAL


def _quote(ask: float, ask_size: float = 50) -> QuoteSnapshot:
    bid = ask - 0.02
    mid = (bid + ask) / 2.0
    # Tiny ask_size so the order can't fill at the touch — it must walk the path.
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp="2024-09-04T14:00:00Z", quote_age_seconds=0.5,
        source=SOURCE_HISTORICAL, bid_size=ask_size, ask_size=ask_size,
    )


def test_30_second_timeout_uses_seconds_resolution() -> None:
    """A 30s timeout ignores the 60-second bar that has the runaway high.

    Scenario:
    - submit_ts = 14:00:00
    - limit = 10.05 (offset 0.005 from ask=10.00)
    - Bar at 14:00:00 high=10.02 (within limit)
    - Bar at 14:01:00 high=11.00 (runaway)
    - Timeout: 30s — only the FIRST bar (14:00:00) is in window → fill ok
    - Timeout: 60s — both bars in window → bar 2 runs past limit → no-fill
    """
    scan_ts = pd.Timestamp("2024-09-04 14:00:00", tz="UTC")
    q = _quote(ask=10.00, ask_size=500)  # ample size to fill at touch
    # Single bar at +45s with a runaway high. With a 30s timeout the bar is
    # OUTSIDE the window → no path → no timeout. With a 60s timeout the bar
    # is INSIDE the window → its high (11.0) is above the 10.05 limit so the
    # min-of-highs-above-limit check fires → timeout.
    bars = pd.DataFrame([
        {"symbol": "AAA", "timestamp": scan_ts + pd.Timedelta(seconds=45),
         "open": 10.5, "high": 11.0, "low": 10.4, "close": 10.9, "volume": 5000.0},
    ])
    # 30s timeout: bar at +45s is outside the [0s, 30s] window → fill ok.
    fill_30s = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,  # limit = 10.05
        marketable_limit_timeout_seconds=30,
        minute_bars=bars, scan_ts=scan_ts,
        cost_stress="base",
    )
    assert fill_30s.filled is True, (
        "30s timeout window excludes the +45s runaway bar — fill must succeed"
    )

    # 60s timeout: the +45s bar IS in the [0s, 60s] window. Its high (11.0)
    # runs past the 10.05 limit and is the only bar → ``min(highs) > limit``
    # fires → no-fill with ``marketable_limit_timeout``.
    fill_60s = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=q,
        marketable_limit_slippage_pct=0.005,
        marketable_limit_timeout_seconds=60,
        minute_bars=bars, scan_ts=scan_ts,
        cost_stress="base",
    )
    assert fill_60s.filled is False
    assert fill_60s.reason == "marketable_limit_timeout"
