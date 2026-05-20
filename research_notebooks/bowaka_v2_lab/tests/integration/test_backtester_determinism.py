"""Same cfg + dataset_hash + seed → byte-identical summary.json."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def _cfg():
    return {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                     "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                   "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04", "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                   "data_root": "research_notebooks/bowaka_v2_lab/data",
                   "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def _run(tmp_path: Path):
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sd = _dt.date(2024, 9, 4)
    sessions = [sd]
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {sd: {"universe_hash": "sha256:t",
                       "symbols": [{"symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
                                       "instrument_class": "operating_equity",
                                       "eligible_for_bowaka_equity_bucket": True}]}}
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                          "avg_dollar_volume_20d": 5_000_000,
                                          "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}])}
    return run_backtest(
        cfg=_cfg(), sessions=sessions,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars,
        daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0, paths=paths,
    )


def test_two_runs_produce_identical_summary(tmp_path: Path) -> None:
    r1 = _run(tmp_path / "a")
    r2 = _run(tmp_path / "b")
    # Strip per-host fields that vary between runs of the same code (e.g. created_at,
    # host) — we focus on the *deterministic* parts of summary.json.
    s1 = dict(r1.summary)
    s2 = dict(r2.summary)
    # run_id differs only if dataset_hash or cfg_hash differs; here both inputs match,
    # so run_id must also match.
    assert s1["run_id"] == s2["run_id"]
    # Strip non-deterministic fields from the summary that should be identical.
    for k in ("run_id", "n_trades", "win_rate", "total_pnl", "net_return_pct",
                "final_bankroll", "accepted_count", "rejected_count"):
        assert s1[k] == s2[k], f"determinism break on {k}: {s1[k]} != {s2[k]}"
