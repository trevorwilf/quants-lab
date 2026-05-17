"""Tests for the ``bowaka_lab.utils.io.to_parquet_safe`` helper."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import pytest

from bowaka_lab.utils.io import to_parquet_safe


def test_writes_plain_dataframe_unchanged(tmp_path: Path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    out_path = tmp_path / "plain.parquet"
    to_parquet_safe(df, out_path)
    assert out_path.exists()
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    pd.testing.assert_frame_equal(read, df)


def test_empty_dict_column_serialized(tmp_path: Path):
    """The exact failure mode the operator hit: an all-{} dict column."""
    df = pd.DataFrame({"trade_id": ["t1", "t2"], "diagnostics": [{}, {}]})
    out_path = tmp_path / "diag.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    assert list(read["diagnostics"]) == ["{}", "{}"]


def test_mixed_dict_column_serialized(tmp_path: Path):
    df = pd.DataFrame(
        {"trade_id": ["t1", "t2"], "diagnostics": [{}, {"reason": "stop_first"}]}
    )
    out_path = tmp_path / "mixed.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    decoded = [json.loads(v) for v in read["diagnostics"]]
    assert decoded == [{}, {"reason": "stop_first"}]


def test_list_column_serialized(tmp_path: Path):
    df = pd.DataFrame({"sym": ["AAA"], "rejection_reasons": [["price_min", "rvol_min"]]})
    out_path = tmp_path / "lists.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    assert json.loads(read["rejection_reasons"].iloc[0]) == ["price_min", "rvol_min"]


def test_purely_none_column_passes_through(tmp_path: Path):
    df = pd.DataFrame({"a": [1, 2], "b": [None, None]})
    out_path = tmp_path / "nones.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    assert read.shape == (2, 2)


def test_creates_parent_dirs(tmp_path: Path):
    df = pd.DataFrame({"a": [1]})
    out_path = tmp_path / "a" / "b" / "c.parquet"
    to_parquet_safe(df, out_path)
    assert out_path.exists()


def test_round_trip_via_json_load(tmp_path: Path):
    df = pd.DataFrame(
        {"sym": ["AAA"], "diagnostics": [{"bar_open": 5.04, "stop": 4.6}]}
    )
    out_path = tmp_path / "rt.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    decoded = json.loads(read["diagnostics"].iloc[0])
    assert decoded["bar_open"] == pytest.approx(5.04)
    assert decoded["stop"] == pytest.approx(4.6)


def test_simulates_backtester_trades_df_shape(tmp_path: Path):
    """Replicate the column mix the BowakaPortfolioBacktester emits."""
    df = pd.DataFrame(
        [
            {
                "trade_id": "bt_AAA_2026-05-12_fixed_time_0945_cfg_abc",
                "symbol": "AAA",
                "qty": 1000,
                "entry_price": 5.04,
                "exit_price": 5.79,
                "pnl": 750.0,
                "exit_reason": "target_hit",
                "ambiguous_bar": False,
                "diagnostics": {},
            }
        ]
    )
    out_path = tmp_path / "trades.parquet"
    to_parquet_safe(df, out_path)
    read = pq.ParquetFile(str(out_path)).read().to_pandas()
    assert read.shape == df.shape
    assert read["diagnostics"].iloc[0] == "{}"
