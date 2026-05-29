"""Phase 2 (audit 2026-05-29 §8.5) — no-fill when the bar range is too tight."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot

_SCAN = pd.Timestamp("2024-08-01 14:30", tz="UTC")


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        bid=99.9, ask=100.1, mid=100.0, spread_pct=0.002,
        quote_timestamp=_SCAN.isoformat(), quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def _tight_bars() -> pd.DataFrame:
    # range 0.0 -> below the conservative threshold (0.75 * 0.005 * 100 = 0.375)
    return pd.DataFrame([{
        "symbol": "AAA", "timestamp": _SCAN,
        "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1_000.0,
    }])


def test_tight_bar_blocks_fill_under_conservative() -> None:
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=_quote(),
        minute_bars=_tight_bars(), scan_ts=_SCAN, cost_stress="conservative",
        no_fill_bar_range_active=True,
    )
    assert not fill.filled
    assert fill.reason == "STRESS_BAR_RANGE_TOO_TIGHT"


def test_base_never_blocks_on_bar_range() -> None:
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=_quote(),
        minute_bars=_tight_bars(), scan_ts=_SCAN, cost_stress="base",
        no_fill_bar_range_active=True,
    )
    assert fill.filled  # base ratio is 0.0 -> no block
