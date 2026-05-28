"""Phase 4 — three-way full-fold backtest parity (slow).

Speedup report v2 §10.6 task 3. Runs a full backtest over the fixture
validation sessions under runtime_mode disabled / compatibility /
vectorized and asserts the trade list + daily-equity series match across
all three. The vectorized run requires a verifier_version>=2 parity_proof
marker, which this test writes via verify_scan_matrix(..., vectorized_check
=True) + the CLI proof writer path.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import (
    build_daily_cache_from_lake,
    make_forward_minute_supplier,
    make_lake_suppliers,
    make_quote_supplier,
    resolve_intraday_window_policy,
)
from bowaka_v2_lab.scanner.scan_matrix import ScanMatrixStore, verify_scan_matrix
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from bowaka_v2_lab.universe.builder import (
    build_pit_universe_for_sessions,
    eligible_symbols,
)
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


pytestmark = pytest.mark.slow


def _run(fx, *, runtime_mode: str, store, tmp_path):
    from bowaka_common.marketdata import MarketDataStore

    cfg = dict(fx.cfg)
    cfg.setdefault("optuna", {}).setdefault("acceleration", {})["scan_matrix"] = {
        "enabled": runtime_mode != "disabled",
        "runtime_mode": runtime_mode,
        # vectorized requires parity_manifest_present=True at the guard; the
        # verifier_version>=2 proof (written by the test) is the second gate.
        "require_parity_manifest": runtime_mode == "vectorized",
    }
    lake = fx.lake
    feed = cfg["market_data"]["feed"]
    sessions = fx.sessions
    mds = MarketDataStore(lake)
    policy = resolve_intraday_window_policy(cfg)
    minute_sup, daily_sup = make_lake_suppliers(lake, feed=feed, intraday_window_policy=policy)
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
                {"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                 "instrument_class": "operating_equity",
                 "eligible_for_bowaka_equity_bucket": True}
                for s in syms
            ],
        }
        daily_cache_by_session[sd] = build_daily_cache_from_lake(lake, syms, sd, feed=feed)
    lab = tmp_path / f"run_{runtime_mode}" / "research_notebooks" / "bowaka_v2_lab"
    paths = BowakaV2Paths(
        lab_root=lab, data_root=lab / "data", artifact_root=lab / "artifacts",
        config_path=fx.cfg_path,
    )
    return run_backtest(
        cfg=cfg, sessions=list(sessions),
        scan_times_per_session=lambda d: list(scan_times_for_session(d, dict(cfg))),
        universe_snapshot_by_session=universe_by_session,
        daily_cache_by_session=daily_cache_by_session,
        minute_bars_supplier=minute_sup, daily_bars_supplier=daily_sup,
        quote_supplier=quote_sup, forward_minute_supplier=fwd_sup,
        initial_bankroll=100_000.0, paths=paths,
        artifact_mode="objective_minimal",
        scan_matrix_store=store if runtime_mode != "disabled" else None,
    )


def _trades(result):
    return [(t.get("symbol"), round(float(t.get("pnl", 0.0)), 9)) for t in result.trades]


def _equity(result):
    return [(r["session_date"], round(float(r["bankroll"]), 12)) for r in result.daily_equity]


def test_three_way_full_fold_parity(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(tmp_path / "fx", lab_root)
    # Write a verifier_version=2 parity proof (required for vectorized opt-in).
    report = verify_scan_matrix(
        fx.store_root, fx.cfg_path, sample_count=50, vectorized_check=True,
    )
    assert report["status"] == "ok", report
    proof = {
        "matrix_id": report["matrix_id"], "verifier_version": 2,
        "dataset_hash": report["dataset_hash"],
    }
    (Path(fx.store_root) / "parity_proof.json").write_text(
        json.dumps(proof), encoding="utf-8",
    )
    store = ScanMatrixStore(fx.store_root, readonly=True)

    legacy = _run(fx, runtime_mode="disabled", store=store, tmp_path=tmp_path)
    compat = _run(fx, runtime_mode="compatibility", store=store, tmp_path=tmp_path)
    vec = _run(fx, runtime_mode="vectorized", store=store, tmp_path=tmp_path)

    assert _trades(legacy) == _trades(compat) == _trades(vec)
    assert _equity(legacy) == _equity(compat) == _equity(vec)
