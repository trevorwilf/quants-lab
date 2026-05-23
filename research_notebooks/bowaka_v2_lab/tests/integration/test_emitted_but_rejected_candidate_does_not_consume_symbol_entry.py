"""Realism Remediation 2 Phase 7 (audit P1-003) — an emitted candidate that
the strategy consumer then REJECTS (missing quote, spread too wide, halt gate,
etc.) must NOT consume same-symbol entry allowance on the portfolio side.

The scanner-dedup view (``signal_emits_per_symbol_today``) IS incremented on
emission — that is the scanner's own per-day cap. But the portfolio's
``entries_per_symbol_today`` (PARENT_FILL count) MUST stay zero unless an
actual fill lands. A risk gate that read the scanner counter would suppress
later valid candidates for the same symbol; reading the portfolio counter
correctly does not.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.sim.portfolio import Portfolio


_SYMBOL = "AAA"


def _cfg() -> dict[str, Any]:
    return {
        "strategy_id": "bowaka_v2",
        "scanner": {
            "max_candidates_per_scan": 10,
            "max_entries_per_scan": 10,
            "same_symbol_entries_per_day": 5,
            "symbol_cooldown_minutes": 0,
        },
        "signals": {},
        "score": {},
        "market_data": {"max_bar_age_seconds": 6_000_000},
    }


def _universe() -> dict[str, Any]:
    return {
        "universe_hash": "sha256:test_p7_rej",
        "symbols": [{
            "symbol": _SYMBOL, "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        }],
    }


def _daily_cache() -> pd.DataFrame:
    return pd.DataFrame([{
        "symbol": _SYMBOL, "prior_close": 10.0,
        "avg_dollar_volume_20d": 500_000_000,
        "prior_atr_pct": 0.02, "ema_slope_prior": 0.01,
    }])


def _emitting_bars() -> pd.DataFrame:
    base = pd.Timestamp("2024-09-04 09:30", tz="UTC")
    rows = [{
        "timestamp": base + pd.Timedelta(minutes=i),
        "open": 10.0 + 0.05 * i,
        "high": 10.10 + 0.05 * i,
        "low": 10.0 + 0.05 * i,
        "close": 10.05 + 0.05 * i,
        "volume": 100_000.0,
    } for i in range(15)]
    return pd.DataFrame(rows)


def _bars_supplier(bars: pd.DataFrame):
    def supplier(symbol: str, cutoff) -> pd.DataFrame:
        ts = pd.Timestamp(cutoff).tz_convert("UTC")
        return bars[bars["timestamp"] <= ts].copy()
    return supplier


def test_emit_without_fill_does_not_consume_portfolio_entry() -> None:
    """A bare emit (scanner accepts but no PARENT_FILL follows — simulating an
    emitted-but-rejected candidate downstream) does NOT touch the portfolio's
    per-symbol entry count."""
    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "signal_emits_per_symbol_today": {},
    }
    pf = Portfolio(initial_bankroll=100_000.0)
    sd = _dt.date(2024, 9, 4)
    pf.begin_session(sd)

    bars = _emitting_bars()
    result = evaluate_one_scan(
        cfg=_cfg(), universe_snapshot=_universe(), daily_cache=_daily_cache(),
        volume_curve=None, state=state,
        scan_ts=pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        bars_supplier=_bars_supplier(bars),
    )
    if not result.emitted:
        pytest.skip("scanner emitted no candidate for this test fixture")

    # Scanner DID emit (and incremented its emit counter).
    assert state["signal_emits_per_symbol_today"].get(_SYMBOL, 0) >= 1

    # No PARENT_FILL happened — the candidate was rejected downstream. The
    # portfolio entry counter for this symbol must stay zero.
    assert pf.state is not None
    assert pf.state.entries_per_symbol_today.get(_SYMBOL, 0) == 0, (
        "emitted-but-rejected candidate must not consume same-symbol entry "
        "allowance on the portfolio side (audit P1-003)"
    )


def test_repeated_emit_without_fill_does_not_lock_out_future_entries() -> None:
    """If the scanner emits a candidate and the strategy rejects it, a LATER
    real fill must still be allowed (because the portfolio entry count is
    still zero — only the scanner-side emit count went up)."""
    # cfg: scanner allows up to 3 emits per symbol per day; portfolio risk uses
    # its own counter so a later fill is not pre-blocked.
    cfg = _cfg()
    cfg["scanner"]["same_symbol_entries_per_day"] = 3

    state: dict[str, Any] = {
        "entered_symbols_today": [],
        "in_play_pool": {},
        "symbol_last_emit_ts": {},
        "signal_emits_per_symbol_today": {},
    }
    pf = Portfolio(initial_bankroll=100_000.0)
    pf.begin_session(_dt.date(2024, 9, 4))

    bars = _emitting_bars()
    # Two scans, two emits — but no fills.
    for scan_ts in [
        pd.Timestamp("2024-09-04 13:50:00", tz="UTC"),
        pd.Timestamp("2024-09-04 13:55:00", tz="UTC"),
    ]:
        evaluate_one_scan(
            cfg=cfg, universe_snapshot=_universe(),
            daily_cache=_daily_cache(),
            volume_curve=None, state=state,
            scan_ts=scan_ts, bars_supplier=_bars_supplier(bars),
        )

    # The scanner-side emit counter increased; the portfolio side did NOT.
    assert pf.state is not None
    assert pf.state.entries_per_symbol_today.get(_SYMBOL, 0) == 0, (
        "scanner emits must not leak into portfolio per-symbol entry count"
    )


def test_portfolio_entry_count_recomputed_on_begin_session() -> None:
    """``begin_session`` recomputes per-symbol entries from lots whose
    ``entry_session == today`` — prior-day lots do NOT count toward today.
    """
    from bowaka_v2_lab.sim.portfolio import Position

    pf = Portfolio(initial_bankroll=100_000.0)
    sd_a = _dt.date(2024, 9, 4)
    pf.begin_session(sd_a)
    pos_a = Position(
        symbol=_SYMBOL, entry_date=sd_a, entry_price=10.0, qty=100,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=sd_a, entry_timestamp=f"{sd_a}T09:35:00Z",
        stop_price=9.2, target_price=11.5, position_id="pos-prev",
    )
    pf.add_position(pos_a)
    assert pf.state is not None
    assert pf.state.entries_per_symbol_today.get(_SYMBOL) == 1

    # New session begins — the prior-day lot does NOT count toward today.
    sd_b = _dt.date(2024, 9, 5)
    pf.begin_session(sd_b)
    assert pf.state.entries_per_symbol_today == {}, (
        "begin_session must recompute per-symbol entries for THIS session"
    )
