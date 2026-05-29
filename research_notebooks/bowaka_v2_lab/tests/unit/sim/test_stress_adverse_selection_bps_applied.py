"""Phase 2 (audit 2026-05-29 §8.5) — adverse-selection slippage penalty."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.sim.fills import simulate_marketable_limit_fill
from bowaka_v2_lab.sim.quote_model import SOURCE_HISTORICAL, QuoteSnapshot

_SCAN = pd.Timestamp("2024-08-01 14:30", tz="UTC")


def _quote() -> QuoteSnapshot:
    return QuoteSnapshot(
        bid=99.95, ask=100.0, mid=100.0, spread_pct=0.0005,
        quote_timestamp=_SCAN.isoformat(), quote_age_seconds=1.0,
        source=SOURCE_HISTORICAL, bid_size=10_000.0, ask_size=10_000.0,
    )


def _bars(close: float) -> pd.DataFrame:
    return pd.DataFrame([{
        "symbol": "AAA", "timestamp": _SCAN,
        "open": 100.0, "high": 100.2, "low": 98.0, "close": close, "volume": 1_000.0,
    }])


def test_buy_adverse_close_one_atr_adds_25_bps() -> None:
    # Fill at ask=100; bar close 99.0 -> 1.0 ATR adverse (entry_atr=1.0) -> 25 bps.
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=_quote(),
        minute_bars=_bars(99.0), scan_ts=_SCAN, cost_stress="base",
        adverse_selection_active=True, entry_atr=1.0,
    )
    assert fill.filled
    assert fill.adverse_selection_bps_added == 25.0


def test_no_adverse_when_close_does_not_move_against() -> None:
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=_quote(),
        minute_bars=_bars(100.1), scan_ts=_SCAN, cost_stress="base",
        adverse_selection_active=True, entry_atr=1.0,
    )
    assert fill.filled
    assert fill.adverse_selection_bps_added == 0.0
