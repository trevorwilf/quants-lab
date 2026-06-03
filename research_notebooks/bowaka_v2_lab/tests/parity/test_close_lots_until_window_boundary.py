"""Regression lock — the ``_close_lots_until`` per-event window boundary.

Per-trial sim speedup: the minute event loop's ``_close_lots_until`` used to
recompute the new-bar count on every poll-cadence event (~10k/session) with
``pd.to_datetime(bars.iloc[cursor:][ts]) <= walk_until`` then ``mask.sum()`` —
an O(remaining-tail) re-parse per event. It now caches each lot's sorted ns
timestamps ONCE and finds the boundary with a single
``np.searchsorted(ts_ns, walk_until_ns, side="right")``.

The full-fold parity tests cross-compare *scan modes*, which all share this
code, so they cannot catch a boundary regression here. This module pins the two
formulas equal directly: for a realistic 5-second poll cadence over a held lot's
session path (and assorted edge frames — µs vs ns resolution, duplicate
timestamps, a bar exactly on the event ts), the cached-``searchsorted`` boundary
must equal the legacy ``to_datetime + mask.sum`` boundary at every event. A
mismatch means a different set of minute bars would reach ``walk_lot_exit`` —
i.e. a changed trade — and is a hard failure.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

_ET = "America/New_York"


def _legacy_new_idx(bars: pd.DataFrame, cursor: int, walk_until: pd.Timestamp,
                    ts_col: str) -> int:
    """The pre-speedup boundary: re-parse the tail, mask <= walk_until, sum."""
    sub = bars.iloc[cursor:]
    sub_ts = pd.to_datetime(sub[ts_col], utc=True)
    mask = sub_ts <= pd.Timestamp(walk_until)
    return cursor + int(mask.sum())


def _cached_ts_ns(bars: pd.DataFrame, ts_col: str) -> np.ndarray:
    """The production ns cache (mirrors backtester._close_lots_until setup)."""
    idx = pd.DatetimeIndex(bars[ts_col])
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    return idx.tz_localize(None).to_numpy(dtype="datetime64[ns]").view("int64")


def _fast_new_idx(ts_ns: np.ndarray, walk_until: pd.Timestamp) -> int:
    """The production boundary (mirrors backtester._close_lots_until)."""
    wu = pd.Timestamp(walk_until)
    wu = wu.tz_localize("UTC") if wu.tzinfo is None else wu.tz_convert("UTC")
    return int(np.searchsorted(ts_ns, wu.value, side="right"))


def _session_bars(n: int = 390, *, unit: str = "us") -> pd.DataFrame:
    base = pd.Timestamp("2024-09-04 09:31", tz=_ET).tz_convert("UTC")
    ts = pd.to_datetime([base + pd.Timedelta(minutes=i) for i in range(n)]).as_unit(unit)
    return pd.DataFrame({
        "timestamp": ts, "open": 100.0, "high": 100.2, "low": 99.8,
        "close": 100.0, "volume": 1000.0,
    })


def _poll_events(step_seconds: int = 5) -> list[pd.Timestamp]:
    start = pd.Timestamp("2024-09-04 09:31", tz=_ET).tz_convert("UTC")
    end = pd.Timestamp("2024-09-04 16:00", tz=_ET).tz_convert("UTC")
    k = int((end - start).total_seconds() // step_seconds) + 1
    return [start + pd.Timedelta(seconds=step_seconds * i) for i in range(k)]


@pytest.mark.parametrize("unit", ["us", "ns"])
def test_full_session_5s_cadence_boundary_parity(unit: str) -> None:
    """The cursor walk over a whole session at 5s cadence is byte-identical."""
    bars = _session_bars(390, unit=unit)
    ts_ns = _cached_ts_ns(bars, "timestamp")
    cur_legacy = cur_fast = 0
    for ev in _poll_events(5):
        legacy = _legacy_new_idx(bars, cur_legacy, ev, "timestamp")
        fast = _fast_new_idx(ts_ns, ev)
        assert legacy == fast, f"unit={unit} ev={ev} legacy={legacy} fast={fast}"
        # advance both cursors exactly as the event loop does (only forward)
        cur_legacy = legacy
        cur_fast = fast if fast > cur_fast else cur_fast


def test_bar_exactly_on_event_is_included() -> None:
    """A bar whose ts == walk_until is INCLUDED (side='right' == legacy <=)."""
    bars = _session_bars(10)
    ts_ns = _cached_ts_ns(bars, "timestamp")
    for i in range(len(bars)):
        ev = pd.Timestamp(bars["timestamp"].iloc[i])
        assert _legacy_new_idx(bars, 0, ev, "timestamp") == _fast_new_idx(ts_ns, ev)
        # one ns before the bar excludes it in both
        ev_minus = ev - pd.Timedelta(nanoseconds=1)
        assert _legacy_new_idx(bars, 0, ev_minus, "timestamp") == _fast_new_idx(ts_ns, ev_minus)


def test_duplicate_timestamps_boundary_parity() -> None:
    bars = _session_bars(6)
    dup = pd.concat([bars, bars.iloc[[2, 2, 4]]], ignore_index=True)
    dup = dup.sort_values("timestamp").reset_index(drop=True)  # pre-sorted, as cached
    ts_ns = _cached_ts_ns(dup, "timestamp")
    for cursor in range(len(dup)):
        for ev in _poll_events(30):
            assert _legacy_new_idx(dup, cursor, ev, "timestamp") == _fast_new_idx(ts_ns, ev) \
                or _fast_new_idx(ts_ns, ev) <= cursor  # both agree, or no-new-bars guard
    # exact, cursor-0 sweep over the dup bar timestamps
    for i in range(len(dup)):
        ev = pd.Timestamp(dup["timestamp"].iloc[i])
        assert _legacy_new_idx(dup, 0, ev, "timestamp") == _fast_new_idx(ts_ns, ev)


def test_single_bar_and_empty_tail() -> None:
    bars = _session_bars(1)
    ts_ns = _cached_ts_ns(bars, "timestamp")
    ev = pd.Timestamp(bars["timestamp"].iloc[0])
    assert _legacy_new_idx(bars, 0, ev, "timestamp") == _fast_new_idx(ts_ns, ev) == 1
    before = ev - pd.Timedelta(minutes=1)
    assert _legacy_new_idx(bars, 0, before, "timestamp") == _fast_new_idx(ts_ns, before) == 0
