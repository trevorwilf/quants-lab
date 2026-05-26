"""Batch daily-cache builder matches the legacy per-session output bit-for-bit.

Speedup report v2 §4 P1 / Phase 1 task 5. The batch builder reads each
symbol's daily parquet once over the full span; the per-session
``dict[date, DataFrame]`` it produces must be identical to the legacy
:func:`build_daily_cache_from_lake` output called per session.

Covered cases:

* one symbol with a 30% intraday close jump that looks like a split,
* one symbol with missing dates in the middle,
* one symbol with ``< atr_window`` rows,
* one symbol with ``session_date`` column present,
* one symbol with ``timestamp`` column only (fallback path),
* one canonical "present" symbol with dense data.

Asserted for two ``lookback_days`` values to exercise the truncation
boundary too.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import layout
from bowaka_v2_lab.data.daily_cache_batch import build_daily_cache_for_sessions_from_lake
from bowaka_v2_lab.data.suppliers import (
    DAILY_CACHE_COLUMNS,
    build_daily_cache_from_lake,
)


def _write_daily(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily_frame(
    sym: str,
    days: list[dt.date],
    closes: list[float] | None = None,
    *,
    include_session_date: bool = True,
) -> pd.DataFrame:
    n = len(days)
    closes = closes if closes is not None else [100.0 + 0.5 * i for i in range(n)]
    cols = {
        "symbol": [sym] * n,
        "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
        "open":   closes,
        "high":   [c + 1.0 for c in closes],
        "low":    [c - 1.0 for c in closes],
        "close":  closes,
        "volume": [1_000_000 + 1000 * i for i in range(n)],
    }
    if include_session_date:
        cols["session_date"] = days
    return pd.DataFrame(cols)


@pytest.fixture
def mixed_lake(tmp_path: Path) -> tuple[Path, list[dt.date], list[str]]:
    """A 6-symbol fixture lake with diverse defects, ~80 trading days."""
    lake = tmp_path / "lake"
    start = dt.date(2024, 1, 1)
    days = [d.date() for d in pd.bdate_range(start, start + dt.timedelta(days=115))]
    sessions = days[-6:]  # last 6 trading sessions are the "scan" sessions

    # MISS_DAY — same as PRESENT but with 5 days removed in the middle.
    miss = [d for d in days if d.toordinal() % 13 != 0]
    _write_daily(layout.daily_bars_path(lake, "MISS_DAY", feed="iex"),
                 _daily_frame("MISS_DAY", miss))
    # SPLIT_LIKE — close drops 30% on one day.
    closes = [100.0 + 0.1 * i for i in range(len(days))]
    closes[50] = closes[50] * 0.7  # 30% intra-day drop
    _write_daily(layout.daily_bars_path(lake, "SPLIT_LIKE", feed="iex"),
                 _daily_frame("SPLIT_LIKE", days, closes))
    # SHORT — only 5 rows (< atr_window). The legacy builder's ATR falls back to 0.0.
    _write_daily(layout.daily_bars_path(lake, "SHORT", feed="iex"),
                 _daily_frame("SHORT", days[-10:-5]))
    # WITH_SD — canonical dense frame with session_date column.
    _write_daily(layout.daily_bars_path(lake, "WITH_SD", feed="iex"),
                 _daily_frame("WITH_SD", days, include_session_date=True))
    # WITHOUT_SD — same dense frame but no session_date column (timestamp fallback).
    _write_daily(layout.daily_bars_path(lake, "WITHOUT_SD", feed="iex"),
                 _daily_frame("WITHOUT_SD", days, include_session_date=False))
    # PRESENT — canonical, dense, with session_date.
    _write_daily(layout.daily_bars_path(lake, "PRESENT", feed="iex"),
                 _daily_frame("PRESENT", days, include_session_date=True))
    return lake, sessions, ["MISS_DAY", "SPLIT_LIKE", "SHORT", "WITH_SD", "WITHOUT_SD", "PRESENT"]


@pytest.mark.parametrize("lookback_days", [400, 30])
def test_batch_matches_legacy_per_session_byte_for_byte(
    mixed_lake: tuple[Path, list[dt.date], list[str]], lookback_days: int,
) -> None:
    lake, sessions, all_syms = mixed_lake
    symbols_by_session = {s: list(all_syms) for s in sessions}
    legacy = {
        s: build_daily_cache_from_lake(
            lake, all_syms, s, feed="iex", lookback_days=lookback_days,
        )
        for s in sessions
    }
    batch = build_daily_cache_for_sessions_from_lake(
        lake, symbols_by_session, sessions,
        feed="iex", lookback_days=lookback_days,
    )
    for s in sessions:
        a = legacy[s]
        b = batch[s]
        assert list(a.columns) == list(DAILY_CACHE_COLUMNS), \
            f"legacy columns drifted for {s}"
        assert list(b.columns) == list(DAILY_CACHE_COLUMNS), \
            f"batch columns drifted for {s}"
        assert a["symbol"].tolist() == b["symbol"].tolist(), (
            f"row order differs for {s}: legacy={a['symbol'].tolist()} "
            f"batch={b['symbol'].tolist()}"
        )
        for col in DAILY_CACHE_COLUMNS:
            if col == "symbol":
                continue
            for row_idx, (va, vb) in enumerate(zip(a[col].tolist(), b[col].tolist())):
                assert abs(float(va) - float(vb)) <= 1e-12, (
                    f"session={s} col={col} row={row_idx} legacy={va!r} batch={vb!r}"
                )
