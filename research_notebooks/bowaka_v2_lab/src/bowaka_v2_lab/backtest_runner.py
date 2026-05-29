"""Canonical config-driven backtest runner for the v2 lab.

:func:`run_config_backtest` is the single "run a real backtest from a config"
entry point shared by notebooks 05-08 and 11. It resolves the symbol universe,
sessions, bar suppliers, and the daily-feature cache from the config — reading
the shared market-data lake when ``market_data.*_source`` is ``alpaca`` /
``shared``, else using deterministic synthetic data (the smoke / fixture path).
"""
from __future__ import annotations

import copy
import datetime as _dt
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BowakaV2Paths, load_config
from .sim.backtester import BacktestResult, run_backtest
from .sim.replay_fixtures import synthetic_daily_cache, synthetic_universe
from .sim.schedule import scan_times_for_session

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _to_date(value: Any, default: _dt.date | None = None) -> _dt.date:
    if value is None:
        return default or _dt.date.today()
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def uses_lake(cfg: dict) -> bool:
    """True when the config points the bar feeds at the shared market-data lake."""
    md = cfg.get("market_data", {}) or {}
    return str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared")


def config_sessions(cfg: dict) -> list[_dt.date]:
    """XNYS sessions in the config's ``backtest`` window."""
    import exchange_calendars as xcals

    bt = cfg.get("backtest", {}) or {}
    start = _to_date(bt.get("start_date"), _dt.date(2024, 9, 4))
    end = _to_date(bt.get("end_date"), start)
    cal = xcals.get_calendar("XNYS")
    sessions = [pd.Timestamp(s).date() for s in cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))]
    return sessions or [start]


def resolve_symbols(cfg: dict, *, cap: int = 100) -> list[str]:
    """Explicit ``universe.symbols`` > lake-derived symbols (capped) > synthetic."""
    explicit = (cfg.get("universe", {}) or {}).get("symbols")
    if explicit:
        return [str(s) for s in explicit]
    md = cfg.get("market_data", {}) or {}
    if uses_lake(cfg):
        from bowaka_common.marketdata import available_symbols

        return available_symbols(
            md.get("shared_root"), timeframe="1d", feed=md.get("feed", "iex")
        )[:cap]
    return ["AAA", "BBB", "CCC"]


def _synthetic_suppliers():
    """Deterministic synthetic minute / daily bar suppliers (smoke path)."""

    def minute_supplier(symbol: str, cutoff: Any) -> pd.DataFrame:
        ts = pd.Timestamp(cutoff)
        ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
        session = ts.tz_convert("America/New_York").date()
        open_et = pd.Timestamp(session, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
        rows = []
        for i in range(60):
            bar_ts = (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC")
            if bar_ts > ts:
                break
            rows.append(
                {"symbol": symbol, "timestamp": bar_ts, "open": 100 + i * 0.1,
                 "high": 100 + i * 0.2, "low": 99.5, "close": 100 + i * 0.15, "volume": 5000.0}
            )
        return pd.DataFrame(rows)

    def daily_supplier(symbol: str, session_date: Any) -> pd.DataFrame:
        d = _to_date(session_date)
        return pd.DataFrame(
            [{"symbol": symbol, "session_date": d, "open": 100.0,
              "high": 110.0, "low": 98.0, "close": 108.0, "volume": 100_000}]
        )

    return minute_supplier, daily_supplier


def resolve_suppliers(cfg: dict):
    """``(minute_supplier, daily_supplier)`` — lake-backed or synthetic per config.

    Realism Phase 4: the lake minute supplier's forming-session window honours
    ``simulation.intraday_window_policy``.
    """
    md = cfg.get("market_data", {}) or {}
    if uses_lake(cfg):
        from .data.adjustment import daily_adjustment_for_config
        from .data.suppliers import make_lake_suppliers, resolve_intraday_window_policy

        return make_lake_suppliers(
            md.get("shared_root"),
            feed=md.get("feed", "iex"),
            intraday_window_policy=resolve_intraday_window_policy(cfg),
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
    return _synthetic_suppliers()


def resolve_daily_cache(cfg: dict, symbols: list[str], session: _dt.date) -> pd.DataFrame:
    """Daily-feature cache for ``session`` — lake-backed or synthetic per config."""
    md = cfg.get("market_data", {}) or {}
    if uses_lake(cfg):
        from .data.adjustment import daily_adjustment_for_config
        from .data.suppliers import build_daily_cache_from_lake

        return build_daily_cache_from_lake(
            md.get("shared_root"), symbols, session, feed=md.get("feed", "iex"),
            daily_adjustment=daily_adjustment_for_config(cfg),
        )
    return synthetic_daily_cache(symbols)


def apply_overrides(cfg: dict, overrides: dict) -> dict:
    """Return a deep copy of ``cfg`` with ``overrides`` merged section-wise."""
    out = copy.deepcopy(cfg)
    for section, vals in overrides.items():
        if isinstance(vals, dict):
            merged = dict(out.get(section) or {})
            merged.update(vals)
            out[section] = merged
        else:
            out[section] = vals
    return out


def paths_for(cfg: dict) -> BowakaV2Paths:
    paths = BowakaV2Paths.from_config(cfg, repo_root=_REPO_ROOT)
    paths.assert_strategy_isolation()
    return paths


def run_config_backtest(
    config: Any,
    *,
    param_overrides: dict | None = None,
    sessions: list[_dt.date] | None = None,
    run_dir: str | Path | None = None,
    paths: BowakaV2Paths | None = None,
    initial_bankroll: float = 100_000.0,
) -> BacktestResult:
    """Run a real backtest from a config (path or dict). Returns the BacktestResult.

    With a research config (``market_data.*_source: alpaca``) the suppliers and
    daily cache are read from the shared lake; with the smoke / fixture config
    they are synthetic. ``param_overrides`` (e.g. ``{"backtest": {"entry_delay_minutes": 5}}``)
    are merged section-wise — used by the ablation and counterfactual notebooks.
    """
    cfg = load_config(config) if isinstance(config, (str, Path)) else dict(config)
    if param_overrides:
        cfg = apply_overrides(cfg, param_overrides)
    paths = paths or paths_for(cfg)
    symbols = resolve_symbols(cfg)
    if sessions is None:
        sessions = config_sessions(cfg)
    minute_supplier, daily_supplier = resolve_suppliers(cfg)
    universe = {s: synthetic_universe(symbols) for s in sessions}
    daily_cache = {s: resolve_daily_cache(cfg, symbols, s) for s in sessions}
    # Realism Phase 4: full calendar-aware intraday scan cadence (was one
    # hard-coded 14:00-UTC scan per session).
    return run_backtest(
        cfg=cfg,
        sessions=sessions,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=initial_bankroll,
        paths=paths,
        run_dir=Path(run_dir) if run_dir else None,
    )
