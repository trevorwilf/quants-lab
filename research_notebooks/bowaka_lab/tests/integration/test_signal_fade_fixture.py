"""Phase 6: signal-fade integration on synthetic per-minute path."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.features.signal_fade_features import assemble_intraday_context
from bowaka_lab.sim.signal_fade import compute_signal_fade_score


def _make_bars(*, session_date: date, path_pct: list[float], symbol: str = "X") -> pd.DataFrame:
    minutes = pd.date_range(
        start=pd.Timestamp(session_date).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30),
        periods=len(path_pct),
        freq="1min",
        tz="America/New_York",
    ).tz_convert("UTC")
    rows = []
    base = 10.0
    for ts, p in zip(minutes, path_pct):
        price = base * (1.0 + p)
        rows.append({"symbol": symbol, "timestamp": ts, "open": price, "high": price * 1.001, "low": price * 0.999, "close": price, "volume": 1000})
    df = pd.DataFrame(rows)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def test_fade_evolves_with_path():
    # Path: pop +5% in first 60 min, then sag to -2% by minute 200.
    path = [min(0.05, i * 0.001) for i in range(60)] + [0.05 - 0.0007 * (i - 60) for i in range(60, 200)]
    bars = _make_bars(session_date=date(2026, 5, 11), path_pct=path)
    entry_time = bars.iloc[0]["timestamp"]
    entry_price = float(bars.iloc[0]["close"])
    now_ts = bars.iloc[-1]["timestamp"]
    current_price = float(bars.iloc[-1]["close"])

    ctx = assemble_intraday_context(
        bars_through_now=bars,
        entry_price=entry_price,
        entry_time=entry_time,
        now_ts=now_ts,
        prior_close=10.0,
        session_date=date(2026, 5, 11),
    )
    mfe_pct = ctx.running_high / entry_price - 1.0
    current_return = current_price / entry_price - 1.0
    res = compute_signal_fade_score(
        entry_price=entry_price,
        mfe_pct=mfe_pct,
        current_return_pct=current_return,
        minutes_since_entry=ctx.minutes_since_entry,
        intraday=ctx,
    )
    # Path gave back > 50% of MFE → should at least be soft fade.
    assert res.score >= 3
