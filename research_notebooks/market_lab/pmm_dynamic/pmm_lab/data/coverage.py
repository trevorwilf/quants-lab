"""Data-coverage preflight for the range_ladder walk-forward notebook.

`audit_pair` reads the Mongo lake via the existing loader and reports the
usable span/gap profile for one (connector, pair, interval).
`preflight_pair` picks 1h-native candles when present, otherwise resamples
5m→1h, and ABORTS (raises) instead of silently shrinking walk-forward folds
when history is too short or too gappy.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from pmm_lab.config.defaults import INTERVAL_SECONDS
from pmm_lab.config.params import DataQuery

logger = logging.getLogger(__name__)

MIN_USABLE_DAYS = 150.0
MAX_GAP_PCT = 5.0


def audit_pair(
    connector: str,
    trading_pair: str,
    interval: str,
    loader=None,
) -> dict:
    """Coverage audit for one (connector, pair, interval) in the Mongo lake.

    Returns a dict with: first_ts, last_ts, days, bars, expected_bars,
    gap_pct, max_gap_hours. A pair with no data returns zeros (bars=0)
    rather than raising, so the notebook can print a full audit table.
    """
    if interval not in INTERVAL_SECONDS:
        raise ValueError(
            f"Invalid interval '{interval}'. Valid: {list(INTERVAL_SECONDS)}"
        )
    iv = INTERVAL_SECONDS[interval]
    if loader is None:
        from pmm_lab.data.mongo import MongoCandleLoader
        loader = MongoCandleLoader()

    empty = dict(
        connector=connector, trading_pair=trading_pair, interval=interval,
        first_ts=None, last_ts=None, days=0.0, bars=0, expected_bars=0,
        gap_pct=100.0, max_gap_hours=float("inf"),
    )
    try:
        candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=trading_pair, interval=interval)
        )
    except ValueError:
        return empty
    if len(candles) == 0:
        return empty

    ts = candles["timestamp"].astype(np.int64)
    first_ts, last_ts = int(ts[0]), int(ts[-1])
    bars = int(len(ts))
    expected = int((last_ts - first_ts) // iv) + 1
    gap_pct = (expected - bars) / expected * 100.0 if expected > 0 else 0.0
    if bars > 1:
        max_gap_seconds = int(np.max(np.diff(ts))) - iv
    else:
        max_gap_seconds = 0
    return dict(
        connector=connector, trading_pair=trading_pair, interval=interval,
        first_ts=first_ts, last_ts=last_ts,
        days=float((last_ts - first_ts) / 86400.0),
        bars=bars, expected_bars=expected,
        gap_pct=float(gap_pct),
        max_gap_hours=float(max(0, max_gap_seconds) / 3600.0),
    )


def resample_candles(
    candles: np.ndarray,
    from_interval: str,
    to_interval: str,
) -> np.ndarray:
    """Resample OHLCV candles to a coarser UTC-aligned interval.

    Buckets are aligned to the target interval on the UTC epoch grid
    (bucket_ts = ts - ts % to_seconds). Aggregation: open = first bar's
    open, high = max, low = min, close = last bar's close, volume = sum.
    A bucket is flagged forward-fill only if ALL contributing bars are.
    """
    from_s = INTERVAL_SECONDS[from_interval]
    to_s = INTERVAL_SECONDS[to_interval]
    if to_s % from_s != 0 or to_s <= from_s:
        raise ValueError(
            f"target interval {to_interval} must be a coarser multiple of "
            f"{from_interval}"
        )
    if len(candles) == 0:
        return candles.copy()

    ts = candles["timestamp"].astype(np.int64)
    bucket = ts - (ts % to_s)
    # candles are sorted by timestamp (loader guarantees); bucket boundaries
    # are where the bucket id changes.
    change = np.nonzero(np.diff(bucket))[0] + 1
    starts = np.concatenate([[0], change])
    ends = np.concatenate([change, [len(candles)]])

    rows = []
    for s, e in zip(starts, ends):
        chunk = candles[s:e]
        rows.append((
            int(bucket[s]),
            float(chunk["open"][0]),
            float(np.max(chunk["high"])),
            float(np.min(chunk["low"])),
            float(chunk["close"][-1]),
            float(np.sum(chunk["volume"])),
            bool(np.all(chunk["is_forward_fill"])),
        ))
    return np.array(rows, dtype=candles.dtype)


def preflight_pair(
    connector: str,
    trading_pair: str,
    interval: str = "1h",
    loader=None,
    min_usable_days: float = MIN_USABLE_DAYS,
    max_gap_pct: float = MAX_GAP_PCT,
    fine_interval: str = "5m",
) -> tuple:
    """Load candles for the study, preferring native bars at `interval`.

    Falls back to resampling `fine_interval` when the target interval is
    absent from the lake. Raises RuntimeError (with the audit rows embedded
    in the message) when usable days < `min_usable_days` or the gap fraction
    exceeds `max_gap_pct` — the notebook surfaces this as a preflight abort.

    Returns (candles, info) where info holds the audit rows and the source
    ("native" | "resampled_{fine_interval}").
    """
    if loader is None:
        from pmm_lab.data.mongo import MongoCandleLoader
        loader = MongoCandleLoader()

    audit_native = audit_pair(connector, trading_pair, interval, loader=loader)
    audit_fine = audit_pair(connector, trading_pair, fine_interval, loader=loader)

    if audit_native["bars"] > 0:
        candles = loader.load_range(
            DataQuery(connector=connector, trading_pair=trading_pair, interval=interval)
        )
        source = "native"
        chosen = audit_native
    elif audit_fine["bars"] > 0:
        fine = loader.load_range(
            DataQuery(connector=connector, trading_pair=trading_pair, interval=fine_interval)
        )
        candles = resample_candles(fine, fine_interval, interval)
        source = f"resampled_{fine_interval}"
        chosen = audit_fine
    else:
        raise RuntimeError(
            f"preflight ABORT: no candles in the lake for {connector} "
            f"{trading_pair} at {interval} or {fine_interval}.\n"
            f"audit[{interval}]: {audit_native}\n"
            f"audit[{fine_interval}]: {audit_fine}"
        )

    info = dict(
        source=source,
        audit_native=audit_native,
        audit_fine=audit_fine,
        chosen=chosen,
    )
    if chosen["days"] < min_usable_days:
        raise RuntimeError(
            f"preflight ABORT: {connector} {trading_pair} has "
            f"{chosen['days']:.1f} usable days (< {min_usable_days:.0f}d "
            f"required for the 3-fold walk-forward layout).\n{info}"
        )
    if chosen["gap_pct"] > max_gap_pct:
        raise RuntimeError(
            f"preflight ABORT: {connector} {trading_pair} gap_pct "
            f"{chosen['gap_pct']:.2f}% exceeds {max_gap_pct:.1f}%.\n{info}"
        )
    return candles, info
