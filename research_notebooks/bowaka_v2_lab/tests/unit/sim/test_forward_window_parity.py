"""§10h opt #2 — ``_forward_window`` must be byte-identical to the prior inline
``df.copy(); df['timestamp']=pd.to_datetime(utc=True); df[mask].sort_values('timestamp')``
pattern it replaced in the five fill-model helpers.

Asserts the selected rows AND their order (the frame index) match a reference
implementation of the old pattern across edge cases (tz-aware, tz-naive, unsorted,
windowed, empty), and locks the five public helpers' outputs on a known frame.
"""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.sim.fills import (
    _ask_path_from_bars,
    _ask_runs_above_limit,
    _forward_window,
    _minute_dollar_volume,
    _minute_volume_shares,
    _scan_bar,
)

_OHLCV = ["open", "high", "low", "close", "volume"]


def _ref_forward(minute_bars, scan_ts, horizon_seconds=None):
    """The exact prior inline pattern (the byte-identical reference)."""
    if minute_bars is None or len(minute_bars) == 0 or "timestamp" not in minute_bars.columns:
        return None
    df = minute_bars.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    cut = pd.Timestamp(scan_ts)
    cut = cut.tz_localize("UTC") if cut.tzinfo is None else cut.tz_convert("UTC")
    if horizon_seconds is None:
        return df[df["timestamp"] >= cut].sort_values("timestamp")
    horizon = cut + pd.Timedelta(seconds=int(horizon_seconds))
    return df[(df["timestamp"] >= cut) & (df["timestamp"] <= horizon)].sort_values("timestamp")


def _frame(tz="UTC", shuffle=False):
    ts = pd.date_range("2025-11-03T14:30:00", periods=6, freq="1min", tz=tz)
    df = pd.DataFrame({
        "timestamp": ts,
        "open": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5],
        "high": [10.2, 10.3, 10.6, 10.4, 10.9, 10.7],
        "low": [9.9, 10.0, 10.1, 10.2, 10.3, 10.4],
        "close": [10.1, 10.2, 10.3, 10.35, 10.5, 10.6],
        "volume": [100.0, 200.0, 300.0, 400.0, 500.0, 600.0],
    })
    if shuffle:
        df = df.iloc[[3, 0, 5, 1, 4, 2]].reset_index(drop=True)
    return df


def _assert_same(new, ref):
    if ref is None or new is None:
        assert new is ref or (new is None and ref is None), (new, ref)
        return
    # Same rows, same order (index), same OHLCV payload — the timestamp column may
    # differ in tz REPRESENTATION (the consumers never read it), so compare payload.
    assert list(new.index) == list(ref.index), (list(new.index), list(ref.index))
    assert new[_OHLCV].reset_index(drop=True).equals(ref[_OHLCV].reset_index(drop=True))


@pytest.mark.parametrize("tz", ["UTC", "US/Eastern", None])
@pytest.mark.parametrize("shuffle", [False, True])
def test_forward_window_matches_reference_forward_only(tz, shuffle):
    df = _frame(tz=tz, shuffle=shuffle)
    scan_ts = pd.Timestamp("2025-11-03T14:32:00", tz="UTC")
    _assert_same(_forward_window(df, scan_ts), _ref_forward(df, scan_ts))


@pytest.mark.parametrize("tz", ["UTC", None])
@pytest.mark.parametrize("horizon", [30, 90, 150])
def test_forward_window_matches_reference_windowed(tz, horizon):
    df = _frame(tz=tz)
    scan_ts = pd.Timestamp("2025-11-03T14:31:00", tz="UTC")
    _assert_same(
        _forward_window(df, scan_ts, horizon_seconds=horizon),
        _ref_forward(df, scan_ts, horizon_seconds=horizon),
    )


def test_forward_window_empty_forward_window():
    df = _frame()
    scan_ts = pd.Timestamp("2025-11-03T18:00:00", tz="UTC")  # after every bar
    new = _forward_window(df, scan_ts)
    assert new is not None and new.empty
    _assert_same(new, _ref_forward(df, scan_ts))


@pytest.mark.parametrize("bad", [None, pd.DataFrame(), pd.DataFrame({"open": [1.0]})])
def test_forward_window_unusable_frame_returns_none(bad):
    assert _forward_window(bad, pd.Timestamp("2025-11-03T14:32:00", tz="UTC")) is None


def test_public_helpers_lock_values():
    df = _frame()
    scan_ts = pd.Timestamp("2025-11-03T14:32:00", tz="UTC")  # bars idx 2..5 forward
    # _scan_bar -> first forward bar (idx 2)
    assert _scan_bar(df, scan_ts) == {"open": 10.2, "high": 10.6, "low": 10.1, "close": 10.3}
    # _ask_path_from_bars -> forward high path, in order
    assert _ask_path_from_bars(df, scan_ts) == [10.6, 10.4, 10.9, 10.7]
    # _minute_dollar_volume -> first forward bar volume*close
    assert _minute_dollar_volume(df, scan_ts) == pytest.approx(300.0 * 10.3)
    # _minute_volume_shares -> first forward bar volume
    assert _minute_volume_shares(df, scan_ts) == pytest.approx(300.0)
    # _ask_runs_above_limit (buy) -> ALL windowed bars' high above limit (min > limit).
    # horizon 90s window = bars at 14:32 (high 10.6) + 14:33 (high 10.4) -> min 10.4.
    assert _ask_runs_above_limit(df, scan_ts, "buy", 10.3, 90) is True
    assert _ask_runs_above_limit(df, scan_ts, "buy", 10.5, 90) is False
