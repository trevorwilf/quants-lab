"""Lake-backed suppliers for the v2 backtester.

Bridges ``bowaka_common.marketdata.MarketDataStore`` to the callable suppliers
that ``run_backtest`` / ``replay`` expect, plus a no-lookahead daily-feature
cache builder. This is the v2 counterpart of the synthetic fixtures in
``sim/replay_fixtures.py`` — same shapes, real data.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd

from bowaka_common.marketdata import MarketDataStore

from ..utils.profile_counters import counters_enabled, current_profile_counters


def _count(**kwargs: int) -> None:
    """Increment the active :class:`ProfileCounters` if counters are enabled.

    Fast-path skip when the process flag is off (zero allocations). Outside an
    active context the ``LookupError`` from ``ContextVar.get()`` is swallowed.
    """
    if not counters_enabled():
        return
    try:
        current_profile_counters().inc(**kwargs)
    except LookupError:
        pass

#: Local clock time (ET) each intraday-window policy starts the forming-session
#: minute-bar window from. ``regular_open`` = 09:30, ``scanner_start`` = 09:45,
#: ``extended_hours`` = 04:00 (premarket). Realism Phase 4 (audit P0-006).
_INTRADAY_WINDOW_START_ET: dict[str, tuple[int, int]] = {
    "scanner_start_to_scan": (9, 45),
    "regular_open_to_scan": (9, 30),
    "extended_hours_to_scan": (4, 0),
}
#: Policy used when a config omits ``simulation.intraday_window_policy``. The
#: live scanner builds the window from scanner_start (09:45 ET).
_DEFAULT_INTRADAY_WINDOW_POLICY = "scanner_start_to_scan"


def intraday_window_start(cutoff: Any, intraday_window_policy: str) -> pd.Timestamp:
    """UTC start of the forming-session minute-bar window for ``cutoff``.

    Realism Phase 4 (audit P0-006). ``cutoff`` is the scan timestamp; the window
    runs ``[start, cutoff]``. ``start`` is the policy's local (ET) clock time on
    ``cutoff``'s ET session date:

    - ``scanner_start_to_scan`` → 09:45 ET (the live scanner's behaviour)
    - ``regular_open_to_scan`` → 09:30 ET (regular open)
    - ``extended_hours_to_scan`` → 04:00 ET (premarket)

    The ET session date is taken from ``cutoff`` converted to America/New_York,
    so the window never spills into the previous calendar day's premarket.
    """
    ts = pd.Timestamp(cutoff)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    session_date = ts.tz_convert("America/New_York").date()
    hour, minute = _INTRADAY_WINDOW_START_ET.get(
        str(intraday_window_policy), _INTRADAY_WINDOW_START_ET[_DEFAULT_INTRADAY_WINDOW_POLICY]
    )
    start_et = pd.Timestamp(
        _dt.datetime.combine(session_date, _dt.time(hour=hour, minute=minute)),
        tz="America/New_York",
    )
    return start_et.tz_convert("UTC")


def resolve_intraday_window_policy(cfg: Any) -> str:
    """Resolve ``simulation.intraday_window_policy`` from a config (dict or model).

    Falls back to :data:`_DEFAULT_INTRADAY_WINDOW_POLICY` when unset — the
    SimulationConfig post-validator normally fills this from ``mode``, so an
    unset value here only happens for a bare dict that skipped validation.
    """
    sim = getattr(cfg, "simulation", None)
    if sim is None and isinstance(cfg, dict):
        sim = cfg.get("simulation") or {}
    if sim is None:
        sim = {}
    if isinstance(sim, dict):
        policy = sim.get("intraday_window_policy")
    else:
        policy = getattr(sim, "intraday_window_policy", None)
    return str(policy) if policy else _DEFAULT_INTRADAY_WINDOW_POLICY


#: Columns of the v2 daily-feature cache (mirrors ``synthetic_daily_cache``).
DAILY_CACHE_COLUMNS = [
    "symbol",
    "prior_close",
    "avg_volume_20d",
    "avg_dollar_volume_20d",
    "prior_atr_14d",
    "prior_atr_pct",
    "ema_10_prior",
    "ema_10_lag_3",
    "ema_slope_prior",
]


def _as_date(x: Any) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    return pd.Timestamp(x).date()


def _as_store(store_or_root: Any, *, vendor: str) -> MarketDataStore:
    if isinstance(store_or_root, MarketDataStore):
        return store_or_root
    return MarketDataStore(store_or_root, vendor=vendor)


def make_lake_suppliers(
    shared_root: str | Path | None = None,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    daily_lookback_days: int = 400,
    intraday_window_policy: str = _DEFAULT_INTRADAY_WINDOW_POLICY,
) -> tuple[Callable[[str, Any], pd.DataFrame], Callable[[str, Any], pd.DataFrame]]:
    """Return ``(minute_bars_supplier, daily_bars_supplier)`` reading the shared lake.

    - ``minute_bars_supplier(symbol, cutoff)`` → the forming-session minute bars
      from the :func:`intraday_window_start` for ``intraday_window_policy`` up to
      ``cutoff`` (tz-aware).
    - ``daily_bars_supplier(symbol, session_date)`` → daily bars over the trailing
      ``daily_lookback_days`` ending on ``session_date``.

    Realism Phase 4 (audit P0-006): the minute-bar window now starts at the
    policy-resolved local time (09:30 / 09:45 / 04:00 ET) rather than UTC
    midnight, so the forming-session bar window honours
    ``simulation.intraday_window_policy``.
    """
    store = _as_store(shared_root, vendor=vendor)

    def minute_bars_supplier(symbol: str, cutoff: Any) -> pd.DataFrame:
        _count(minute_supplier_calls=1)
        ts = pd.Timestamp(cutoff)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        session_start = intraday_window_start(ts, intraday_window_policy)
        return store.minute_bars(symbol, session_start, ts, feed=feed)

    def daily_bars_supplier(symbol: str, session_date: Any) -> pd.DataFrame:
        end = _as_date(session_date)
        start = end - _dt.timedelta(days=daily_lookback_days)
        return store.daily_bars(symbol, start, end, feed=feed)

    return minute_bars_supplier, daily_bars_supplier


def make_forward_minute_supplier(
    shared_root: str | Path | None = None,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    window_minutes: int = 5,
) -> Callable[[str, Any], pd.DataFrame]:
    """Return a supplier of the minute bars **forward** from a timestamp.

    Realism Phase 6. ``forward_minute_supplier(symbol, ts)`` returns the minute
    bars in ``[ts, ts + window_minutes]`` — the order-lifetime path a
    marketable-limit fill walks to decide whether the quote chased past its
    limit before the timeout. (The ordinary minute supplier only ever returns
    bars *up to* a cutoff, so a separate forward reader is needed.)
    """
    store = _as_store(shared_root, vendor=vendor)

    def forward_minute_supplier(symbol: str, ts: Any) -> pd.DataFrame:
        _count(minute_supplier_calls=1)
        start = pd.Timestamp(ts)
        start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
        end = start + pd.Timedelta(minutes=int(window_minutes))
        return store.minute_bars(symbol, start, end, feed=feed)

    return forward_minute_supplier


def make_quote_supplier(
    shared_root: str | Path | None = None,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    default_max_age_seconds: float = 60.0,
) -> Callable[..., Any]:
    """Return a ``quote_supplier`` reading historical quotes from the shared lake.

    Realism Phase 6. The returned callable has signature
    ``quote_supplier(symbol, ts, max_age_seconds=None) -> Optional[dict]`` — it
    queries :meth:`MarketDataStore.quotes_at_or_before` and maps the resulting
    :class:`bowaka_common.marketdata.QuoteRow` to the dict shape the
    ``StrategyConsumer`` consumes as ``historical_quote``.

    On the current lake — which has **no ``quotes/`` partitions** (there is no
    quote-ingestion stage) — every call returns ``None``, so the lab's synthetic
    fallback (per ``quote_fallback_policy``) covers every non-realism path and a
    realism run correctly fails the quote-coverage gate.
    """
    store = _as_store(shared_root, vendor=vendor)

    def quote_supplier(symbol: str, ts: Any, max_age_seconds: Any = None):
        _count(quote_supplier_calls=1)
        age = float(max_age_seconds) if max_age_seconds is not None else float(default_max_age_seconds)
        row = store.quotes_at_or_before(symbol, ts, max_age_seconds=age, feed=feed)
        if row is None:
            return None
        # Audit P1-002 fix: record the row's actual UTC timestamp, not the
        # request timestamp. Quote age + spread analytics need the real quote
        # time. Fall back to the request ts only if the store omitted the field.
        row_ts = row.timestamp if row.timestamp is not None else pd.Timestamp(ts)
        return {
            "bid": row.bid,
            "ask": row.ask,
            "bid_size": row.bid_size,
            "ask_size": row.ask_size,
            "mid": row.mid,
            "spread_pct": row.spread_pct,
            "quote_timestamp": str(row_ts),
            "quote_age_seconds": row.quote_age_seconds,
            "source": row.source,
        }

    return quote_supplier


def _daily_cache_row_from_prior(
    symbol: str,
    prior: pd.DataFrame,
    *,
    atr_window: int,
    vol_window: int,
    ema_span: int,
) -> dict[str, Any]:
    """Compute the per-symbol daily-cache row from an already-filtered ``prior``.

    Speedup report v2 §4 P1 / §5.3 / Phase 1 task 1. Extracted from the legacy
    :func:`build_daily_cache_from_lake` loop so the batch path
    (:func:`bowaka_v2_lab.data.daily_cache_batch.build_daily_cache_for_sessions_from_lake`)
    can share identical row math. ``prior`` must be the DataFrame after
    ``prior["_sd"] < target`` filtering, sorted ascending by ``_sd`` and
    reset-indexed.

    The output dict carries the exact keys / dtypes the legacy loop appended,
    in the order matching :data:`DAILY_CACHE_COLUMNS`. **EMA is computed from
    the truncated ``prior`` (length ≤ ``lookback_days`` calendar days) — do
    NOT compute over a longer history and slice; the 400-day truncation is
    part of the strategy definition.**
    """
    close = prior["close"].astype(float)
    high = prior["high"].astype(float)
    low = prior["low"].astype(float)
    volume = prior["volume"].astype(float)
    prev_close = close.shift(1)
    true_range = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = true_range.rolling(atr_window).mean()
    ema = close.ewm(span=ema_span, adjust=False).mean()
    prior_close = float(close.iloc[-1])
    prior_atr = float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0
    ema_prior = float(ema.iloc[-1])
    ema_lag3 = float(ema.iloc[-4]) if len(ema) >= 4 else ema_prior
    return {
        "symbol": symbol,
        "prior_close": prior_close,
        "avg_volume_20d": float(volume.tail(vol_window).mean()),
        "avg_dollar_volume_20d": float((close * volume).tail(vol_window).mean()),
        "prior_atr_14d": prior_atr,
        "prior_atr_pct": (prior_atr / prior_close) if prior_close else 0.0,
        "ema_10_prior": ema_prior,
        "ema_10_lag_3": ema_lag3,
        "ema_slope_prior": (ema_prior - ema_lag3) / 3.0,
    }


def build_daily_cache_from_lake(
    store_or_root: Any,
    symbols: Iterable[str],
    session_date: Any,
    *,
    feed: str = "iex",
    vendor: str = "alpaca",
    atr_window: int = 14,
    vol_window: int = 20,
    ema_span: int = 10,
    lookback_days: int = 400,
) -> pd.DataFrame:
    """Build the v2 daily-feature cache as-of the session **before** ``session_date``.

    No-lookahead: every value uses only sessions strictly earlier than
    ``session_date``. Returns a DataFrame with :data:`DAILY_CACHE_COLUMNS`.
    """
    _count(daily_cache_builds=1)
    store = _as_store(store_or_root, vendor=vendor)
    target = _as_date(session_date)
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        df = store.daily_bars(
            symbol, target - _dt.timedelta(days=lookback_days), target, feed=feed
        )
        _count(daily_parquet_reads=1)
        if df.empty:
            continue
        if "session_date" in df.columns:
            sd = pd.to_datetime(df["session_date"]).dt.date
        else:
            sd = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York").dt.date
        prior = df.assign(_sd=sd)
        prior = prior[prior["_sd"] < target].sort_values("_sd").reset_index(drop=True)
        if prior.empty:
            continue
        rows.append(_daily_cache_row_from_prior(
            symbol, prior,
            atr_window=atr_window, vol_window=vol_window, ema_span=ema_span,
        ))
    if not rows:
        return pd.DataFrame(columns=DAILY_CACHE_COLUMNS)
    return pd.DataFrame(rows, columns=DAILY_CACHE_COLUMNS)
