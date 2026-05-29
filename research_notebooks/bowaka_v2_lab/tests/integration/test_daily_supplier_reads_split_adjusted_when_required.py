"""Phase 1 (audit 2026-05-29 §5.2 / §5.3) — daily reader honours the config.

A lake with BOTH a raw (close=100) and a split_adjusted (close=10) daily
partition for the same symbol. With ``market_data.require_split_adjustment:
true`` the lab's cfg-aware daily reader (the PIT-universe builder) MUST read
the split_adjusted partition (prior_close=10), NOT the store default raw
(prior_close=100). This test FAILS on the pre-Phase-1 path (which ignored the
config and always read raw).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.universe.builder import (
    _pit_daily_history_cache_clear,
    build_pit_universe,
)
from tests.fixtures.universe_fixture import write_lake_asset_master


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily_frame(symbol: str, session: dt.date, close: float) -> pd.DataFrame:
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(ddates),
            "timestamp": [
                pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates
            ],
            "open": [close] * len(ddates), "high": [close * 1.01] * len(ddates),
            "low": [close * 0.99] * len(ddates), "close": [close] * len(ddates),
            "volume": [1_000_000] * len(ddates), "session_date": ddates,
        }
    )


def test_pit_universe_reads_split_adjusted_when_required(tmp_path: Path) -> None:
    _pit_daily_history_cache_clear()
    symbol, session = "AAAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    # raw partition: close=100; split_adjusted partition: close=10.
    _write(
        layout.daily_bars_path(lake, symbol, feed="iex", adjustment="raw"),
        _daily_frame(symbol, session, 100.0),
    )
    _write(
        layout.daily_bars_path(lake, symbol, feed="iex", adjustment="split_adjusted"),
        _daily_frame(symbol, session, 10.0),
    )
    write_lake_asset_master(lake, [symbol])

    cfg = {
        "market_data": {"feed": "iex", "shared_root": str(lake),
                        "require_split_adjustment": True},
        "simulation": {"mode": "current_code_parity"},
        "universe": {"min_price": 1.0, "max_price": 1_000.0, "min_adv_dollars": 0},
    }
    universe = build_pit_universe(session, cfg, MarketDataStore(lake))
    assert symbol in universe
    # Reads the split_adjusted close (10.0), not the raw default (100.0).
    assert universe[symbol].prior_close == 10.0
    _pit_daily_history_cache_clear()


def test_pit_universe_reads_raw_by_default(tmp_path: Path) -> None:
    """Control: with no adjustment requirement, the default raw partition wins."""
    _pit_daily_history_cache_clear()
    symbol, session = "BBBB", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _write(
        layout.daily_bars_path(lake, symbol, feed="iex", adjustment="raw"),
        _daily_frame(symbol, session, 100.0),
    )
    _write(
        layout.daily_bars_path(lake, symbol, feed="iex", adjustment="split_adjusted"),
        _daily_frame(symbol, session, 10.0),
    )
    write_lake_asset_master(lake, [symbol])
    cfg = {
        "market_data": {"feed": "iex", "shared_root": str(lake)},
        "simulation": {"mode": "current_code_parity"},
        "universe": {"min_price": 1.0, "max_price": 1_000.0, "min_adv_dollars": 0},
    }
    universe = build_pit_universe(session, cfg, MarketDataStore(lake))
    assert universe[symbol].prior_close == 100.0
    _pit_daily_history_cache_clear()
