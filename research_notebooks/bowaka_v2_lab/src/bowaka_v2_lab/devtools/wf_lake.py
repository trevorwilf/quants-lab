"""Tiny synthetic market-data lake builder for walk-forward Optuna tests.

A real walk-forward study is ``n_trials x n_folds`` real backtests; the test
suite needs a *small* but real lake so the study path can be exercised
end-to-end without minutes of compute. :func:`build_tiny_lake` writes daily +
per-month minute parquet partitions for a handful of symbols;
:func:`write_walkforward_test_config` derives a small in-memory-storage
walk-forward config from a real one.

This lives in ``devtools`` (not ``tests/``) so every test module can import it
through the package — sibling-test imports are fragile under pytest's default
``prepend`` import mode.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml

from bowaka_common.marketdata import layout


def build_tiny_lake(
    lake: Path,
    symbols: Iterable[str],
    *,
    start: _dt.date,
    end: _dt.date,
    feed: str = "iex",
) -> None:
    """Write daily bars over ``[start, end]`` plus per-month minute bars per symbol.

    The bars are deterministic flat-ish OHLCV — enough for the backtester and the
    walk-forward objective to run, not enough to be a research dataset.
    """
    for sym in symbols:
        days = [d.date() for d in pd.bdate_range(start, end)]
        dpath = layout.daily_bars_path(lake, sym, feed=feed)
        dpath.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "symbol": [sym] * len(days),
                "timestamp": [
                    pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days
                ],
                "open": [100.0] * len(days), "high": [101.0] * len(days),
                "low": [99.0] * len(days), "close": [100.0] * len(days),
                "volume": [1_000_000] * len(days), "session_date": days,
            }
        ).to_parquet(dpath, index=False)
        by_month: dict[tuple[int, int], list] = {}
        for d in days:
            for i in range(30):
                ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
                by_month.setdefault((d.year, d.month), []).append(
                    {"symbol": sym, "timestamp": ts, "open": 100.0, "high": 101.0,
                     "low": 99.0, "close": 100.5, "volume": 5000.0}
                )
        for (year, month), rows in by_month.items():
            mpath = layout.minute_bars_path(lake, sym, year, month, feed=feed)
            mpath.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_parquet(mpath, index=False)


def write_walkforward_test_config(
    base_config_path: Path,
    out_path: Path,
    *,
    lake: Path,
    symbols: Iterable[str],
    start: _dt.date,
    end: _dt.date,
    n_trials: int = 2,
) -> Path:
    """Derive a small, in-memory-storage walk-forward config from a real one.

    Pins the date range, the tiny-lake root and the IEX feed, redirects the lab
    paths into the tmp area, and drops the Optuna storage URI so the study runs
    against an in-memory Optuna study (no SQLite file).
    """
    raw = yaml.safe_load(Path(base_config_path).read_text(encoding="utf-8"))
    raw["backtest"]["start_date"] = start.isoformat()
    raw["backtest"]["end_date"] = end.isoformat()
    raw["market_data"]["shared_root"] = str(lake)
    raw["market_data"]["feed"] = "iex"  # pin to match build_tiny_lake's feed
    raw.setdefault("universe", {})["symbols"] = list(symbols)
    raw["optuna"]["n_trials"] = n_trials
    raw["optuna"]["n_jobs"] = 1
    raw["optuna"]["walkforward"] = {
        "train_months": 1, "val_months": 1, "final_holdout_months": 1,
    }
    raw["optuna"].pop("storage", None)  # -> in-memory Optuna study
    tmp_lab = Path(out_path).parent / "bowaka_v2_lab"
    raw["paths"] = {
        "lab_root": str(tmp_lab),
        "data_root": str(tmp_lab / "data"),
        "artifact_root": str(tmp_lab / "artifacts"),
    }
    Path(out_path).write_text(yaml.safe_dump(raw), encoding="utf-8")
    return Path(out_path)


__all__ = ["build_tiny_lake", "write_walkforward_test_config"]
