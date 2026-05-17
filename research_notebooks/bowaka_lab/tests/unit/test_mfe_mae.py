"""Phase 4: MFE/MAE calculation."""

from __future__ import annotations

import pandas as pd
import pytest

from bowaka_lab.metrics.mfe_mae import compute_mfe_mae


def _bars(rows):
    df = pd.DataFrame(rows, columns=["timestamp", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def test_mfe_pct_at_max_high_post_entry():
    entry_ts = pd.Timestamp("2026-05-12 13:45")
    bars = _bars(
        [
            (entry_ts, 10.1, 9.9, 10.0),
            (entry_ts + pd.Timedelta(minutes=1), 10.5, 10.0, 10.4),
            (entry_ts + pd.Timedelta(minutes=2), 10.3, 9.8, 9.9),
        ]
    )
    res = compute_mfe_mae(bars=bars, entry_time=entry_ts, entry_price=10.0, qty=100)
    assert res.mfe_pct == pytest.approx(0.05, abs=1e-9)
    assert res.time_to_mfe_minutes == 1


def test_mae_pct_at_min_low_post_entry():
    entry_ts = pd.Timestamp("2026-05-12 13:45")
    bars = _bars(
        [
            (entry_ts, 10.1, 9.9, 10.0),
            (entry_ts + pd.Timedelta(minutes=1), 10.5, 9.5, 9.7),
        ]
    )
    res = compute_mfe_mae(bars=bars, entry_time=entry_ts, entry_price=10.0, qty=100)
    assert res.mae_pct == pytest.approx(-0.05, abs=1e-9)
    assert res.time_to_mae_minutes == 1


def test_mfe_giveback_pct():
    entry_ts = pd.Timestamp("2026-05-12 13:45")
    bars = _bars(
        [
            (entry_ts, 10.1, 9.9, 10.0),
            (entry_ts + pd.Timedelta(minutes=1), 11.0, 10.0, 10.8),
            (entry_ts + pd.Timedelta(minutes=2), 10.9, 10.4, 10.5),
        ]
    )
    res = compute_mfe_mae(bars=bars, entry_time=entry_ts, entry_price=10.0, qty=100, current_price=10.5)
    # MFE = 0.10 (high 11.0), current return = 0.05, giveback = 0.5
    assert res.mfe_pct == pytest.approx(0.10, abs=1e-9)
    assert res.mfe_giveback_pct == pytest.approx(0.5, abs=1e-9)


def test_zero_path_returns_zero():
    res = compute_mfe_mae(bars=pd.DataFrame(columns=["timestamp", "high", "low", "close"]), entry_time=pd.Timestamp("2026-05-12"), entry_price=10.0, qty=100)
    assert res.mfe_pct == 0.0
    assert res.mae_pct == 0.0


def test_dollars_match_pct_times_qty():
    entry_ts = pd.Timestamp("2026-05-12 13:45")
    bars = _bars(
        [
            (entry_ts, 10.1, 9.9, 10.0),
            (entry_ts + pd.Timedelta(minutes=1), 11.0, 10.0, 10.8),
        ]
    )
    res = compute_mfe_mae(bars=bars, entry_time=entry_ts, entry_price=10.0, qty=100)
    assert res.mfe_dollars == pytest.approx(0.10 * 10.0 * 100)
