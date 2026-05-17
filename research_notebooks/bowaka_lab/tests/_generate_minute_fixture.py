"""Synthetic minute-bar fixture for the backtester integration test.

Builds:
  tests/fixtures/minute_bars_small.parquet  -- 2 symbols, 5 trading sessions
  tests/fixtures/expected_backtest_trades.json
                                            -- golden trades produced by the
                                               default exit geometry on the
                                               minute fixture

The data is deliberately small and deterministic. The goal is *not* a realistic
microcap profile; it is *just* enough resolution to exercise stop, target, and
time-stop exits in a single canned run.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent / "fixtures"


def _session_minutes(session_date: date) -> pd.DatetimeIndex:
    start = pd.Timestamp(session_date).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30)
    return pd.date_range(start=start, periods=390, freq="1min", tz="America/New_York").tz_convert("UTC")


def _build_session(*, symbol: str, session_date: date, open_p: float, intraday_pct_path: list[float]) -> pd.DataFrame:
    """Produce 390 1-minute bars whose closes follow ``intraday_pct_path``.

    ``intraday_pct_path`` is a list of length 390 of cumulative percent returns
    from open. open/high/low/close are derived so high == max(open, close) and
    low == min(open, close) within each minute.
    """
    minutes = _session_minutes(session_date)
    closes = [open_p * (1.0 + p) for p in intraday_pct_path]
    rows = []
    prev = open_p
    for ts, close in zip(minutes, closes, strict=False):
        bar_open = prev
        bar_close = close
        bar_high = max(bar_open, bar_close) * 1.001
        bar_low = min(bar_open, bar_close) * 0.999
        rows.append(
            {
                "symbol": symbol,
                "timestamp": ts,
                "open": float(bar_open),
                "high": float(bar_high),
                "low": float(bar_low),
                "close": float(bar_close),
                "volume": 1000,
            }
        )
        prev = bar_close
    df = pd.DataFrame(rows)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def _build_target_session(symbol: str, session_date: date, open_p: float, target_pct: float) -> pd.DataFrame:
    """Build a session that ramps from 0% to (target_pct + 0.01) linearly."""
    path = np.linspace(0.0, target_pct + 0.02, num=390).tolist()
    return _build_session(symbol=symbol, session_date=session_date, open_p=open_p, intraday_pct_path=path)


def _build_stop_session(symbol: str, session_date: date, open_p: float, stop_pct: float) -> pd.DataFrame:
    """Build a session that drops from 0% to -(stop_pct + 0.01) linearly."""
    path = np.linspace(0.0, -(stop_pct + 0.02), num=390).tolist()
    return _build_session(symbol=symbol, session_date=session_date, open_p=open_p, intraday_pct_path=path)


def _build_flat_session(symbol: str, session_date: date, open_p: float) -> pd.DataFrame:
    path = np.linspace(0.0, 0.005, num=390).tolist()
    return _build_session(symbol=symbol, session_date=session_date, open_p=open_p, intraday_pct_path=path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Five sessions: signal_date is 2026-05-08, trade_dates 5/11..5/15.
    sessions = [date(2026, 5, 11), date(2026, 5, 12), date(2026, 5, 13), date(2026, 5, 14), date(2026, 5, 15)]
    frames = []
    # AAA hits target on 2026-05-11 (entry day).
    frames.append(_build_target_session("AAA", sessions[0], open_p=5.0, target_pct=0.15))
    # AAA holds flat for subsequent sessions (won't matter because target hit on day 1).
    for s in sessions[1:]:
        frames.append(_build_flat_session("AAA", s, open_p=5.7))

    # BBB hits stop on 2026-05-12 (day 2 of hold) — flat day 1, then drops.
    frames.append(_build_flat_session("BBB", sessions[0], open_p=10.0))
    frames.append(_build_stop_session("BBB", sessions[1], open_p=10.05, stop_pct=0.08))
    for s in sessions[2:]:
        frames.append(_build_flat_session("BBB", s, open_p=9.2))

    # CCC times out on day 3 (max_hold_days=3, default) — flat all three days.
    for s in sessions:
        frames.append(_build_flat_session("CCC", s, open_p=4.0))

    minute_bars = pd.concat(frames, ignore_index=True)
    minute_bars.to_parquet(OUT_DIR / "minute_bars_small.parquet", index=False)
    print(f"Wrote minute fixture: {OUT_DIR / 'minute_bars_small.parquet'}")


if __name__ == "__main__":
    main()
