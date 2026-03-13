"""Candle canonicalization and validation."""

from collections import Counter

import numpy as np

from pmm_lab.config.defaults import (
    INTERVAL_SECONDS,
    MAX_DUPLICATE_FRACTION,
    MAX_OHLC_VIOLATION_FRACTION,
)
from pmm_lab.config.params import AuditResult
from pmm_lab.data.hashing import hash_candles


def validate_candles(
    candles: np.ndarray, interval: str, strict: bool = True
) -> AuditResult:
    """Validate a canonical candle array and return an AuditResult.

    Checks performed:
    1. Monotonic timestamps (strictly increasing).
    2. No duplicate timestamps.
    3. OHLC sanity:
       a. high >= max(open, close) for every row
       b. low <= min(open, close) for every row
       c. All OHLC values > 0
       d. high >= low
    4. Volume >= 0.
    5. Gap analysis: histogram of gaps between consecutive timestamps.
    6. Expected row count based on (last_ts - first_ts) / interval_seconds + 1.

    Parameters
    ----------
    candles : np.ndarray
        Canonical structured candle array.
    interval : str
        Candle interval (e.g. '5m').
    strict : bool
        If True, apply strict failure criteria.

    Returns
    -------
    AuditResult
    """
    interval_sec = INTERVAL_SECONDS[interval]
    n = len(candles)

    if n == 0:
        return AuditResult(
            total_rows=0,
            first_timestamp=0,
            last_timestamp=0,
            expected_rows=0,
            missing_rows=0,
            duplicate_count=0,
            null_counts={},
            ohlc_violations=0,
            ohlc_violation_details={},
            volume_zero_count=0,
            volume_zero_fraction=0.0,
            dataset_hash="",
            interval_seconds=interval_sec,
            gap_histogram={},
            longest_gap_seconds=0,
            passed_strict=False,
            failure_reasons=["Empty candle array"],
        )

    ts = candles["timestamp"]
    o = candles["open"]
    h = candles["high"]
    lo = candles["low"]
    c = candles["close"]
    v = candles["volume"]

    failure_reasons = []

    # --- Duplicates ---
    unique_ts, counts = np.unique(ts, return_counts=True)
    duplicate_count = int(np.sum(counts[counts > 1] - 1))

    # --- Monotonicity check ---
    if n > 1:
        ts_diffs = np.diff(ts)
        non_monotonic_count = int(np.sum(ts_diffs <= 0))
        if non_monotonic_count > 0 and strict:
            failure_reasons.append(
                f"Timestamps are not strictly monotonic: {non_monotonic_count} non-increasing gaps"
            )
    else:
        non_monotonic_count = 0

    # --- OHLC violations ---
    violation_details: dict[str, int] = {}

    high_lt_open_close = h < np.maximum(o, c)
    n_high_violation = int(np.sum(high_lt_open_close))
    if n_high_violation > 0:
        violation_details["high < max(open, close)"] = n_high_violation

    low_gt_open_close = lo > np.minimum(o, c)
    n_low_violation = int(np.sum(low_gt_open_close))
    if n_low_violation > 0:
        violation_details["low > min(open, close)"] = n_low_violation

    non_positive = (o <= 0) | (h <= 0) | (lo <= 0) | (c <= 0)
    n_non_positive = int(np.sum(non_positive))
    if n_non_positive > 0:
        violation_details["non-positive OHLC"] = n_non_positive

    high_lt_low = h < lo
    n_high_lt_low = int(np.sum(high_lt_low))
    if n_high_lt_low > 0:
        violation_details["high < low"] = n_high_lt_low

    ohlc_violations = n_high_violation + n_low_violation + n_non_positive + n_high_lt_low

    # --- Null counts (for structured arrays, check for NaN in float fields) ---
    null_counts = {}
    for field_name in ("open", "high", "low", "close", "volume"):
        nan_count = int(np.sum(np.isnan(candles[field_name])))
        if nan_count > 0:
            null_counts[field_name] = nan_count

    # --- Volume zero ---
    volume_zero_count = int(np.sum(v == 0))
    volume_zero_fraction = volume_zero_count / n if n > 0 else 0.0

    # --- Gap analysis ---
    if n > 1:
        diffs = np.diff(ts)
        gap_counter = Counter(int(d) for d in diffs)
        gap_histogram = dict(gap_counter)
        longest_gap = int(np.max(diffs))
    else:
        gap_histogram = {}
        longest_gap = 0

    # --- Expected rows ---
    first_ts = int(ts[0])
    last_ts = int(ts[-1])
    expected_rows = (last_ts - first_ts) // interval_sec + 1
    missing_rows = max(0, expected_rows - n)

    # --- Dataset hash ---
    dataset_hash = hash_candles(candles)

    # --- Strict checks ---
    if strict:
        if n > 0 and ohlc_violations / n > MAX_OHLC_VIOLATION_FRACTION:
            failure_reasons.append(
                f"OHLC violation fraction {ohlc_violations / n:.4f} exceeds threshold {MAX_OHLC_VIOLATION_FRACTION}"
            )
        if n_non_positive > 0:
            failure_reasons.append(
                f"non-positive OHLC values found: {n_non_positive} rows"
            )
        if duplicate_count > 0:
            failure_reasons.append(
                f"duplicate timestamps found: {duplicate_count}"
            )

    return AuditResult(
        total_rows=n,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        expected_rows=expected_rows,
        missing_rows=missing_rows,
        duplicate_count=duplicate_count,
        null_counts=null_counts,
        ohlc_violations=ohlc_violations,
        ohlc_violation_details=violation_details,
        volume_zero_count=volume_zero_count,
        volume_zero_fraction=volume_zero_fraction,
        dataset_hash=dataset_hash,
        interval_seconds=interval_sec,
        gap_histogram=gap_histogram,
        longest_gap_seconds=longest_gap,
        passed_strict=len(failure_reasons) == 0,
        failure_reasons=failure_reasons,
    )
