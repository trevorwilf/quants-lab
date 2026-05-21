"""run_backtest end-to-end against a synthetic shared-lake fixture.

Proves the Phase-4 wiring: lake-backed suppliers + daily cache feed the v2
backtester through to the full artifact contract.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def test_run_backtest_reads_the_shared_lake(tmp_path, lab_root):
    lake = tmp_path / "lake"
    symbol = "AAA"
    session = dt.date(2024, 9, 4)

    # 80 daily warmup sessions ending the day before `session`
    ddates = [session - dt.timedelta(days=i) for i in range(80, 0, -1)]
    _write(
        layout.daily_bars_path(lake, symbol),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(ddates),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
                "open": [100.0] * len(ddates),
                "high": [101.0] * len(ddates),
                "low": [99.0] * len(ddates),
                "close": [100.0] * len(ddates),
                "volume": [1_000_000] * len(ddates),
                "session_date": ddates,
            }
        ),
    )
    # minute bars across the session
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    _write(
        layout.minute_bars_path(lake, symbol, 2024, 9),
        pd.DataFrame(
            {
                "symbol": [symbol] * 60,
                "timestamp": mts,
                "open": [100.0] * 60,
                "high": [101.0] * 60,
                "low": [99.0] * 60,
                "close": [100.5] * 60,
                "volume": [5000.0] * 60,
            }
        ),
    )

    cfg = load_config(lab_root / "configs" / "bowaka_v2_backtest_smoke.yml")
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = {session: synthetic_universe([symbol])}

    result = run_backtest(
        cfg=cfg,
        sessions=[session],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0,
        paths=paths,
        run_dir=tmp_path / "run",
    )

    # the backtest completed and wrote its artifact contract from lake data
    assert result.run_dir.is_dir()
    assert (result.run_dir / "summary.json").is_file()
    # the lake-backed daily cache was non-empty (real warmup bars were read)
    assert not daily_cache[session].empty
    assert daily_cache[session].iloc[0]["prior_close"] == 100.0
