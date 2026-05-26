"""In-memory session minute-bar window cache (speedup report v2 §4 P3 / §5.7).

The legacy minute supplier
(:func:`bowaka_v2_lab.data.suppliers.make_lake_suppliers`)
calls :meth:`MarketDataStore.minute_bars` for every ``(symbol, scan_ts)`` pair
the scanner inspects — each call re-reads the per-month parquet partition,
filters by symbol, and bounds the slice by
:func:`bowaka_v2_lab.data.suppliers.intraday_window_start`. For a fold with
N eligible symbols * S scan timestamps the per-pair filter dominates the
scanner cost.

:class:`SessionMinuteWindowCache` preloads each symbol's
**regular-session** minute frame once for a given session and replies to
``bars_until(symbol, scan_ts)`` with a numpy-searchsorted slice. Boundary
semantics mirror the legacy minute supplier exactly so a parity-tested
swap-in is byte-stable:

* Inclusive lower bound:
  :func:`bowaka_v2_lab.data.suppliers.intraday_window_start` for the
  resolved policy.
* Inclusive upper bound: ``scan_ts`` (i.e. a bar whose timestamp ==
  scan_ts IS returned — ``searchsorted(..., side="right")``).
* Missing-symbol semantics: empty frame with the canonical columns.

The optional ``max_bar_age_seconds`` constructor knob is **off by default**
(``None``). When set, the lower bound becomes the LATER of
``intraday_window_start(scan_ts, policy)`` and
``scan_ts - max_bar_age_seconds`` — a tighter recency window. With the
default ``None`` the legacy parity holds; with an explicit value the
cache emits only the most recent N seconds of bars (used by the
``max_bar_age`` benchmark test).
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from bowaka_common.marketdata import MarketDataStore

from ..data.suppliers import (
    _DEFAULT_INTRADAY_WINDOW_POLICY,
    intraday_window_start,
    make_lake_suppliers,
)
from ..utils.profile_counters import counters_enabled, current_profile_counters


_EMPTY_MINUTE_COLUMNS: tuple[str, ...] = (
    "symbol", "timestamp", "open", "high", "low", "close", "volume",
)


def _empty_minute_frame() -> pd.DataFrame:
    """Empty frame with the canonical minute-bar columns + dtypes.

    Mirrors the legacy minute-supplier behaviour on a missing symbol — the
    scanner expects a DataFrame, not ``None``, for downstream slicing.
    """
    return pd.DataFrame(
        {
            "symbol": pd.Series([], dtype="object"),
            "timestamp": pd.Series([], dtype="datetime64[ns, UTC]"),
            "open": pd.Series([], dtype="float64"),
            "high": pd.Series([], dtype="float64"),
            "low": pd.Series([], dtype="float64"),
            "close": pd.Series([], dtype="float64"),
            "volume": pd.Series([], dtype="float64"),
        }
    )


def _count(**kwargs: int) -> None:
    if not counters_enabled():
        return
    try:
        current_profile_counters().inc(**kwargs)
    except LookupError:
        pass


def _ts_to_utc(ts: Any) -> pd.Timestamp:
    """Normalize ``ts`` to a UTC-aware ``pd.Timestamp``."""
    p = pd.Timestamp(ts)
    return p.tz_localize("UTC") if p.tzinfo is None else p.tz_convert("UTC")


class SessionMinuteWindowCache:
    """Per-session cache of every eligible symbol's regular-session minute frame.

    Construction reads each symbol's session frame ONCE via the legacy
    supplier (so the lake/normalisation logic is unchanged). The runtime
    ``bars_until`` call is a pure-numpy ``searchsorted`` slice plus a
    ``pandas`` ``.iloc[...]``. The cache produces a frame with the SAME
    columns and dtypes the legacy supplier returns — the only difference
    is the wall-clock cost.
    """

    def __init__(
        self,
        store: MarketDataStore | Any,
        session: _dt.date,
        symbols: Sequence[str],
        *,
        feed: str = "iex",
        intraday_policy: str = _DEFAULT_INTRADAY_WINDOW_POLICY,
        max_bar_age_seconds: Optional[float] = None,
    ) -> None:
        self.session = session
        self.feed = str(feed)
        self.intraday_policy = str(intraday_policy)
        self.max_bar_age_seconds: Optional[float] = (
            float(max_bar_age_seconds) if max_bar_age_seconds is not None else None
        )
        self._frames: dict[str, pd.DataFrame] = {}
        self._timestamps: dict[str, np.ndarray] = {}
        # The legacy supplier already encapsulates timezone / dedup logic;
        # reuse it via a one-shot probe at the regular-session END so the
        # cache loads the FULL session frame for the symbol.
        minute_supplier, _ = make_lake_suppliers(
            store if not hasattr(store, "minute_bars") else store,
            feed=self.feed,
            intraday_window_policy=self.intraday_policy,
        ) if not isinstance(store, MarketDataStore) else (None, None)
        if minute_supplier is None:
            # ``store`` IS a MarketDataStore — rebuild the supplier against it.
            minute_supplier, _ = make_lake_suppliers(
                store, feed=self.feed,
                intraday_window_policy=self.intraday_policy,
            )
        # Probe ts is the regular-session end (16:00 ET); the legacy
        # supplier returns every bar in [intraday_window_start, 16:00 ET]
        # for the session — equivalent to the full session frame.
        probe_et = pd.Timestamp(
            _dt.datetime.combine(self.session, _dt.time(hour=16, minute=0)),
            tz="America/New_York",
        )
        probe_utc = probe_et.tz_convert("UTC")
        for symbol in symbols:
            frame = minute_supplier(symbol, probe_utc)
            _count(minute_parquet_reads=1)
            if frame is None or len(frame) == 0:
                continue
            # Ensure the timestamp column is tz-aware UTC.
            ts_col = pd.to_datetime(frame["timestamp"], utc=True)
            frame = frame.assign(timestamp=ts_col).sort_values("timestamp").reset_index(drop=True)
            self._frames[str(symbol)] = frame
            self._timestamps[str(symbol)] = (
                frame["timestamp"].to_numpy().astype("datetime64[ns]").astype("int64")
            )

    def bars_until(self, symbol: str, scan_ts: Any) -> pd.DataFrame:
        """Return the legacy minute-supplier slice from the in-memory cache.

        Boundary semantics:

        * Lower bound: :func:`intraday_window_start(scan_ts, policy)` when
          ``max_bar_age_seconds is None`` (legacy parity). With an explicit
          value the cache uses the LATER of the policy bound and
          ``scan_ts - max_bar_age_seconds``.
        * Upper bound (inclusive): ``scan_ts`` —
          ``np.searchsorted(timestamps, ts_ns, side="right")`` so a bar
          whose timestamp equals ``scan_ts`` IS returned.
        """
        _count(bars_supplier_calls=1)
        frame = self._frames.get(str(symbol))
        if frame is None:
            _count(session_window_cache_misses=1)
            return _empty_minute_frame()
        _count(session_window_cache_hits=1)
        ts_utc = _ts_to_utc(scan_ts)
        ts_ns = ts_utc.value
        # Inclusive upper bound: side="right" → index AFTER all ts <= ts_ns.
        timestamps = self._timestamps[str(symbol)]
        hi_idx = int(np.searchsorted(timestamps, ts_ns, side="right"))
        # Lower bound: legacy policy ∪ optional max_bar_age.
        policy_lo_ns = intraday_window_start(ts_utc, self.intraday_policy).value
        lo_ns = policy_lo_ns
        if self.max_bar_age_seconds is not None:
            age_lo_ns = ts_ns - int(self.max_bar_age_seconds * 1_000_000_000)
            lo_ns = max(policy_lo_ns, age_lo_ns)
        lo_idx = int(np.searchsorted(timestamps, lo_ns, side="left"))
        slice_df = frame.iloc[lo_idx:hi_idx]
        _count(bars_df_slices=1)
        return slice_df


__all__ = ["SessionMinuteWindowCache"]
