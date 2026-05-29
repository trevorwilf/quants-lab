"""Phase 1 (audit 2026-05-29 §5.3 / §5.4) — lake builders for adjustment +
current-code-parity full-fold-preflight tests.

Small but real IEX-shaped lakes: daily bars over a span (raw and/or
split_adjusted), per-month minute bars for selected months, an asset master,
and an optional ``_ingestion/manifest.json``. Deterministic flat-ish OHLCV —
enough for the DQ report + universe builder + preflight to run.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from bowaka_common.marketdata import layout

from tests.fixtures.universe_fixture import write_lake_asset_master


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def write_daily(
    root: Path, symbol: str, start: _dt.date, end: _dt.date,
    *, feed: str = "iex", adjustment: str = "raw", close: float = 10.0,
) -> None:
    days = [d.date() for d in pd.bdate_range(start, end)]
    _write(
        layout.daily_bars_path(root, symbol, feed=feed, adjustment=adjustment),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(days),
                "timestamp": [
                    pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days
                ],
                "open": [close] * len(days), "high": [close * 1.05] * len(days),
                "low": [close * 0.95] * len(days), "close": [close] * len(days),
                "volume": [2_000_000] * len(days), "session_date": days,
            }
        ),
    )


def write_minute_month(
    root: Path, symbol: str, year: int, month: int,
    *, feed: str = "iex", adjustment: str = "raw", close: float = 10.05,
) -> None:
    first = _dt.date(year, month, 1)
    days = [d.date() for d in pd.bdate_range(first, first + _dt.timedelta(days=31))
            if d.month == month]
    rows = []
    for d in days:
        for i in range(60):
            ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
            rows.append({"symbol": symbol, "timestamp": ts, "open": close,
                         "high": close * 1.01, "low": close * 0.99,
                         "close": close, "volume": 5000.0})
    _write(
        layout.minute_bars_path(root, symbol, year, month, feed=feed, adjustment=adjustment),
        pd.DataFrame(rows),
    )


def write_manifest(root: Path, *, feed: str = "iex", adjustment: str = "raw") -> None:
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": feed, "adjustment": adjustment,
                    "dataset_hashes": {"lake": f"sha256:{adjustment}"}}),
        encoding="utf-8",
    )


def build_lake(
    root: Path,
    symbols: Sequence[str],
    *,
    daily_start: _dt.date,
    daily_end: _dt.date,
    minute_months: Iterable[tuple[int, int]],
    feed: str = "iex",
    adjustment: str = "raw",
    close: float = 10.0,
    manifest_adjustment: str | None = None,
) -> None:
    """Build an IEX-shaped lake.

    ``adjustment`` is the daily/minute partition adjustment written.
    ``minute_months`` is the set of ``(year, month)`` to write minute bars for —
    a month NOT listed has daily bars but no minute coverage. ``manifest_adjustment``
    (when set) writes ``_ingestion/manifest.json`` declaring that adjustment.
    """
    for symbol in symbols:
        write_daily(root, symbol, daily_start, daily_end,
                    feed=feed, adjustment=adjustment, close=close)
        for (year, month) in minute_months:
            # Minute bars are raw by lake convention (even SIP minute bars are
            # raw) and the lab's minute supplier always reads the raw partition,
            # so write minute bars raw regardless of the DAILY adjustment.
            write_minute_month(root, symbol, year, month,
                               feed=feed, adjustment="raw", close=close * 1.005)
    write_lake_asset_master(root, list(symbols))
    if manifest_adjustment is not None:
        write_manifest(root, feed=feed, adjustment=manifest_adjustment)
