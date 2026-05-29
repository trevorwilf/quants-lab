"""Production-side normalizer reads ``trades.parquet`` + canonicalizes fields."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.parity.normalizers import (
    _normalize_production_trades_df,
    normalize_production_output,
)


def _trades_df() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "session_date": "2026-05-19",
            "symbol": "AAA",
            "entry_ts": "2026-05-19T14:30:25Z",
            "entry_price": 10.50,
            "qty": 100,
            "exit_ts": "2026-05-19T15:00:10Z",
            "exit_price": 11.00,
            "exit_reason": "TARGET",
            "pnl_dollars": 50.0,
        },
        {
            "session_date": "2026-05-19",
            "symbol": "BBB",
            "entry_ts": "2026-05-19T14:31:00Z",
            "entry_price": 5.0,
            "qty": 200,
            "exit_ts": None,
            "exit_price": None,
            "exit_reason": "Signal-Fade Soft",
            "pnl_dollars": 0.0,
        },
    ])


def test_normalize_production_trades_df_canonicalizes_minute_and_reason() -> None:
    trades = _normalize_production_trades_df(_trades_df())
    assert len(trades) == 2
    aaa, bbb = trades[0], trades[1]
    assert aaa.session_date == _dt.date(2026, 5, 19)
    assert aaa.entry_ts_minute == _dt.datetime(2026, 5, 19, 14, 30, tzinfo=_dt.UTC)
    assert aaa.exit_ts_minute == _dt.datetime(2026, 5, 19, 15, 0, tzinfo=_dt.UTC)
    assert aaa.exit_reason == "target"
    assert aaa.qty_filled == 100
    # Whitespace + camelcase + dash all normalize to snake_case.
    assert bbb.exit_reason == "signal_fade_soft"
    assert bbb.exit_ts_minute is None
    assert bbb.exit_price is None


def test_normalize_production_output_reads_parquet(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "prod_out"
    out_dir.mkdir()
    _trades_df().to_parquet(out_dir / "trades.parquet")

    @dataclass
    class _Result:
        trades_path: Path

    trades, cands = normalize_production_output(_Result(trades_path=out_dir / "trades.parquet"))
    assert len(trades) == 2
    assert cands == []  # production doesn't emit candidate telemetry


def test_normalize_production_output_handles_missing_file(tmp_path: Path) -> None:

    @dataclass
    class _Result:
        trades_path: Path

    trades, cands = normalize_production_output(_Result(trades_path=tmp_path / "missing.parquet"))
    assert trades == []
    assert cands == []


def test_normalize_production_output_falls_back_to_parquet_when_path_is_json(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    out_dir = tmp_path / "prod_out"
    out_dir.mkdir()
    _trades_df().to_parquet(out_dir / "trades.parquet")

    @dataclass
    class _Result:
        trades_path: Path

    # An older mirror path that has trades.json next to (missing) trades.parquet
    # should silently fall through to the parquet.
    trades, _ = normalize_production_output(_Result(trades_path=out_dir / "trades.json"))
    assert len(trades) == 2
