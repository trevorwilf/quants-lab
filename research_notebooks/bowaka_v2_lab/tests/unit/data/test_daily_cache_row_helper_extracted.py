"""``_daily_cache_row_from_prior`` is shared between legacy + batch builders.

Speedup report v2 §4 P1 / §5.3 / Phase 1 task 1. The extracted helper carries
the per-symbol row math (ATR, EMA, rolling means) that both
:func:`build_daily_cache_from_lake` and
:func:`build_daily_cache_for_sessions_from_lake` consume. After the
extraction refactor the legacy builder's output is unchanged (every
DataFrame row equal to the helper output).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.suppliers import (
    DAILY_CACHE_COLUMNS,
    _daily_cache_row_from_prior,
    build_daily_cache_from_lake,
)


def _make_prior(n_rows: int) -> pd.DataFrame:
    """Build a synthetic ``prior`` DataFrame (already filtered + sorted)."""
    days = [dt.date(2024, 1, 1) + dt.timedelta(days=i) for i in range(n_rows)]
    return pd.DataFrame({
        "_sd": days,
        "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
        "open":   [100.0 + 0.5 * i for i in range(n_rows)],
        "high":   [101.0 + 0.5 * i for i in range(n_rows)],
        "low":    [ 99.0 + 0.5 * i for i in range(n_rows)],
        "close":  [100.5 + 0.5 * i for i in range(n_rows)],
        "volume": [1_000_000 + 1000 * i for i in range(n_rows)],
    })


def test_helper_row_has_canonical_keys() -> None:
    prior = _make_prior(25)
    row = _daily_cache_row_from_prior(
        "ABC", prior, atr_window=14, vol_window=20, ema_span=10,
    )
    # Every column in DAILY_CACHE_COLUMNS must be present (same key set).
    assert set(row.keys()) == set(DAILY_CACHE_COLUMNS)
    assert row["symbol"] == "ABC"
    assert isinstance(row["ema_10_prior"], float)


def test_helper_row_ema_lag3_fallback_when_short_prior() -> None:
    """When ``len(prior) < 4`` ``ema_10_lag_3`` falls back to ``ema_10_prior``."""
    prior = _make_prior(3)  # len < 4 → triggers the lag-3 fallback
    row = _daily_cache_row_from_prior(
        "FB", prior, atr_window=14, vol_window=20, ema_span=10,
    )
    assert row["ema_10_lag_3"] == row["ema_10_prior"]
    assert row["ema_slope_prior"] == 0.0


def test_helper_row_atr_fallback_when_shorter_than_window() -> None:
    """When the ATR window is longer than ``prior``, the helper falls back to 0.0."""
    prior = _make_prior(5)  # rolling(14).mean() at row 5 = NaN → 0.0 fallback
    row = _daily_cache_row_from_prior(
        "XX", prior, atr_window=14, vol_window=20, ema_span=10,
    )
    assert row["prior_atr_14d"] == 0.0
    assert row["prior_atr_pct"] == 0.0


def test_legacy_builder_produces_helper_output_byte_for_byte(tmp_path: Path) -> None:
    """A fixture lake with one symbol — legacy builder's single row matches the helper."""
    sym = "ABC"
    session = dt.date(2024, 4, 1)
    # 81 days back so ATR(14) is well-populated.
    days = [session - dt.timedelta(days=i) for i in range(81, 0, -1)]
    daily_path = layout.daily_bars_path(tmp_path, sym, feed="iex")
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "symbol": [sym] * len(days),
        "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
        "open":   [100.0 + 0.5 * i for i in range(len(days))],
        "high":   [101.0 + 0.5 * i for i in range(len(days))],
        "low":    [ 99.0 + 0.5 * i for i in range(len(days))],
        "close":  [100.5 + 0.5 * i for i in range(len(days))],
        "volume": [1_000_000 + 1000 * i for i in range(len(days))],
        "session_date": days,
    }).to_parquet(daily_path, index=False)

    legacy_df = build_daily_cache_from_lake(tmp_path, [sym], session, feed="iex")
    assert len(legacy_df) == 1, "fixture should yield exactly one row"
    legacy_row = legacy_df.iloc[0].to_dict()

    # Rebuild the helper-equivalent ``prior`` from the same source data so we
    # can compare values bit-for-bit.
    raw = pd.read_parquet(daily_path)
    raw["_sd"] = pd.to_datetime(raw["session_date"]).dt.date
    prior = raw[raw["_sd"] < session].sort_values("_sd").reset_index(drop=True)
    helper_row = _daily_cache_row_from_prior(
        sym, prior, atr_window=14, vol_window=20, ema_span=10,
    )

    for k in DAILY_CACHE_COLUMNS:
        a, b = legacy_row[k], helper_row[k]
        if isinstance(a, float):
            assert abs(float(a) - float(b)) <= 1e-12, (
                f"{k}: legacy={a!r} helper={b!r}"
            )
        else:
            assert a == b, f"{k}: legacy={a!r} helper={b!r}"
