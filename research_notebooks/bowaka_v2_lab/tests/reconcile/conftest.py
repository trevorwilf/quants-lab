"""Shared fixtures for the Phase-10 reconciliation tests.

Builds a tiny synthetic market-data lake (daily + minute bars + an asset
master) and a ``current_code_parity`` lab config pointed at it, so the
paper-vs-lab replay path can run end-to-end without real lake data or network.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd
import pytest
import yaml

from bowaka_common.marketdata import layout
from tests.fixtures.universe_fixture import write_lake_asset_master

#: The frozen synthetic-paper-log fixture session.
SYNTHETIC_SESSION = _dt.date(2024, 9, 4)
SYNTHETIC_SYMBOLS = ("AAA", "BBB")
#: Where the frozen synthetic paper logs live.
PAPER_LOGS_SYNTHETIC = (
    Path(__file__).resolve().parents[1] / "fixtures" / "paper_logs_synthetic"
)


def _build_tiny_lake(lake: Path, symbols: tuple[str, ...]) -> None:
    """Daily + intraday minute bars + an asset master for a tiny lake.

    Daily bars span June-Sept 2024 (enough prior history for the PIT universe
    + the daily-feature cache); minute bars cover the full regular session so
    the intraday scan cadence has bars at every scan timestamp.
    """
    start, end = _dt.date(2024, 6, 1), _dt.date(2024, 9, 6)
    days = [d.date() for d in pd.bdate_range(start, end)]
    for sym in symbols:
        dpath = layout.daily_bars_path(lake, sym, feed="iex")
        dpath.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "symbol": [sym] * len(days),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
                "open": [10.0] * len(days), "high": [10.2] * len(days),
                "low": [9.8] * len(days), "close": [10.0] * len(days),
                "volume": [1_000_000] * len(days), "session_date": days,
            }
        ).to_parquet(dpath, index=False)
        by_month: dict[tuple[int, int], list] = {}
        for d in days:
            for i in range(390):  # full 09:30-16:00 regular session
                ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
                by_month.setdefault((d.year, d.month), []).append(
                    {"symbol": sym, "timestamp": ts, "open": 10.0, "high": 10.3,
                     "low": 9.9, "close": 10.15, "volume": 5000.0}
                )
        for (year, month), rows in by_month.items():
            mpath = layout.minute_bars_path(lake, sym, year, month, feed="iex")
            mpath.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_parquet(mpath, index=False)
    write_lake_asset_master(lake, list(symbols))


@pytest.fixture
def parity_lake_config(tmp_path: Path, lab_root: Path) -> dict:
    """A ``current_code_parity``-ready lab config over a tiny synthetic lake.

    The returned config dict points the bar feeds at a freshly built tiny lake
    and pins the universe / dates so the lab replays exactly the synthetic
    paper-log session. Lab paths are redirected under ``tmp_path`` (the
    directory name keeps ``bowaka_v2_lab`` so ``assert_strategy_isolation``
    passes).
    """
    lake = tmp_path / "lake"
    _build_tiny_lake(lake, SYNTHETIC_SYMBOLS)

    raw = yaml.safe_load(
        (lab_root / "configs" / "bowaka_v2_backtest_smoke.yml").read_text(encoding="utf-8")
    )
    raw["market_data"]["minute_bar_source"] = "alpaca"
    raw["market_data"]["daily_bar_source"] = "alpaca"
    raw["market_data"]["feed"] = "iex"
    raw["market_data"]["shared_root"] = str(lake)
    raw["universe"]["symbols"] = list(SYNTHETIC_SYMBOLS)
    raw["backtest"]["start_date"] = SYNTHETIC_SESSION.isoformat()
    raw["backtest"]["end_date"] = SYNTHETIC_SESSION.isoformat()
    tmp_lab = tmp_path / "bowaka_v2_lab"
    raw["paths"] = {
        "lab_root": str(tmp_lab),
        "data_root": str(tmp_lab / "data"),
        "artifact_root": str(tmp_lab / "artifacts"),
    }
    return raw
