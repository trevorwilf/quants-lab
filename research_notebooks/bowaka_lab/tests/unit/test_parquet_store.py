"""Phase 1: ParquetStore tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from bowaka_lab.data.parquet_store import ParquetStore, PathParts


def test_path_parts_path_layout():
    parts = PathParts({"vendor": "alpaca", "feed": "iex", "symbol": "RILY"})
    assert parts.as_path() == Path("vendor=alpaca/feed=iex/symbol=RILY")


def test_path_parts_rejects_empty_key():
    with pytest.raises(ValueError):
        PathParts({"": "x"})


def test_path_parts_rejects_path_separator_in_value():
    with pytest.raises(ValueError):
        PathParts({"k": "a/b"})


def test_round_trip(tmp_path):
    store = ParquetStore(tmp_path)
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    parts = PathParts({"vendor": "alpaca", "feed": "iex"})
    target = store.write(df, dataset="bars", parts=parts)
    assert target.exists()
    out = store.read("bars", parts)
    pd.testing.assert_frame_equal(out.reset_index(drop=True), df)


def test_write_overwrites_by_default(tmp_path):
    store = ParquetStore(tmp_path)
    parts = PathParts({"vendor": "alpaca"})
    store.write(pd.DataFrame({"a": [1]}), dataset="d", parts=parts)
    store.write(pd.DataFrame({"a": [2]}), dataset="d", parts=parts)
    out = store.read("d", parts)
    assert out["a"].tolist() == [2]


def test_write_no_overwrite_raises(tmp_path):
    store = ParquetStore(tmp_path)
    parts = PathParts({"vendor": "alpaca"})
    store.write(pd.DataFrame({"a": [1]}), dataset="d", parts=parts)
    with pytest.raises(FileExistsError):
        store.write(pd.DataFrame({"a": [2]}), dataset="d", parts=parts, overwrite=False)


def test_read_missing_raises(tmp_path):
    store = ParquetStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.read("missing", PathParts({"k": "v"}))


def test_partition_path_for_minute_bars(tmp_path):
    store = ParquetStore(tmp_path)
    parts = PathParts(
        {
            "vendor": "alpaca",
            "feed": "iex",
            "timeframe": "1m",
            "adjustment": "raw",
            "session_date": "2026-05-12",
            "symbol": "RILY",
        }
    )
    p = store.path_for("bars", parts, "part.parquet")
    assert "vendor=alpaca" in str(p)
    assert "feed=iex" in str(p)
    assert "session_date=2026-05-12" in str(p)
    assert "symbol=RILY" in str(p)
