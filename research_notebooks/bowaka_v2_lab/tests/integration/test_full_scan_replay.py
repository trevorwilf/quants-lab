"""Realism Phase 4 — a backtest replays every configured scan per session.

The pre-Phase-4 backtester ran exactly one scan per session at a hard-coded
14:00 UTC. With the calendar-aware scheduler the backtester now replays the
full intraday cadence; ``run_manifest.json['scan_counts']`` records the per-
session expected vs actual scan counts and ``gate_dump.parquet`` carries one
row per ``(scan_ts, symbol)`` tuple.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.schedule import scan_times_for_session
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def _paths(tmp_path: Path) -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _cfg(sessions: list[_dt.date], *, interval_s: int = 900) -> dict:
    # Coarse 15-minute interval keeps the test fast while still being a true
    # multi-scan replay; scan_times_for_session itself is exercised at the
    # live 60s cadence by the schedule unit tests.
    return {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "session": {
            "calendar": "XNYS", "timezone": "America/New_York",
            "scanner_start": "09:45", "scanner_end": "15:30",
            "scan_interval_seconds": interval_s,
        },
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600,
                    "same_symbol_entries_per_day": 1, "symbol_cooldown_minutes": 390},
        "signals": {},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                 "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                 "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.05, "max_hold_days": 1},
        "backtest": {"start_date": sessions[0].isoformat(),
                     "end_date": sessions[-1].isoformat(), "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def test_backtest_replays_full_cadence_and_writes_gate_dump(tmp_path: Path) -> None:
    # Two ordinary XNYS sessions, 3 symbols.
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    symbols = ["AAA", "BBB", "CCC"]
    cfg = _cfg(sessions, interval_s=900)

    # Minute bars span the whole session so a scan late in the day still has
    # bars within max_bar_age. 09:30 -> 15:59 ET = 390 minutes.
    bars_by = {
        (s, sd): make_minute_bars(s, sd, minutes=390, drift_per_minute=0.05,
                                  minute_volume=20_000)
        for s in symbols for sd in sessions
    }
    daily_by = {
        s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=6,
                           daily_drift_pct=0.08, daily_range_pct=0.10)
        for s in symbols
    }
    universe = {sd: {"universe_hash": "sha256:t",
                     "symbols": [{"symbol": s, "exchange": "NASDAQ",
                                  "venue_code": "XNAS",
                                  "instrument_class": "operating_equity",
                                  "eligible_for_bowaka_equity_bucket": True}
                                 for s in symbols]}
                for sd in sessions}
    daily_cache = {sd: pd.DataFrame([{"symbol": s, "prior_close": 100.0,
                                      "avg_dollar_volume_20d": 5_000_000,
                                      "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
                                     for s in symbols])
                   for sd in sessions}

    expected_per_session = {
        sd: len(scan_times_for_session(sd, cfg)) for sd in sessions
    }
    # Each session has the same coarse cadence: (15:30-09:45)/900 + 1 = 24.
    assert set(expected_per_session.values()) == {24}

    result = run_backtest(
        cfg=cfg, sessions=sessions,
        scan_times_per_session=lambda d: scan_times_for_session(d, cfg),
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars_by[
            (sym, pd.Timestamp(ts).tz_convert("America/New_York").date())
        ],
        daily_bars_supplier=lambda sym, d: daily_by[sym][daily_by[sym]["session_date"] == d],
        initial_bankroll=10_000.0, paths=_paths(tmp_path),
    )

    # --- run_manifest scan_counts ---
    manifest = json.loads((result.run_dir / "run_manifest.json").read_text())
    scan_counts = manifest["scan_counts"]
    assert set(scan_counts) == {sd.isoformat() for sd in sessions}
    for sd in sessions:
        sc = scan_counts[sd.isoformat()]
        assert sc["expected_scans"] == 24
        # The backtester replayed *every* configured scan, not one.
        assert sc["actual_scans"] == 24
        assert sc["actual_scans"] > 1
        assert "gate_rejection_breakdown" in sc

    # --- per-(scan_ts, symbol) gate dump ---
    gate_dump = pd.read_parquet(result.run_dir / "gate_dump.parquet")
    assert len(gate_dump) > 0
    for col in ("scan_ts", "symbol", "candidate_emitted", "rejection_reason"):
        assert col in gate_dump.columns
    # 24 scans x 3 symbols x 2 sessions = 144 gate-dump rows.
    assert len(gate_dump) == 24 * 3 * 2
    # Every (scan_ts, symbol) tuple appears exactly once.
    assert not gate_dump.duplicated(subset=["scan_ts", "symbol"]).any()
    # Multiple distinct scan timestamps are present (true multi-scan replay).
    assert gate_dump["scan_ts"].nunique() == 24 * 2


def test_single_scan_legacy_lambda_still_supported(tmp_path: Path) -> None:
    # A caller passing an explicit single-scan lambda still works — the
    # scheduler wiring did not remove the injection point.
    sd = _dt.date(2024, 9, 4)
    cfg = _cfg([sd])
    symbols = ["AAA"]
    bars = {s: make_minute_bars(s, sd, minutes=60, drift_per_minute=0.1) for s in symbols}
    daily_by = {s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=5) for s in symbols}
    universe = {sd: {"universe_hash": "sha256:t",
                     "symbols": [{"symbol": s, "exchange": "NASDAQ",
                                  "venue_code": "XNAS",
                                  "instrument_class": "operating_equity",
                                  "eligible_for_bowaka_equity_bucket": True}
                                 for s in symbols]}}
    daily_cache = {sd: pd.DataFrame([{"symbol": s, "prior_close": 100.0,
                                      "avg_dollar_volume_20d": 5_000_000,
                                      "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
                                     for s in symbols])}
    result = run_backtest(
        cfg=cfg, sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars[sym],
        daily_bars_supplier=lambda sym, d: daily_by[sym][daily_by[sym]["session_date"] == d],
        initial_bankroll=10_000.0, paths=_paths(tmp_path),
    )
    manifest = json.loads((result.run_dir / "run_manifest.json").read_text())
    assert manifest["scan_counts"][sd.isoformat()]["actual_scans"] == 1
