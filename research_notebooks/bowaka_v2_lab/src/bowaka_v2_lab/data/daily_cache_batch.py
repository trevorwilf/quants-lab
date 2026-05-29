"""Batch daily-feature cache builder (speedup report v2 §4 P1 / Phase 1).

The legacy :func:`bowaka_v2_lab.data.suppliers.build_daily_cache_from_lake`
calls ``MarketDataStore.daily_bars`` once per ``(symbol, session)`` pair, so a
fold of S sessions and N eligible symbols pays N * S parquet reads. The batch
builder reads each symbol's daily parquet **once** over the full
``[min(sessions) - lookback_days, max(sessions)]`` span and slices per
session in memory; N * S parquet reads collapse to N.

The per-session-row math is identical to the legacy path —
:func:`bowaka_v2_lab.data.suppliers._daily_cache_row_from_prior` is shared
between the two builders so the output is bit-for-bit equal (every per-session
``DataFrame`` is structurally and value-wise the same).

**EMA semantics.** The legacy path computes the EMA over the truncated
``prior`` (length ≤ ``lookback_days`` calendar days, i.e. the slice already
bounded by ``[session - lookback_days, session)``). The batch path mirrors
this exactly — EMA is computed INSIDE ``_daily_cache_row_from_prior`` on the
per-session slice, NOT once over the full symbol history. The 400-day
truncation is part of the strategy definition; the parity test
``test_batch_daily_cache_truncated_ema_parity`` enforces this.
"""
from __future__ import annotations

import datetime as _dt
import time as _time
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from bowaka_common.marketdata import MarketDataStore

from ..utils.profile_counters import counters_enabled, current_profile_counters
from .suppliers import (
    DAILY_CACHE_COLUMNS,
    _as_store,
    _daily_cache_row_from_prior,
)


def _count(**kwargs: Any) -> None:
    if not counters_enabled():
        return
    try:
        current_profile_counters().inc(**kwargs)
    except LookupError:
        pass


@dataclass(frozen=True)
class _DailySymbolFrame:
    """Cached full-span normalized daily frame for one symbol.

    ``df`` carries the original columns + an added ``_sd`` column (per-row
    session date as :class:`datetime.date`); sorted ascending by ``_sd`` and
    reset-indexed. ``session_dates`` is the same column as a ``numpy.ndarray``
    of ``dtype=object`` for fast per-session slicing.
    """

    df: pd.DataFrame
    session_dates: np.ndarray


def _load_symbol_daily(
    store: MarketDataStore,
    symbol: str,
    min_session: _dt.date,
    max_session: _dt.date,
    lookback_days: int,
    feed: str,
    daily_adjustment: str = "raw",
) -> _DailySymbolFrame | None:
    """Read the symbol's daily parquet ONCE over the full lookback span.

    Mirrors the legacy ``store.daily_bars(symbol, target - lookback_days, target,
    feed=feed)`` call but with the span widened to the entire batch horizon:
    ``[min_session - lookback_days, max_session]``. Inclusive on both ends —
    the half-open ``prior["_sd"] < session`` slice per session removes any
    lookahead.

    Returns ``None`` when the lake has no rows for this symbol.
    """
    start = min_session - _dt.timedelta(days=lookback_days)
    df = store.daily_bars(
        symbol, start, max_session, feed=feed, adjustment=daily_adjustment
    )
    _count(daily_parquet_reads=1)
    if df.empty:
        return None
    if "session_date" in df.columns:
        sd = pd.to_datetime(df["session_date"]).dt.date
    else:
        sd = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
    df = df.assign(_sd=sd).sort_values("_sd").reset_index(drop=True)
    if df.empty:
        return None
    session_dates = df["_sd"].to_numpy()
    return _DailySymbolFrame(df=df, session_dates=session_dates)


def build_daily_cache_for_sessions_from_lake(
    store_or_root: Any,
    symbols_by_session: Mapping[_dt.date, Sequence[str]],
    sessions: Sequence[_dt.date],
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    atr_window: int = 14,
    vol_window: int = 20,
    ema_span: int = 10,
    lookback_days: int = 400,
    daily_adjustment: str = "raw",
) -> dict[_dt.date, pd.DataFrame]:
    """Build a per-session daily-feature cache for every session in one pass.

    Returns ``dict[date, pd.DataFrame]`` matching the legacy per-session output
    of :func:`bowaka_v2_lab.data.suppliers.build_daily_cache_from_lake` exactly:

    * Same column list (``DAILY_CACHE_COLUMNS``).
    * Same row content (floats within ``1e-12``, ints / strings exact).
    * Same row order (mirrors ``symbols_by_session[s]`` minus symbols whose
      ``prior`` slice is empty for that session).

    Each symbol is read from the lake ONCE; per-session DataFrames are built
    from in-memory slices.

    The function is a pure helper — no config, no Optuna coupling — so it is
    safe to call from any caller that has the lake + the per-session
    eligible-symbol map.
    """
    store = _as_store(store_or_root, vendor=vendor)
    sessions_list = [pd.Timestamp(s).date() if not isinstance(s, _dt.date) else s
                     for s in sessions]
    if not sessions_list:
        return {}
    all_symbols = tuple(dict.fromkeys(
        sym for s in sessions_list for sym in symbols_by_session.get(s, ())
    ))
    _count(daily_cache_symbols=len(all_symbols), daily_cache_sessions=len(sessions_list))
    min_session = min(sessions_list)
    max_session = max(sessions_list)
    # ---- Phase A: read each symbol once over the full span. -----------------
    t_load_start = _time.perf_counter()
    daily_by_symbol: dict[str, _DailySymbolFrame] = {}
    for sym in all_symbols:
        sf = _load_symbol_daily(
            store, sym, min_session, max_session, lookback_days, feed,
            daily_adjustment=daily_adjustment,
        )
        if sf is not None:
            daily_by_symbol[sym] = sf
    t_load_end = _time.perf_counter()
    _count(daily_cache_batch_load_seconds=t_load_end - t_load_start)
    # ---- Phase B: build per-session DataFrame from in-memory slices. -------
    t_slice_start = _time.perf_counter()
    out: dict[_dt.date, pd.DataFrame] = {}
    for s in sessions_list:
        lo = s - _dt.timedelta(days=lookback_days)
        rows: list[dict[str, Any]] = []
        for sym in symbols_by_session.get(s, ()):
            sf = daily_by_symbol.get(sym)
            if sf is None or sf.df.empty:
                continue
            mask = (sf.df["_sd"] >= lo) & (sf.df["_sd"] < s)
            prior = sf.df[mask].sort_values("_sd").reset_index(drop=True)
            if prior.empty:
                continue
            rows.append(_daily_cache_row_from_prior(
                sym, prior,
                atr_window=atr_window, vol_window=vol_window, ema_span=ema_span,
            ))
        out[s] = (
            pd.DataFrame(rows, columns=DAILY_CACHE_COLUMNS)
            if rows else pd.DataFrame(columns=DAILY_CACHE_COLUMNS)
        )
    t_slice_end = _time.perf_counter()
    _count(daily_cache_batch_slice_seconds=t_slice_end - t_slice_start)
    return out


__all__ = ["build_daily_cache_for_sessions_from_lake"]
