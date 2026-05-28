"""Phase 3/4 — shared fixture builder for scan-matrix parity tests.

Builds a tiny lake + a scan matrix and returns everything the parity tests
need to drive BOTH the legacy ``evaluate_one_scan`` path and the matrix
compatibility/vectorized paths against the same inputs:

    * the opened :class:`ScanMatrixSession` for the first validation session;
    * a legacy ``bars_supplier`` that returns the SAME 04:00-16:00 ET window
      (sliced ``<= scan_ts``) the matrix builder consumed, so the legacy
      aggregation matches the matrix cells exactly;
    * the per-session ``ScanSessionContext``;
    * the universe snapshot + daily cache + scan times.

The matrix builder writes ``volume_curve_fraction`` via the fallback curve
(``compute_volume_curve_fraction(None, ...)``); the legacy path must be
driven with ``volume_curve=None`` for parity, which this helper enforces.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yaml

from bowaka_v2_lab import cli
from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake
from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.scanner.scan_context import build_scan_session_context
from bowaka_v2_lab.scanner.scan_matrix import ScanMatrixStore
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from bowaka_v2_lab.universe.builder import (
    build_pit_universe_for_sessions,
    eligible_symbols,
)


@dataclass
class MatrixParityFixture:
    cfg: dict
    cfg_path: Path
    lake: Path
    store_root: Path
    store: ScanMatrixStore
    sessions: list[dt.date]
    session_date: dt.date
    matrix_session: Any
    universe: dict
    daily_cache: pd.DataFrame
    scan_times: list[Any]
    bars_supplier: Callable[[str, Any], pd.DataFrame | None]
    scan_context: Any


def _matched_bars_supplier(
    lake: Path, symbols: list[str], session_date: dt.date, feed: str,
) -> Callable[[str, Any], pd.DataFrame | None]:
    """A bars supplier returning the SAME 04:00-16:00 ET window the matrix
    builder used, sliced ``<= scan_ts`` — guarantees identical aggregation."""
    from bowaka_common.marketdata import MarketDataStore

    mds = MarketDataStore(lake)
    sstart = pd.Timestamp(
        dt.datetime.combine(session_date, dt.time(4, 0)),
        tz="America/New_York",
    ).tz_convert("UTC")
    send = pd.Timestamp(
        dt.datetime.combine(session_date, dt.time(16, 0)),
        tz="America/New_York",
    ).tz_convert("UTC")
    full: dict[str, pd.DataFrame] = {}
    for s in symbols:
        try:
            full[s] = mds.minute_bars(s, sstart, send, feed=feed)
        except Exception:  # noqa: BLE001
            full[s] = pd.DataFrame()

    def supplier(sym: str, ts: Any) -> pd.DataFrame | None:
        df = full.get(sym)
        if df is None or df.empty:
            return df
        ts_obj = pd.Timestamp(ts)
        ts_cols = [c for c in df.columns if c.lower() in ("timestamp", "ts")]
        if not ts_cols:
            return df
        return df[df[ts_cols[0]] <= ts_obj]

    return supplier


def build_matrix_parity_fixture(
    tmp_path: Path,
    lab_root: Path,
    *,
    symbols: list[str] | None = None,
    start: dt.date = dt.date(2024, 1, 1),
    end: dt.date = dt.date(2024, 5, 1),
    scan_interval_seconds: int = 1800,
) -> MatrixParityFixture:
    """Build a tiny lake + matrix and return a parity fixture for the first
    validation session."""
    symbols = symbols or ["AAA"]
    lake = tmp_path / "lake"
    build_tiny_lake(lake, symbols, start=start, end=end)
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=symbols, start=start, end=end, n_trials=1,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw.setdefault("session", {})["scan_interval_seconds"] = scan_interval_seconds
    raw["simulation"]["intraday_window_policy"] = "extended_hours_to_scan"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    store_root = tmp_path / "matrix"
    rc = cli.main([
        "scan-matrix", "build",
        "--config", str(cfg_path),
        "--scope", "validation",
        "--store-root", str(store_root),
        "--workers", "1",
        "--reserve-system-gib", "0.1",
        "--max-optuna-workers", "1",
    ])
    assert rc == 0, "matrix build failed"

    cfg = load_config(cfg_path)
    store = ScanMatrixStore(store_root, readonly=True)
    sessions = [dt.date.fromisoformat(s) for s in store.manifest["sessions"]]
    session_date = sessions[0]
    matrix_session = store.open_session(session_date, purpose="objective")

    feed = cfg["market_data"]["feed"]
    from bowaka_common.marketdata import MarketDataStore

    mds = MarketDataStore(lake)
    pit = build_pit_universe_for_sessions([session_date], dict(cfg), mds)
    eligible = sorted(eligible_symbols(pit.get(session_date, {})) or symbols)
    daily_cache = build_daily_cache_from_lake(lake, eligible, session_date, feed=feed)
    universe = {
        "universe_hash": "sha256:t",
        "symbols": [
            {
                "symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                "instrument_class": "operating_equity",
                "eligible_for_bowaka_equity_bucket": True,
            }
            for s in eligible
        ],
    }
    scan_times = list(scan_times_for_session(session_date, dict(cfg)))
    bars_supplier = _matched_bars_supplier(lake, eligible, session_date, feed)
    scan_context = build_scan_session_context(
        dict(cfg), daily_cache, universe, scan_times,
        volume_curve=None, collect_gate_dump=True,
    )
    return MatrixParityFixture(
        cfg=dict(cfg),
        cfg_path=cfg_path,
        lake=lake,
        store_root=store_root,
        store=store,
        sessions=sessions,
        session_date=session_date,
        matrix_session=matrix_session,
        universe=universe,
        daily_cache=daily_cache,
        scan_times=scan_times,
        bars_supplier=bars_supplier,
        scan_context=scan_context,
    )
