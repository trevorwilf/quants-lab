"""Tiny historical fixture (3 symbols × 2 sessions) → run-dir artifacts appear."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.scanner.replay import replay_scanner
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_replay_writes_expected_artifacts(tmp_run_dir: Path) -> None:
    symbols = ["AAA", "BBB", "CCC"]
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    bars_by_sym_session = {}
    for sd in sessions:
        for sym in symbols:
            bars_by_sym_session[(sym, sd)] = make_minute_bars(
                sym, sd, minutes=30, drift_per_minute=0.8, minute_volume=10_000,
            )

    universe = {
        "universe_hash": "sha256:test",
        "symbols": [{
            "symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
            "instrument_class": "operating_equity",
            "eligible_for_bowaka_equity_bucket": True,
        } for s in symbols],
    }
    daily_cache = pd.DataFrame([
        {"symbol": s, "prior_close": 100.0, "avg_dollar_volume_20d": 5_000_000,
         "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
        for s in symbols
    ])
    cfg = {
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "signal_expiry_seconds": 600},
        "signals": {},
        "historical_features": {},
    }

    scan_ts_list = [
        pd.Timestamp(f"2024-09-04 14:00:00", tz="UTC"),
        pd.Timestamp(f"2024-09-05 14:00:00", tz="UTC"),
    ]

    def supplier(sym: str, ts) -> pd.DataFrame:
        sd = pd.Timestamp(ts).tz_convert("America/New_York").date()
        return bars_by_sym_session.get((sym, sd), pd.DataFrame())

    summary = replay_scanner(
        cfg=cfg, universe_snapshot=universe, daily_cache=daily_cache,
        volume_curve=None, scan_timestamps=scan_ts_list,
        bars_supplier=supplier, run_dir=tmp_run_dir,
    )

    assert (tmp_run_dir / "scanner_summary.json").is_file()
    assert (tmp_run_dir / "candidate_events.jsonl").is_file()
    assert (tmp_run_dir / "candidate_events.parquet").is_file()
    assert (tmp_run_dir / "gate_dump.parquet").is_file()
    assert summary["scan_count"] == 2
    assert summary["emitted_count"] >= 1

    # Round-trip the JSONL.
    with (tmp_run_dir / "candidate_events.jsonl").open() as fh:
        events = [json.loads(line) for line in fh]
    assert len(events) == summary["emitted_count"]
    for ev in events:
        assert ev["strategy"] == "bowaka_v2"
        assert ev["schema_version"] == 3
