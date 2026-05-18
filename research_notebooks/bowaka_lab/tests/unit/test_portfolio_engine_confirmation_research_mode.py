"""Phase fidelity-3: research-mode confirmation paths.

When ``intraday_confirmation.enabled=true``:
- Quotes available + valid → enter with fill_label='quote_confirmed'.
- No quotes available (research mode) → enter with fill_label='no_quote'.
- Stale quote (research mode) → entry SKIPPED with the source fail_reason.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


def _cfg(*, confirmation_enabled=True, max_spread_pct=0.02, max_age_seconds=15):
    return BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex",
                     "start_date": "2026-05-11", "end_date": "2026-05-12"},
            "entry": {
                "default_rule": "fixed_time_0945",
                "intraday_confirmation": {
                    "enabled": confirmation_enabled,
                    "window_minutes": 15,
                    "max_spread_pct": max_spread_pct,
                    "max_quote_age_seconds": max_age_seconds,
                    "price_band": {"max_pct_above_close": 0.50, "min_pct_below_close": -0.50},
                },
            },
            "portfolio": {"per_trade_notional": 1000.0, "max_concurrent_positions": 5,
                          "max_total_entries_per_day": 5},
        }
    )


def _candidates(signal_date):
    return pd.DataFrame([
        {"symbol": "AAA", "signal_date": signal_date, "rank": 1, "close": 5.0,
         "passed_prefilter": True, "avg_dollar_volume": 1e8},
    ])


def _bars(symbol, trade_date):
    minutes = pd.date_range(
        start=pd.Timestamp(trade_date).tz_localize("America/New_York")
        + pd.Timedelta(hours=9, minutes=30),
        periods=60, freq="1min", tz="America/New_York",
    ).tz_convert("UTC")
    rows = [{"symbol": symbol, "timestamp": ts, "open": 5.0, "high": 5.05, "low": 4.95,
             "close": 5.0, "volume": 100} for ts in minutes]
    return pd.DataFrame(rows)


def _quotes(symbol, trade_date, *, bid=4.95, ask=5.05, offset_seconds=0):
    confirm_ts = (pd.Timestamp(trade_date).tz_localize("America/New_York")
                  + pd.Timedelta(hours=9, minutes=45)).tz_convert("UTC")
    quote_ts = confirm_ts - pd.Timedelta(seconds=offset_seconds)
    return pd.DataFrame([{
        "symbol": symbol, "timestamp": quote_ts,
        "bid_price": bid, "ask_price": ask, "bid_size": 100, "ask_size": 100,
        "spread": ask - bid, "mid": (ask + bid) / 2.0,
        "spread_pct": (ask - bid) / ((ask + bid) / 2.0),
    }])


def _run(cfg, *, quotes_df=None):
    signal_date = date(2026, 5, 11)
    trade_date = date(2026, 5, 12)
    runner = BowakaPortfolioBacktester(
        cfg,
        candidate_source=lambda sd: _candidates(signal_date) if sd == signal_date else pd.DataFrame(),
        minute_bars_for=lambda td, syms: _bars("AAA", trade_date) if td == trade_date else pd.DataFrame(),
        quote_loader=(lambda td, syms: quotes_df if td == trade_date and quotes_df is not None else pd.DataFrame()),
    )
    return runner.run()


def test_research_mode_enters_with_quote_confirmed_when_quotes_valid():
    cfg = _cfg()
    quotes = _quotes("AAA", date(2026, 5, 12))
    res = _run(cfg, quotes_df=quotes)
    # Position opens but stays open at session end (no exit hit on flat bars,
    # max_hold_days=3). Asserting via open_positions instead of trades.
    assert len(res.open_positions) == 1
    assert not res.entry_skips


def test_research_mode_enters_with_no_quote_label_when_quotes_missing():
    cfg = _cfg()
    res = _run(cfg, quotes_df=pd.DataFrame())
    # Research mode does NOT fail closed — enters with bar fill.
    assert len(res.open_positions) == 1, "research mode should fall back to bar fill"
    assert not res.entry_skips


def test_research_mode_skips_when_quote_stale():
    cfg = _cfg(max_age_seconds=5)
    quotes = _quotes("AAA", date(2026, 5, 12), offset_seconds=60)  # 60s old > 5s cap
    res = _run(cfg, quotes_df=quotes)
    assert len(res.trades) == 0, "stale quote should block entry"
    assert len(res.entry_skips) == 1
    assert res.entry_skips[0].fail_reason.startswith("quote_age>")


def test_research_mode_skips_on_wide_spread():
    cfg = _cfg(max_spread_pct=0.005)
    quotes = _quotes("AAA", date(2026, 5, 12), bid=4.5, ask=5.5)  # 20% spread
    res = _run(cfg, quotes_df=quotes)
    assert len(res.trades) == 0
    assert res.entry_skips[0].fail_reason.startswith("spread>")


def test_entry_skips_df_has_documented_columns():
    cfg = _cfg(max_spread_pct=0.005)
    quotes = _quotes("AAA", date(2026, 5, 12), bid=4.5, ask=5.5)
    res = _run(cfg, quotes_df=quotes)
    df = res.entry_skips_df()
    for col in ("symbol", "trade_date", "fail_reason", "candidate_rank",
                "bar_ts", "mid", "spread_pct", "quote_age_seconds"):
        assert col in df.columns
