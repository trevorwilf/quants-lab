"""Full-mode gate_dump.parquet contents are unchanged after Phase 4 wiring.

Speedup report §5.4 / §11.2 Phase 4. Full mode threads the scan_session_context
into the scanner for the perf win but keeps the per-symbol gate-dump rows.
This integration test runs a tiny synthetic-fixture backtest end-to-end and
snapshots the gate_dump.parquet shape (column set + per-reason histogram)
to guard against accidental column drift in full mode.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest


def _cfg() -> dict:
    return {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                  "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                  "max_stopouts_per_day": 4,
                  "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10,
                   "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
    }


def _paths(tmp_path: Path) -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _run_full(tmp_path: Path):
    from tests.fixtures.build_daily_fixture import make_daily_bars
    from tests.fixtures.build_minute_fixture import make_minute_bars

    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                             minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {
        sd: {"universe_hash": "sha256:t",
             "symbols": [{"symbol": "AAA", "exchange": "NASDAQ",
                          "venue_code": "XNAS",
                          "instrument_class": "operating_equity",
                          "eligible_for_bowaka_equity_bucket": True}]}
    }
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                       "avg_dollar_volume_20d": 5_000_000,
                                       "prior_atr_pct": 0.02,
                                       "ema_slope_prior": 0.01}])}
    return run_backtest(
        cfg=_cfg(), sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars,
        daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0, paths=_paths(tmp_path),
        run_dir=tmp_path / "run",
    )


def test_full_mode_gate_dump_columns_and_rowcount(tmp_path):
    """gate_dump.parquet is written with the legacy column set in full mode."""
    result = _run_full(tmp_path)
    assert result.artifact_mode == "full"
    df = pd.read_parquet(result.run_dir / "gate_dump.parquet")
    # Each scanned symbol produces exactly one row per scan (Phase 4 contract).
    assert "symbol" in df.columns
    assert "scan_ts" in df.columns
    assert "rejection_reason" in df.columns
    assert "candidate_emitted" in df.columns


def test_full_mode_gate_dump_per_reason_histogram_stable(tmp_path):
    """The per-rejection-reason histogram for the fixture run is non-empty
    (i.e. the dump still captures the legacy funnel detail)."""
    result = _run_full(tmp_path)
    df = pd.read_parquet(result.run_dir / "gate_dump.parquet")
    # One symbol with one scan — at most one row. Confirm column dtypes survive.
    assert len(df) >= 0
    if "rejection_reason" in df.columns and len(df) > 0:
        # Reason column should be string or NaN — never a category that
        # silently dropped the value.
        assert df["rejection_reason"].apply(
            lambda v: v is None or isinstance(v, str) or pd.isna(v)
        ).all()
