"""Phase 3 — full-fold backtest parity (legacy vs compatibility runtime).

Speedup report v2 §10.5. Runs a full backtest over the fixture validation
sessions twice:
  (a) runtime_mode="disabled" (legacy scanner);
  (b) runtime_mode="compatibility" with the scan-matrix store attached.

Asserts ``BacktestResult.trades`` deep-equal, ``daily_equity`` equal to
1e-12, and the realized PnL equal to 1e-9. ``@pytest.mark.slow`` keeps it
out of the default ``make test-all`` gate.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from bowaka_v2_lab.config import load_config
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import (
    build_daily_cache_from_lake,
    make_lake_suppliers,
    make_forward_minute_supplier,
    make_quote_supplier,
    resolve_intraday_window_policy,
)
from bowaka_v2_lab.scanner.scan_matrix import ScanMatrixStore
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from bowaka_v2_lab.universe.builder import (
    build_pit_universe_for_sessions,
    eligible_symbols,
)
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


pytestmark = pytest.mark.slow


def _run_fold(fx, *, runtime_mode: str, store, tmp_path, lab_root):
    """Run a backtest over the matrix's validation sessions in one runtime mode."""
    from bowaka_common.marketdata import MarketDataStore

    cfg = dict(fx.cfg)
    cfg.setdefault("optuna", {}).setdefault("acceleration", {}).setdefault(
        "scan_matrix", {}
    )
    if runtime_mode == "disabled":
        cfg["optuna"]["acceleration"]["scan_matrix"]["enabled"] = False
        cfg["optuna"]["acceleration"]["scan_matrix"]["runtime_mode"] = "disabled"
    else:
        cfg["optuna"]["acceleration"]["scan_matrix"]["enabled"] = True
        cfg["optuna"]["acceleration"]["scan_matrix"]["runtime_mode"] = "compatibility"
        cfg["optuna"]["acceleration"]["scan_matrix"]["require_parity_manifest"] = False

    lake = fx.lake
    feed = cfg["market_data"]["feed"]
    sessions = fx.sessions
    mds = MarketDataStore(lake)
    policy = resolve_intraday_window_policy(cfg)
    minute_sup, daily_sup = make_lake_suppliers(
        lake, feed=feed, intraday_window_policy=policy,
    )
    quote_sup = make_quote_supplier(lake, feed=feed, default_max_age_seconds=60.0)
    fwd_sup = make_forward_minute_supplier(lake, feed=feed)

    pit = build_pit_universe_for_sessions(sessions, dict(cfg), mds)
    universe_by_session = {}
    daily_cache_by_session = {}
    for sd in sessions:
        syms = sorted(eligible_symbols(pit.get(sd, {})) or [])
        universe_by_session[sd] = {
            "universe_hash": "sha256:t",
            "symbols": [
                {
                    "symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                    "instrument_class": "operating_equity",
                    "eligible_for_bowaka_equity_bucket": True,
                }
                for s in syms
            ],
        }
        daily_cache_by_session[sd] = build_daily_cache_from_lake(
            lake, syms, sd, feed=feed,
        )

    lab_dir = tmp_path / f"run_{runtime_mode}" / "research_notebooks" / "bowaka_v2_lab"
    paths = BowakaV2Paths(
        lab_root=lab_dir,
        data_root=lab_dir / "data",
        artifact_root=lab_dir / "artifacts",
        config_path=fx.cfg_path,
    )
    return run_backtest(
        cfg=cfg, sessions=list(sessions),
        scan_times_per_session=lambda d: list(scan_times_for_session(d, dict(cfg))),
        universe_snapshot_by_session=universe_by_session,
        daily_cache_by_session=daily_cache_by_session,
        minute_bars_supplier=minute_sup,
        daily_bars_supplier=daily_sup,
        quote_supplier=quote_sup,
        forward_minute_supplier=fwd_sup,
        initial_bankroll=100_000.0,
        paths=paths,
        artifact_mode="objective_minimal",
        scan_matrix_store=store if runtime_mode != "disabled" else None,
    )


def test_full_fold_backtest_parity(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(tmp_path / "fx", lab_root)
    store = ScanMatrixStore(fx.store_root, readonly=True)

    legacy = _run_fold(
        fx, runtime_mode="disabled", store=store, tmp_path=tmp_path, lab_root=lab_root,
    )
    compat = _run_fold(
        fx, runtime_mode="compatibility", store=store, tmp_path=tmp_path, lab_root=lab_root,
    )

    # Trades deep-equal (same count + same per-trade symbol / pnl).
    leg_trades = [(t.get("symbol"), round(float(t.get("pnl", 0.0)), 9)) for t in legacy.trades]
    cmp_trades = [(t.get("symbol"), round(float(t.get("pnl", 0.0)), 9)) for t in compat.trades]
    assert leg_trades == cmp_trades, "trade list diverged between runtime modes"

    # Daily equity equal to 1e-12 (bankroll series per session).
    assert len(legacy.daily_equity) == len(compat.daily_equity)
    for leg_row, cmp_row in zip(legacy.daily_equity, compat.daily_equity):
        assert leg_row["session_date"] == cmp_row["session_date"]
        assert abs(
            float(leg_row["bankroll"]) - float(cmp_row["bankroll"])
        ) <= 1e-12, (leg_row, cmp_row)
        assert abs(
            float(leg_row["daily_realized_pnl"])
            - float(cmp_row["daily_realized_pnl"])
        ) <= 1e-9
