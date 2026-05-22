"""Real implementations behind the bowaka_v2_lab CLI subcommands.

Each command is **config-driven**: when ``market_data.minute_bar_source`` /
``daily_bar_source`` is ``alpaca`` / ``shared`` the command reads the shared
market-data lake (``bowaka_common.marketdata``); otherwise it uses deterministic
synthetic data (the smoke / fixture path). The two are decided by :func:`_uses_lake`.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import pandas as pd

from .config import BowakaV2Paths, load_config
from .config.models import BowakaV2Config
from .data.suppliers import (
    build_daily_cache_from_lake,
    make_forward_minute_supplier,
    make_lake_suppliers,
    make_quote_supplier,
    resolve_intraday_window_policy,
)
from .features.volume_curve import build_volume_curve_from_minute_bars, synthesize_default_curve
from .scanner.replay import replay_scanner
from .scanner.universe_builder import build_universe_snapshot, write_universe_snapshot
from .sim.backtester import run_backtest
from .sim.replay_fixtures import synthetic_daily_cache, synthetic_universe
from .sim.schedule import scan_times_for_session
from .universe.builder import (
    build_pit_universe,
    build_pit_universe_for_sessions,
    funnel as universe_funnel,
    to_scanner_snapshot,
)

_REPO_ROOT = Path(__file__).resolve().parents[4]


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------
def _load(config_path: str | Path) -> tuple[dict, BowakaV2Config, BowakaV2Paths]:
    cfg = load_config(config_path)
    validated = BowakaV2Config.model_validate(cfg)
    paths = BowakaV2Paths.from_config(validated, repo_root=_REPO_ROOT)
    paths.assert_strategy_isolation()
    return cfg, validated, paths


def _uses_lake(cfg: dict) -> bool:
    md = cfg.get("market_data", {}) or {}
    return str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared")


def _to_date(value: Any, default: _dt.date | None = None) -> _dt.date:
    if value is None:
        return default or _dt.date.today()
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    return pd.Timestamp(value).date()


def _xnys_sessions(start: _dt.date, end: _dt.date) -> list[_dt.date]:
    import exchange_calendars as xcals

    cal = xcals.get_calendar("XNYS")
    sessions = cal.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    return [pd.Timestamp(s).date() for s in sessions]


def _resolve_symbols(cfg: dict, md: dict, *, cap: int = 100) -> list[str]:
    """Symbols for a command: explicit config list > lake-derived (capped) > synthetic.

    Research configs define the universe by rule (no explicit ``universe.symbols``);
    in lake mode that resolves to the lake's available symbols, capped so a single
    command stays bounded — set ``universe.symbols`` for a precise universe.
    """
    explicit = (cfg.get("universe", {}) or {}).get("symbols")
    if explicit:
        return [str(s) for s in explicit]
    if str(md.get("minute_bar_source", "fixture")) in ("alpaca", "shared"):
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
                {
                    "symbol": symbol, "timestamp": bar_ts,
                    "open": 100 + i * 0.1, "high": 100 + i * 0.2,
                    "low": 99.5, "close": 100 + i * 0.15, "volume": 5000.0,
                }
            )
        return pd.DataFrame(rows)

    def daily_supplier(symbol: str, session_date: Any) -> pd.DataFrame:
        d = _to_date(session_date)
        return pd.DataFrame(
            [{"symbol": symbol, "session_date": d, "open": 100.0,
              "high": 110.0, "low": 98.0, "close": 108.0, "volume": 100_000}]
        )

    return minute_supplier, daily_supplier


def _lake_store(md: dict):
    """A ``MarketDataStore`` over the configured shared-lake root."""
    from bowaka_common.marketdata import MarketDataStore

    return MarketDataStore(md.get("shared_root"))


def _is_smoke(validated: BowakaV2Config) -> bool:
    """True when the config declares ``simulation.mode == smoke_fixture``."""
    return validated.simulation.mode == "smoke_fixture"


def _build_pit_universe_by_session(
    cfg: dict, sessions: list[_dt.date], md: dict
):
    """Point-in-time universe (``{session_date: {symbol: UniverseRecord}}``).

    Realism Phase 3: a non-smoke run must consume the PIT universe built from
    the lake asset snapshot + prior-day bars — never the synthetic fixture.
    """
    store = _lake_store(md)
    return build_pit_universe_for_sessions(sessions, cfg, store)


def _resolve_universe_for_backtest(
    cfg: dict,
    validated: BowakaV2Config,
    sessions: list[_dt.date],
    md: dict,
    symbols: list[str],
    *,
    allow_synthetic_universe: bool,
    command: str,
):
    """Resolve the per-session universe for a backtest / replay command.

    Returns ``(universe_by_session, universe_kind)``. ``universe_kind`` is
    ``"pit"`` (point-in-time, the default for every non-smoke config) or
    ``"synthetic"`` (the deterministic fixture, permitted **only** in
    ``smoke_fixture`` mode). ``--allow-synthetic-universe`` is honoured only in
    smoke mode and raises in any real mode.
    """
    if allow_synthetic_universe and not _is_smoke(validated):
        raise RuntimeError(
            f"{command} refused: --allow-synthetic-universe is permitted only when "
            f"simulation.mode is 'smoke_fixture'; this config is "
            f"'{validated.simulation.mode}'. A non-smoke run must build the "
            f"point-in-time universe from the lake."
        )
    if _is_smoke(validated):
        # Smoke / fixture: synthetic universe is the intended path.
        return {s: synthetic_universe(symbols) for s in sessions}, "synthetic"
    # Non-smoke: build the point-in-time universe from the lake.
    return _build_pit_universe_by_session(cfg, sessions, md), "pit"


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def run_backtest_command(
    config_path: str | Path,
    *,
    smoke: bool = False,
    run_dir: str | Path | None = None,
    allow_smoke: bool = False,
    allow_synthetic_universe: bool = False,
) -> dict:
    """Run the comprehensive v2 backtest (``run-backtest`` / ``smoke``).

    ``run-backtest`` (``smoke=False``) **refuses** a config whose
    ``simulation.mode`` is ``smoke_fixture`` unless ``allow_smoke`` is set: the
    ``smoke`` subcommand is the intended entry point for fixture configs, and a
    "real" backtest on synthetic data is misleading. The ``smoke`` subcommand
    (``smoke=True``) is always exempt.

    Realism Phase 3: a non-smoke config builds the **point-in-time universe**
    from the lake asset snapshot + prior-day bars. ``allow_synthetic_universe``
    is honoured only in ``smoke_fixture`` mode and refused otherwise.
    """
    cfg, validated, paths = _load(config_path)
    if not smoke and validated.simulation.mode == "smoke_fixture" and not allow_smoke:
        raise RuntimeError(
            "run-backtest refused: simulation.mode is 'smoke_fixture'. Use the "
            "`smoke` subcommand for fixture configs, run a research config "
            "(intended_realism / current_code_parity), or pass "
            "--allow-smoke-optimization to override."
        )
    md = cfg.get("market_data", {}) or {}
    bt = cfg.get("backtest", {}) or {}
    symbols = _resolve_symbols(cfg, md)
    start = _to_date(bt.get("start_date"), _dt.date(2024, 9, 4))
    end = _to_date(bt.get("end_date"), start)
    sessions = _xnys_sessions(start, end) or [start]
    if smoke:
        sessions = sessions[:1]
        symbols = symbols[:3]

    quote_supplier = None
    forward_minute_supplier = None
    if _uses_lake(cfg):
        feed, root = md.get("feed", "iex"), md.get("shared_root")
        minute_supplier, daily_supplier = make_lake_suppliers(
            root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
        )
        daily_cache = {s: build_daily_cache_from_lake(root, symbols, s, feed=feed) for s in sessions}
        # Realism Phase 6: historical-quote supplier + forward-minute supplier
        # (for marketable-limit timeout detection) from the same lake.
        quote_supplier = make_quote_supplier(
            root, feed=feed,
            default_max_age_seconds=float(
                (cfg.get("execution") or {}).get("max_quote_age_seconds", 60)
            ),
        )
        forward_minute_supplier = make_forward_minute_supplier(root, feed=feed)
        data_source = "lake"
    else:
        minute_supplier, daily_supplier = _synthetic_suppliers()
        daily_cache = {s: synthetic_daily_cache(symbols) for s in sessions}
        data_source = "synthetic"
    # Realism Phase 3: PIT universe for non-smoke configs; synthetic only in
    # smoke mode (or when --allow-synthetic-universe is passed in smoke mode).
    universe, universe_kind = _resolve_universe_for_backtest(
        cfg, validated, sessions, md, symbols,
        allow_synthetic_universe=allow_synthetic_universe,
        command=("smoke" if smoke else "run-backtest"),
    )

    # Realism Phase 4: full calendar-aware intraday scan cadence (was one
    # hard-coded 14:00-UTC scan per session). scan_times_for_session honours
    # the session's scanner window, interval, DST, holidays and early closes.
    result = run_backtest(
        cfg=cfg,
        sessions=sessions,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        quote_supplier=quote_supplier,
        forward_minute_supplier=forward_minute_supplier,
        initial_bankroll=100_000.0,
        paths=paths,
        run_dir=Path(run_dir) if run_dir else None,
    )
    return {
        "status": "ok",
        "command": "smoke" if smoke else "run-backtest",
        "data_source": data_source,
        "universe_kind": universe_kind,
        "run_id": result.run_id,
        "run_dir": str(result.run_dir),
        "sessions": len(sessions),
        "summary": result.summary,
    }


def build_universe_command(config_path: str | Path, *, out_path: str | Path | None = None) -> dict:
    """Build a point-in-time universe snapshot (``build-universe``).

    Realism Phase 3: a non-smoke config builds the point-in-time universe from
    the lake asset snapshot + prior-day bars via ``universe.build_pit_universe``;
    a smoke config keeps the synthetic snapshot path.
    """
    cfg, validated, paths = _load(config_path)
    md = cfg.get("market_data", {}) or {}
    session = _to_date((cfg.get("backtest", {}) or {}).get("end_date"))
    symbols = _resolve_symbols(cfg, md)

    if not _is_smoke(validated):
        # Point-in-time universe from the lake asset master + prior-day bars.
        records = build_pit_universe(session, cfg, _lake_store(md))
        snapshot = to_scanner_snapshot(records)
        snapshot["session_date"] = session.isoformat()
        snapshot["funnel"] = universe_funnel(records)
        data_source = "lake"
    else:
        baselines = pd.DataFrame(
            [{"symbol": s, "prior_close": 100.0, "avg_dollar_volume_20d": 5_000_000} for s in symbols]
        )
        asset_master = pd.DataFrame(
            [
                {"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                 "instrument_class": "operating_equity", "eligible_for_bowaka_equity_bucket": True}
                for s in symbols
            ]
        )
        snapshot = build_universe_snapshot(
            asset_master=asset_master, daily_baselines=baselines, cfg=cfg, session_date=session
        )
        data_source = "synthetic"

    out = Path(out_path) if out_path else (
        Path(paths.data_root) / "universe_snapshots" / f"{session.isoformat()}.json"
    )
    write_universe_snapshot(snapshot, out)
    return {
        "status": "ok",
        "command": "build-universe",
        "data_source": data_source,
        "session_date": session.isoformat(),
        "universe_size": len(snapshot["symbols"]),
        "path": str(out),
    }


def build_volume_curve_command(config_path: str | Path, *, out_path: str | Path | None = None) -> dict:
    """Build the intraday volume curve (``build-volume-curve``)."""
    cfg, _validated, paths = _load(config_path)
    md = cfg.get("market_data", {}) or {}
    bt = cfg.get("backtest", {}) or {}

    source = "synthetic_default"
    curve = synthesize_default_curve()
    if _uses_lake(cfg):
        feed, root = md.get("feed", "iex"), md.get("shared_root")
        from bowaka_common.marketdata import MarketDataStore

        store = MarketDataStore(root)
        start = _to_date(bt.get("start_date"))
        end = _to_date(bt.get("end_date"), start)
        frames = []
        for sym in _resolve_symbols(cfg, md):
            df = store.minute_bars(sym, start, pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1), feed=feed)
            if not df.empty:
                frames.append(df)
        if frames:
            curve = build_volume_curve_from_minute_bars(pd.concat(frames, ignore_index=True))
            source = "lake_minute_bars"
        else:
            source = "synthetic_default (no lake minute bars found)"

    out = Path(out_path) if out_path else (Path(paths.data_root) / "volume_curve.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    curve.to_parquet(out, index=False)
    return {
        "status": "ok",
        "command": "build-volume-curve",
        "source": source,
        "rows": int(len(curve)),
        "path": str(out),
    }


def replay_scanner_command(
    config_path: str | Path,
    *,
    run_dir: str | Path | None = None,
    allow_synthetic_universe: bool = False,
) -> dict:
    """Replay the historical scanner (``replay-scanner``).

    Realism Phase 3: a non-smoke config replays against the point-in-time
    universe for the session; smoke configs keep the synthetic universe.
    """
    cfg, validated, paths = _load(config_path)
    md = cfg.get("market_data", {}) or {}
    symbols = _resolve_symbols(cfg, md)
    session = _to_date((cfg.get("backtest", {}) or {}).get("start_date"), _dt.date(2024, 9, 4))
    # Realism Phase 4: replay the full intraday scan cadence for the session
    # (was one hard-coded 14:00-UTC scan).
    scan_ts = scan_times_for_session(session, cfg)

    if _uses_lake(cfg):
        feed, root = md.get("feed", "iex"), md.get("shared_root")
        bars_supplier, _ = make_lake_suppliers(
            root, feed=feed,
            intraday_window_policy=resolve_intraday_window_policy(cfg),
        )
        daily_cache = build_daily_cache_from_lake(root, symbols, session, feed=feed)
        data_source = "lake"
    else:
        bars_supplier, _ = _synthetic_suppliers()
        daily_cache = synthetic_daily_cache(symbols)
        data_source = "synthetic"

    universe_by_session, universe_kind = _resolve_universe_for_backtest(
        cfg, validated, [session], md, symbols,
        allow_synthetic_universe=allow_synthetic_universe,
        command="replay-scanner",
    )
    snapshot = universe_by_session[session]
    if universe_kind == "pit":
        snapshot = to_scanner_snapshot(snapshot)

    target = Path(run_dir) if run_dir else (
        Path(paths.artifact_root) / "runs" / f"replay_cli_{session.isoformat()}"
    )
    summary = replay_scanner(
        cfg=cfg,
        universe_snapshot=snapshot,
        daily_cache=daily_cache,
        volume_curve=None,
        scan_timestamps=scan_ts,
        bars_supplier=bars_supplier,
        run_dir=target,
    )
    return {
        "status": "ok",
        "command": "replay-scanner",
        "data_source": data_source,
        "universe_kind": universe_kind,
        "run_dir": str(target),
        "summary": summary,
    }
