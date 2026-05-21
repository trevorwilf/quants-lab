"""Phase 3 — per-session universe artifacts are written to the run dir.

A run that consumes a point-in-time universe must write, under
``<run_dir>/universe/``, a ``universe_snapshot_{date}.parquet`` and a
``universe_funnel_{date}.json`` for each PIT session, and record the per-session
``universe_hash`` in ``run_manifest.json["universe_hashes_by_session"]``.
"""
from __future__ import annotations

import datetime as _dt
import json

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions
from tests.fixtures.universe_fixture import (
    FakeLakeStore,
    asset_master_frame,
    daily_bars_frame,
    realism_cfg,
)


def _minute_supplier(symbol, cutoff):
    ts = pd.Timestamp(cutoff)
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    rows = []
    base = ts.normalize() + pd.Timedelta(hours=13, minutes=30)
    for i in range(40):
        bar = base + pd.Timedelta(minutes=i)
        if bar > ts:
            break
        rows.append({"symbol": symbol, "timestamp": bar, "open": 10.0,
                     "high": 10.1, "low": 9.9, "close": 10.05, "volume": 5000.0})
    return pd.DataFrame(rows)


def _daily_supplier(symbol, session_date):
    return pd.DataFrame([{"symbol": symbol, "session_date": session_date,
                          "open": 10.0, "high": 10.2, "low": 9.8, "close": 10.1,
                          "volume": 200_000}])


def _full_cfg() -> dict:
    """A non-smoke config for run_backtest.

    ``current_code_parity`` is non-smoke (so the PIT universe is required and a
    synthetic universe is refused) but, unlike ``intended_realism``, does not
    abort on the config-parity diff or fail the DQ gate closed — keeping these
    tests focused on the universe artifacts.
    """
    cfg = realism_cfg()
    cfg["strategy_id"] = "bowaka_v2"
    cfg["simulation"] = {"mode": "current_code_parity", "allow_research_relaxed": True}
    return cfg


def test_universe_snapshot_and_funnel_written(tmp_path, lab_root) -> None:
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    syms = ("AAA", "BBB", "PENNYX", "SPYX")
    am = asset_master_frame(
        [
            {"symbol": "AAA"},
            {"symbol": "BBB"},
            {"symbol": "PENNYX"},  # priced out below the band
            {"symbol": "SPYX", "name": "SPDR Test ETF Trust"},  # ETF -> excluded
        ]
    )
    daily = {
        "AAA": daily_bars_frame("AAA", end_before=sessions[0]),
        "BBB": daily_bars_frame("BBB", end_before=sessions[0]),
        "PENNYX": daily_bars_frame("PENNYX", end_before=sessions[0], close=0.40, volume=5_000_000),
        "SPYX": daily_bars_frame("SPYX", end_before=sessions[0]),
    }
    store = FakeLakeStore(am, daily)
    universe = build_pit_universe_for_sessions(sessions, _full_cfg(), store)

    run_dir = tmp_path / "run"
    paths = BowakaV2Paths.default(lab_root.parent.parent)
    result = run_backtest(
        cfg=_full_cfg(),
        sessions=sessions,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session={s: pd.DataFrame() for s in sessions},
        minute_bars_supplier=_minute_supplier,
        daily_bars_supplier=_daily_supplier,
        paths=paths,
        run_dir=run_dir,
    )

    universe_dir = run_dir / "universe"
    assert universe_dir.is_dir()
    for session in sessions:
        snap = universe_dir / f"universe_snapshot_{session.isoformat()}.parquet"
        funnel = universe_dir / f"universe_funnel_{session.isoformat()}.json"
        assert snap.is_file(), snap
        assert funnel.is_file(), funnel

        snap_df = pd.read_parquet(snap)
        assert set(snap_df.columns) == {
            "session_date", "symbol", "instrument_class", "venue_code",
            "eligible", "rejection_reasons",
        }
        # All four asset-master symbols appear; AAA/BBB eligible, others not.
        assert set(snap_df["symbol"]) == set(syms)
        eligible = set(snap_df[snap_df["eligible"]]["symbol"])
        assert eligible == {"AAA", "BBB"}

        funnel_doc = json.loads(funnel.read_text(encoding="utf-8"))
        assert funnel_doc["starting_count"] == 4
        assert funnel_doc["eligible_count"] == 2
        assert "price_below_min" in funnel_doc["rejections_by_reason"]
        assert "excluded_instrument_class" in funnel_doc["rejections_by_reason"]
        assert funnel_doc["session_date"] == session.isoformat()
        assert funnel_doc["universe_hash"].startswith("sha256:")


def test_universe_hashes_in_run_manifest(tmp_path, lab_root) -> None:
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    am = asset_master_frame([{"symbol": "AAA"}, {"symbol": "BBB"}])
    daily = {
        "AAA": daily_bars_frame("AAA", end_before=sessions[0]),
        "BBB": daily_bars_frame("BBB", end_before=sessions[0]),
    }
    universe = build_pit_universe_for_sessions(sessions, _full_cfg(), FakeLakeStore(am, daily))

    run_dir = tmp_path / "run"
    paths = BowakaV2Paths.default(lab_root.parent.parent)
    run_backtest(
        cfg=_full_cfg(),
        sessions=sessions,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session={s: pd.DataFrame() for s in sessions},
        minute_bars_supplier=_minute_supplier,
        daily_bars_supplier=_daily_supplier,
        paths=paths,
        run_dir=run_dir,
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    hashes = manifest["universe_hashes_by_session"]
    assert set(hashes) == {s.isoformat() for s in sessions}
    for uhash in hashes.values():
        assert uhash.startswith("sha256:")
