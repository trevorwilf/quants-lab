"""The batch builder computes EMA on the truncated per-session slice — not
once over the full symbol history.

Speedup report v2 §4 P1 / Phase 1 task 5. The 400-day truncation is part of
the strategy definition: a 500-row close series's truncated EMA(span=10,
adjust=False) is provably different from the full-history EMA at the
boundary. Both legacy and batch paths must produce the truncated value;
this test pins it.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.daily_cache_batch import build_daily_cache_for_sessions_from_lake
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake


def _write_daily(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_batch_matches_legacy_truncated_ema_and_differs_from_full_history(
    tmp_path: Path,
) -> None:
    """At the truncation boundary, full-history EMA differs from the truncated
    one. Both legacy and batch builders must produce the same truncated value.

    Tuned to ``lookback_days=30`` with ``ema_span=10`` because EMA's
    effective memory is ~2*span = ~20 days; with the default
    ``lookback_days=400`` the boundary is irrelevant for any reasonable
    series (days 30..400 in the past carry weight ≈ 0 in EMA(span=10)).
    """
    lake = tmp_path / "lake"
    sym = "ABC"
    # 100 trading days. Days [0..69] flat-HIGH at 1000.0; days [70..99] flat-LOW
    # at 100.0. With lookback_days=30 the truncated window is days [70..99] —
    # 30 closes all at 100.0 → truncated EMA ≈ 100.0. The full-history EMA
    # over [0..99] still carries appreciable weight from the high regime.
    n_days = 100
    days = [d.date() for d in pd.bdate_range(dt.date(2024, 1, 1), periods=n_days)]
    closes = [1000.0 if i < 70 else 100.0 for i in range(n_days)]
    _write_daily(
        layout.daily_bars_path(lake, sym, feed="iex"),
        pd.DataFrame({
            "symbol": [sym] * n_days,
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
            "open":   closes, "high": [c + 1 for c in closes],
            "low":    [c - 1 for c in closes], "close":  closes,
            "volume": [1_000_000] * n_days, "session_date": days,
        }),
    )
    session = days[-1]  # use the last trading day as the scan session
    legacy_df = build_daily_cache_from_lake(
        lake, [sym], session, feed="iex", lookback_days=30,
    )
    batch_out = build_daily_cache_for_sessions_from_lake(
        lake, {session: [sym]}, [session], feed="iex", lookback_days=30,
    )
    legacy_ema = float(legacy_df["ema_10_prior"].iloc[0])
    batch_ema = float(batch_out[session]["ema_10_prior"].iloc[0])
    # legacy <-> batch agree within float-equal tolerance.
    assert abs(legacy_ema - batch_ema) <= 1e-12

    # Full-history EMA — different by design.
    full_close = pd.Series(closes)
    full_ema = float(full_close.ewm(span=10, adjust=False).mean().iloc[-2])  # iloc[-2] = day before session
    assert abs(full_ema - legacy_ema) > 1e-6, (
        f"full-history EMA {full_ema!r} too close to truncated EMA {legacy_ema!r}; "
        "the test scenario does not exercise the truncation boundary"
    )
