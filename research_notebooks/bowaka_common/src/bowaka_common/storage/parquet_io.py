"""Loaders that read the partitioned Parquet layout produced by the
``db_tools/bowaka_backfill.ipynb`` notebook.

Keeping these in the library (not the notebook) preserves the rule that
``notebooks/`` is orchestration-only — and lets other downstream consumers
reuse the same loaders without copy-paste.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
import pyarrow.parquet as pq


def load_daily_bars_from_root(daily_root: Path | str) -> pd.DataFrame:
    """Load every ``symbol=*/part.parquet`` under ``daily_root`` into one DataFrame.

    ``daily_root`` should be the directory ending in ``adjustment=raw`` — see
    :func:`bowaka_lab.data.parquet_store.path_for` or
    ``db_tools/_backfill_lib.daily_root``. Missing root → empty DataFrame.

    Adds a ``session_date`` column derived from ``timestamp`` in
    America/New_York so callers don't have to compute it.
    """
    daily_root = Path(daily_root)
    if not daily_root.exists():
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    for symbol_dir in sorted(daily_root.glob("symbol=*")):
        f = symbol_dir / "part.parquet"
        if not f.exists():
            continue
        df = pq.ParquetFile(str(f)).read().to_pandas()
        if "symbol" not in df.columns:
            df["symbol"] = symbol_dir.name.split("=", 1)[1]
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    if "session_date" not in out.columns:
        out["session_date"] = pd.to_datetime(out["timestamp"]).dt.tz_convert("America/New_York").dt.date
    return out


class MinuteBarLoader:
    """Lazy loader that returns minute bars for a (trade_date, symbols) pair.

    Reads from a partitioned tree of ``session_date=.../symbol=X.parquet``
    files. Instances are callable so they can be passed straight to
    :class:`bowaka_lab.sim.portfolio_engine.BowakaPortfolioBacktester` as the
    ``minute_bars_for`` parameter.
    """

    def __init__(self, minute_root: Path | str):
        self.minute_root = Path(minute_root)

    def __call__(self, trade_date: date, symbols: Iterable[str]) -> pd.DataFrame:
        return self.load(trade_date, symbols)

    def load(self, trade_date: date, symbols: Iterable[str]) -> pd.DataFrame:
        session_dir = self.minute_root / f"session_date={trade_date.isoformat()}"
        if not session_dir.exists():
            return pd.DataFrame()
        frames: list[pd.DataFrame] = []
        for sym in symbols:
            f = session_dir / f"symbol={sym}.parquet"
            if not f.exists():
                continue
            frames.append(pq.ParquetFile(str(f)).read().to_pandas())
        if not frames:
            return pd.DataFrame()
        df = pd.concat(frames, ignore_index=True)
        if "session_date" not in df.columns:
            df["session_date"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("America/New_York").dt.date
        return df


def candidates_dict_to_source(by_signal_date: dict) -> Callable:
    """Convert a ``{signal_date: candidates_df}`` dict to a ``candidate_source``.

    Returns a callable suitable for
    :class:`bowaka_lab.sim.portfolio_engine.BowakaPortfolioBacktester`.
    Unknown signal_dates return an empty DataFrame so the backtester's main
    loop keeps running (just updates open positions, no new entries).
    """

    def source(signal_date: date) -> pd.DataFrame:
        return by_signal_date.get(signal_date, pd.DataFrame())

    return source
