"""Phase 3 — emitted candidate events carry the session universe_hash.

Every candidate event the scanner emits for a session must record that
session's point-in-time ``universe_hash`` (the sha256 of the sorted eligible
symbol list). The same hash appears in ``run_manifest.json``, so an event can be
tied back to the exact universe it was scanned against.
"""
from __future__ import annotations

import datetime as _dt
import json

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.universe.builder import (
    build_pit_universe_for_sessions,
    to_scanner_snapshot,
    universe_hash,
)
from tests.fixtures.universe_fixture import (
    FakeLakeStore,
    asset_master_frame,
    daily_bars_frame,
    realism_cfg,
)


def _minute_supplier(symbol, cutoff):
    """A full forming-session minute series up to ``cutoff`` (passes stale-bar)."""
    ts = pd.Timestamp(cutoff)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    base = ts.normalize() + pd.Timedelta(hours=13, minutes=30)
    rows = []
    i = 0
    while True:
        bar = base + pd.Timedelta(minutes=i)
        if bar > ts:
            break
        rows.append({"symbol": symbol, "timestamp": bar, "open": 10.0,
                     "high": 10.3, "low": 9.8, "close": 10.2, "volume": 8000.0})
        i += 1
    return pd.DataFrame(rows)


def _daily_supplier(symbol, session_date):
    return pd.DataFrame([{"symbol": symbol, "session_date": session_date,
                          "open": 10.0, "high": 10.4, "low": 9.7, "close": 10.25,
                          "volume": 300_000}])


def _daily_cache_row(symbol: str) -> dict:
    return {
        "symbol": symbol, "prior_close": 10.0, "avg_volume_20d": 500_000,
        "avg_dollar_volume_20d": 5_000_000.0, "prior_atr_14d": 0.30,
        "prior_atr_pct": 0.03, "ema_10_prior": 9.9, "ema_10_lag_3": 9.7,
        "ema_slope_prior": 0.05,
    }


def _cfg() -> dict:
    # current_code_parity: non-smoke (PIT required) without the realism
    # parity-diff abort. allow_research_relaxed -> signal gates may be unset, so
    # every candidate passes the (disabled) gates and an event is emitted.
    cfg = realism_cfg()
    cfg["strategy_id"] = "bowaka_v2"
    cfg["simulation"] = {"mode": "current_code_parity", "allow_research_relaxed": True}
    cfg["scanner"] = {"max_candidates_per_scan": 25, "max_entries_per_scan": 25,
                      "min_signal_strength": 0.0}
    return cfg


def test_candidate_events_carry_session_universe_hash(tmp_path, lab_root) -> None:
    session = _dt.date(2024, 9, 4)
    am = asset_master_frame([{"symbol": "AAA"}, {"symbol": "BBB"}])
    daily = {
        "AAA": daily_bars_frame("AAA", end_before=session),
        "BBB": daily_bars_frame("BBB", end_before=session),
    }
    cfg = _cfg()
    universe = build_pit_universe_for_sessions([session], cfg, FakeLakeStore(am, daily))
    expected_hash = universe_hash(universe[session])
    # Sanity: the PIT universe has both symbols eligible.
    assert len(to_scanner_snapshot(universe[session])["symbols"]) == 2

    run_dir = tmp_path / "run"
    paths = BowakaV2Paths.default(lab_root.parent.parent)
    result = run_backtest(
        cfg=cfg,
        sessions=[session],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session={
            session: pd.DataFrame([_daily_cache_row("AAA"), _daily_cache_row("BBB")])
        },
        minute_bars_supplier=_minute_supplier,
        daily_bars_supplier=_daily_supplier,
        paths=paths,
        run_dir=run_dir,
    )

    # Candidate events were emitted, and each carries the session universe_hash.
    assert result.candidate_events, "expected the scanner to emit candidate events"
    for ev in result.candidate_events:
        assert ev["universe_hash"] == expected_hash, ev["symbol"]

    # The same hash is in the JSONL artifact and the run manifest.
    jsonl = (run_dir / "candidate_events.jsonl").read_text(encoding="utf-8").strip()
    assert jsonl, "candidate_events.jsonl is empty"
    for line in jsonl.splitlines():
        assert json.loads(line)["universe_hash"] == expected_hash

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["universe_hashes_by_session"][session.isoformat()] == expected_hash
