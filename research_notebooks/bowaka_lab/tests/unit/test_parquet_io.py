"""Tests for the on-disk Parquet loaders used by the run_backtest notebook."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bowaka_lab.data.parquet_io import (
    MinuteBarLoader,
    candidates_dict_to_source,
    load_daily_bars_from_root,
)


def _write_daily(root, symbol: str, sessions):
    target = root / f"symbol={symbol}" / "part.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for s in sessions:
        ts = pd.Timestamp(s).tz_localize("America/New_York") + pd.Timedelta(hours=16)
        rows.append(
            {
                "symbol": symbol,
                "timestamp": ts.tz_convert("UTC"),
                "open": 5.0,
                "high": 5.1,
                "low": 4.9,
                "close": 5.0,
                "volume": 1_000_000,
            }
        )
    pq.write_table(pa.Table.from_pandas(pd.DataFrame(rows), preserve_index=False), target)


def _write_minute(root, session, symbol: str):
    target = root / f"session_date={session.isoformat()}" / f"symbol={symbol}.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    minutes = pd.date_range(
        start=pd.Timestamp(session).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30),
        periods=10,
        freq="1min",
        tz="America/New_York",
    ).tz_convert("UTC")
    df = pd.DataFrame(
        {
            "symbol": symbol,
            "timestamp": minutes,
            "open": 5.0,
            "high": 5.1,
            "low": 4.9,
            "close": 5.0,
            "volume": 100,
        }
    )
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), target)


def test_load_daily_bars_from_root_returns_concatenated_frame(tmp_path):
    _write_daily(tmp_path, "AAA", [date(2025, 1, 6), date(2025, 1, 7)])
    _write_daily(tmp_path, "BBB", [date(2025, 1, 6)])
    df = load_daily_bars_from_root(tmp_path)
    assert df.shape[0] == 3
    assert set(df["symbol"]) == {"AAA", "BBB"}
    assert "session_date" in df.columns


def test_load_daily_bars_from_root_missing_returns_empty(tmp_path):
    df = load_daily_bars_from_root(tmp_path / "missing")
    assert df.empty


def test_load_daily_bars_from_root_empty_when_no_symbol_dirs(tmp_path):
    df = load_daily_bars_from_root(tmp_path)
    assert df.empty


def test_minute_bar_loader_returns_only_requested_symbols(tmp_path):
    sd = date(2026, 5, 12)
    for sym in ("AAA", "BBB", "CCC"):
        _write_minute(tmp_path, sd, sym)
    loader = MinuteBarLoader(tmp_path)
    df = loader(sd, ["AAA", "BBB"])
    assert set(df["symbol"]) == {"AAA", "BBB"}


def test_minute_bar_loader_unknown_session_returns_empty(tmp_path):
    loader = MinuteBarLoader(tmp_path)
    df = loader(date(2025, 1, 1), ["AAA"])
    assert df.empty


def test_minute_bar_loader_unknown_symbol_skipped(tmp_path):
    sd = date(2026, 5, 12)
    _write_minute(tmp_path, sd, "AAA")
    loader = MinuteBarLoader(tmp_path)
    df = loader(sd, ["AAA", "NOPE"])
    assert set(df["symbol"]) == {"AAA"}


def test_candidates_dict_to_source_round_trip():
    payload = pd.DataFrame([{"symbol": "AAA", "rank": 1}])
    src = candidates_dict_to_source({date(2026, 5, 11): payload})
    out = src(date(2026, 5, 11))
    assert out.equals(payload)
    # Missing signal_date → empty DF, never raises.
    assert src(date(2099, 1, 1)).empty
