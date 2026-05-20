"""All 16 files written; absent files → test fail; run_manifest has required fields."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import _REQUIRED_ARTIFACTS, run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def _minimal_cfg() -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                     "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {"allow_unknown_instrument_class_for_research": False},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                        "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                   "max_stopouts_per_day": 4,
                   "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-05",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                   "data_root": "research_notebooks/bowaka_v2_lab/data",
                   "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def _wire_run(tmp_path: Path, lab_root: Path):
    cfg = _minimal_cfg()
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    symbols = ["AAA"]
    minute_by_sym_date = {
        (s, sd): make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5, minute_volume=10_000)
        for s in symbols for sd in sessions
    }
    daily_by_sym = {s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=10) for s in symbols}
    universe_by_session = {sd: {"universe_hash": "sha256:t",
                                  "symbols": [{"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                                                 "instrument_class": "operating_equity",
                                                 "eligible_for_bowaka_equity_bucket": True}
                                                for s in symbols]}
                            for sd in sessions}
    daily_cache_by_session = {sd: pd.DataFrame([{
        "symbol": s, "prior_close": 100.0,
        "avg_dollar_volume_20d": 5_000_000, "prior_atr_pct": 0.02,
        "ema_slope_prior": 0.01,
    } for s in symbols]) for sd in sessions}

    def minute_supplier(sym, ts):
        sd = pd.Timestamp(ts).tz_convert("America/New_York").date()
        return minute_by_sym_date.get((sym, sd))

    def daily_supplier(sym, sd):
        df = daily_by_sym.get(sym)
        if df is None:
            return None
        return df[df["session_date"] == sd]

    def scan_times(sd):
        return [pd.Timestamp(f"{sd}T14:00:00", tz="UTC")]

    return run_backtest(
        cfg=cfg, sessions=sessions, scan_times_per_session=scan_times,
        universe_snapshot_by_session=universe_by_session,
        daily_cache_by_session=daily_cache_by_session,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0,
        paths=paths,
    )


def test_all_required_artifacts_present(tmp_path: Path, repo_root: Path) -> None:
    result = _wire_run(tmp_path, repo_root / "research_notebooks" / "bowaka_v2_lab")
    for fname in _REQUIRED_ARTIFACTS:
        assert (result.run_dir / fname).is_file(), f"missing required artifact: {fname}"


def test_run_manifest_has_required_fields(tmp_path: Path, repo_root: Path) -> None:
    result = _wire_run(tmp_path, repo_root / "research_notebooks" / "bowaka_v2_lab")
    rm = json.loads((result.run_dir / "run_manifest.json").read_text())
    assert rm["strategy_id"] == "bowaka_v2"
    assert rm["run_id"]
    assert rm["config_hash"]
    assert rm["dataset_hash"]
    assert rm["code_manifest_hash"]
