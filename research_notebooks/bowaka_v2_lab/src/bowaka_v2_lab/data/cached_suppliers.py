"""Bowaka-local cached lake-supplier adapter.

Speedup report §5.3 / §10.3 / §11.2 Phase 3. Wraps the shared
:class:`bowaka_common.marketdata.MarketDataStore` to eliminate repeated
Parquet reads: each `(symbol, year, month, feed, adjustment)` partition is
loaded ONCE per process, normalized identically to the store, and served on
subsequent calls from an in-memory frame via boolean masking (no `searchsorted`
yet — the parity-first implementation; vectorisation can come later if a hot
profile justifies it). The boundary semantics MUST match
``MarketDataStore.minute_bars`` exactly: ``[start, end]`` **both ends
inclusive**, ``sort_values("timestamp")``, ``drop_duplicates(subset=
["timestamp"], keep="last")``, tz-aware UTC.

The adapter is **per-process**. Phase 5 workers each build their own; cross-
process sharing is intentionally not supported (process boundaries are also
GIL boundaries — the savings live within a worker's lifetime).
"""
from __future__ import annotations

import datetime as _dt
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd

from bowaka_common.marketdata import MarketDataStore, layout as _layout
from bowaka_common.marketdata.store import (
    _empty_bars,
    _months_between,
    _normalise_bars,
    _to_date,
    _to_utc_ts,
    QuoteRow,
)

from ..utils.profile_counters import counters_enabled as _profile_counters_enabled
from ..utils.profile_counters import current_profile_counters as _profile_counters_current


def _count(**kwargs: int) -> None:
    if not _profile_counters_enabled():
        return
    try:
        _profile_counters_current().inc(**kwargs)
    except LookupError:
        pass


class _LRU(OrderedDict):
    """A tiny LRU dict with a hard size cap."""

    def __init__(self, max_entries: int):
        super().__init__()
        self.max_entries = int(max_entries)

    def get_or_set(self, key: Any, factory: Callable[[], Any]) -> Any:
        if key in self:
            self.move_to_end(key)
            return self[key]
        value = factory()
        self[key] = value
        while len(self) > self.max_entries:
            self.popitem(last=False)
        return value


class CachedSessionMarketData:
    """LRU-cached, normalised view over a :class:`MarketDataStore`.

    Per-process; not thread- or process-safe. Each Phase 5 worker constructs
    its own. The four public methods produce the same shapes / boundary
    semantics as the legacy ``make_lake_suppliers`` / ``make_quote_supplier``
    / ``make_forward_minute_supplier`` callables, so the backtester accepts
    them without changes.
    """

    def __init__(
        self,
        store: MarketDataStore,
        *,
        feed: str = "iex",
        intraday_window_policy: str = "scanner_start_to_scan",
        max_partition_entries: int = 4096,
        default_max_age_seconds: float = 60.0,
        window_minutes: int = 5,
        daily_lookback_days: int = 400,
        daily_adjustment: str = "raw",
    ):
        self.store = store
        self.feed = feed
        self.intraday_window_policy = intraday_window_policy
        self.default_max_age_seconds = float(default_max_age_seconds)
        self.window_minutes = int(window_minutes)
        self.daily_lookback_days = int(daily_lookback_days)
        # Audit 2026-05-29 §5.3 / Phase 1 — lake-partition adjustment for the
        # daily reader (default "raw"; "split_adjusted" when the config
        # requires adjusted daily bars).
        self.daily_adjustment = str(daily_adjustment)
        self._minute_cache: _LRU = _LRU(max_partition_entries)
        self._quote_cache: _LRU = _LRU(max_partition_entries)
        self._missing_quote_partitions: set[tuple[str, int, int]] = set()
        self._daily_cache: _LRU = _LRU(max(1, max_partition_entries // 4))

    # -- private partition readers ---------------------------------------
    def _minute_month(
        self,
        symbol: str,
        year: int,
        month: int,
        *,
        adjustment: str = "raw",
    ) -> pd.DataFrame:
        key = (symbol, year, month, self.feed, adjustment)

        def _load() -> pd.DataFrame:
            path = _layout.minute_bars_path(
                self.store.root, symbol, year, month,
                vendor=self.store.vendor, feed=self.feed, adjustment=adjustment,
            )
            if not path.is_file():
                # Cache the negative result as an empty frame so a missing
                # partition is not re-stat'd on every call.
                return _empty_bars()
            _count(minute_parquet_reads=1)
            df = _normalise_bars(pd.read_parquet(path))
            if df.empty:
                return df
            return (
                df.sort_values("timestamp")
                .drop_duplicates(subset=["timestamp"], keep="last")
                .reset_index(drop=True)
            )

        return self._minute_cache.get_or_set(key, _load)

    def _quote_month(
        self,
        symbol: str,
        year: int,
        month: int,
    ) -> Optional[pd.DataFrame]:
        key = (symbol, year, month, self.feed)
        if key in self._missing_quote_partitions:
            return None
        if key in self._quote_cache:
            self._quote_cache.move_to_end(key)
            return self._quote_cache[key]
        path = _layout.quotes_path(
            self.store.root, symbol, year, month,
            vendor=self.store.vendor, feed=self.feed,
        )
        if not path.is_file():
            self._missing_quote_partitions.add(key)
            return None
        try:
            _count(quote_parquet_reads=1)
            df = _normalise_bars(pd.read_parquet(path))
        except Exception:  # noqa: BLE001 — unreadable partition = "no quote"
            self._missing_quote_partitions.add(key)
            return None
        if df.empty or "timestamp" not in df.columns:
            self._missing_quote_partitions.add(key)
            return None
        df = df.sort_values("timestamp").reset_index(drop=True)
        self._quote_cache[key] = df
        while len(self._quote_cache) > self._quote_cache.max_entries:
            self._quote_cache.popitem(last=False)
        return df

    # -- public reads ----------------------------------------------------
    def forming_minutes(self, symbol: str, cutoff: Any) -> pd.DataFrame:
        """Minute bars from the policy-resolved session start to ``cutoff`` inclusive.

        Identical to the legacy ``minute_bars_supplier(symbol, cutoff)``
        (audit P0-006).

        Parity with :func:`bowaka_v2_lab.scanner.session_minute_window_supplier.make_session_minute_window_supplier`
        is enforced by ``tests/scanner/test_session_minute_window_supplier_parity.py``
        — do not modify either implementation's boundary semantics
        without updating that test.
        """
        _count(minute_supplier_calls=1)
        from .suppliers import intraday_window_start

        cutoff_ts = _to_utc_ts(cutoff)
        session_start = intraday_window_start(cutoff_ts, self.intraday_window_policy)
        # L1 (PIT look-ahead) fix: exclude the still-forming minute (START-stamped
        # bars span [cutoff, cutoff+60s)); end one bar interval (60s) earlier so
        # only fully-closed bars are returned. Mirrors suppliers.minute_bars_supplier.
        return self._range(
            symbol, session_start, cutoff_ts - pd.Timedelta(seconds=60)
        )

    def forward_minutes(
        self,
        symbol: str,
        ts: Any,
        window_minutes: Optional[int] = None,
    ) -> pd.DataFrame:
        """Minute bars FORWARD from ``ts`` for ``window_minutes`` (default 5)."""
        _count(minute_supplier_calls=1)
        start = _to_utc_ts(ts)
        win = int(window_minutes if window_minutes is not None else self.window_minutes)
        end = start + pd.Timedelta(minutes=win)
        return self._range(symbol, start, end)

    def _range(
        self,
        symbol: str,
        start_ts: pd.Timestamp,
        end_ts: pd.Timestamp,
    ) -> pd.DataFrame:
        if pd.isna(start_ts) or pd.isna(end_ts):
            return _empty_bars()
        frames: list[pd.DataFrame] = []
        for year, month in _months_between(start_ts, end_ts):
            df = self._minute_month(symbol, year, month)
            if not df.empty:
                frames.append(df)
        if not frames:
            return _empty_bars()
        cat = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
        # Boundary semantics: both ends INCLUSIVE (matches MarketDataStore.minute_bars).
        sliced = cat[(cat["timestamp"] >= start_ts) & (cat["timestamp"] <= end_ts)]
        return (
            sliced.sort_values("timestamp")
            .drop_duplicates(subset=["timestamp"], keep="last")
            .reset_index(drop=True)
        )

    def quote_at_or_before(
        self,
        symbol: str,
        ts: Any,
        max_age_seconds: Any = None,
    ) -> Optional[dict]:
        """The dict shape consumed by ``StrategyConsumer`` as
        ``historical_quote``. Matches ``make_quote_supplier`` exactly."""
        _count(quote_supplier_calls=1)
        target = _to_utc_ts(ts)
        df = self._quote_month(symbol, target.year, target.month)
        if df is None or df.empty:
            return None
        # Audit P1-002 — record the row's actual UTC timestamp.
        eligible = df[df["timestamp"] <= target]
        if eligible.empty:
            return None
        row = eligible.iloc[-1]  # sorted ascending; last <= target is most recent
        age = float((target - row["timestamp"]).total_seconds())
        max_age = float(
            max_age_seconds if max_age_seconds is not None else self.default_max_age_seconds
        )
        if age > max_age:
            return None
        bid = float(row.get("bid", 0.0) or 0.0)
        ask = float(row.get("ask", 0.0) or 0.0)
        mid_val = row.get("mid", None)
        mid = float(mid_val) if mid_val is not None and pd.notna(mid_val) else (bid + ask) / 2.0
        spread_pct_val = row.get("spread_pct", None)
        spread_pct = (
            float(spread_pct_val)
            if spread_pct_val is not None and pd.notna(spread_pct_val)
            else ((ask - bid) / mid if mid > 0 else 0.0)
        )
        row_ts = pd.Timestamp(row["timestamp"])
        if row_ts.tzinfo is None:
            row_ts = row_ts.tz_localize("UTC")
        else:
            row_ts = row_ts.tz_convert("UTC")
        return {
            "bid": bid,
            "ask": ask,
            "bid_size": float(row.get("bid_size", 0.0) or 0.0),
            "ask_size": float(row.get("ask_size", 0.0) or 0.0),
            "mid": mid,
            "spread_pct": spread_pct,
            "quote_timestamp": str(row_ts),
            "quote_age_seconds": max(0.0, age),
            "source": "historical",
        }

    def daily_bars(self, symbol: str, session_date: Any) -> pd.DataFrame:
        """Trailing ``daily_lookback_days`` daily bars ending on ``session_date``.

        Mirrors the legacy ``daily_bars_supplier(symbol, session_date)``.
        """
        end = _to_date(session_date)
        start = end - _dt.timedelta(days=self.daily_lookback_days)
        # Daily caching: bucket by (symbol, end_date, feed, adjustment) so a
        # fold reusing the same lookback window does not re-read the parquet on
        # every call, and a raw vs split_adjusted read never collide in cache.
        key = (symbol, end, self.feed, self.daily_adjustment)

        def _load() -> pd.DataFrame:
            return self.store.daily_bars(
                symbol, start, end, feed=self.feed,
                adjustment=self.daily_adjustment,
            )

        return self._daily_cache.get_or_set(key, _load)


def make_cached_lake_suppliers(
    lake_root: Any,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    intraday_window_policy: str = "scanner_start_to_scan",
    daily_lookback_days: int = 400,
    default_max_age_seconds: float = 60.0,
    window_minutes: int = 5,
    max_partition_entries: int = 4096,
    daily_adjustment: str = "raw",
) -> CachedSessionMarketData:
    """Construct a :class:`CachedSessionMarketData` for ``lake_root``.

    Audit 2026-05-29 §5.3 / Phase 1: ``daily_adjustment`` selects the daily
    lake partition (default ``"raw"``).
    """
    store = (
        lake_root if isinstance(lake_root, MarketDataStore)
        else MarketDataStore(lake_root, vendor=vendor)
    )
    return CachedSessionMarketData(
        store, feed=feed,
        intraday_window_policy=intraday_window_policy,
        daily_lookback_days=daily_lookback_days,
        default_max_age_seconds=default_max_age_seconds,
        window_minutes=window_minutes,
        max_partition_entries=max_partition_entries,
        daily_adjustment=daily_adjustment,
    )


def make_cached_supplier_callables(adapter: CachedSessionMarketData) -> dict[str, Callable]:
    """Return the four legacy-shape callables backed by ``adapter``.

    Each callable's signature matches the existing
    :mod:`bowaka_v2_lab.data.suppliers` callables so the backtester accepts
    them without changes.
    """
    return {
        "minute": adapter.forming_minutes,
        "forward_minute": adapter.forward_minutes,
        "quote": adapter.quote_at_or_before,
        "daily": adapter.daily_bars,
    }


__all__ = [
    "CachedSessionMarketData",
    "make_cached_lake_suppliers",
    "make_cached_supplier_callables",
]
