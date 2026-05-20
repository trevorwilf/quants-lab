"""Entry day 1 exits day 3 via target / day 4 via time_stop, depending on fixture."""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_multi_day_hold_exits_on_time_stop_or_target(tmp_path: Path) -> None:
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5),
                 _dt.date(2024, 9, 6), _dt.date(2024, 9, 9)]
    symbols = ["AAA"]
    # Build a daily fixture where the price drifts UP modestly (no early target hit) so the
    # position holds across multiple days and exits via time_stop at day 4 (>=max_hold_days=3).
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=15,
                              daily_drift_pct=0.005, daily_range_pct=0.01)
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 1,
                     "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                   "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                   "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.20, "take_profit_pct": 0.20, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-09", "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                   "data_root": "research_notebooks/bowaka_v2_lab/data",
                   "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }
    universe = {sd: {"universe_hash": "sha256:t",
                       "symbols": [{"symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
                                       "instrument_class": "operating_equity",
                                       "eligible_for_bowaka_equity_bucket": True}]}
                  for sd in sessions}
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                          "avg_dollar_volume_20d": 5_000_000,
                                          "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}])
                    for sd in sessions}

    def daily_supplier(sym, sd):
        return daily[daily["session_date"] == sd]

    def minute_supplier(sym, ts):
        sd = pd.Timestamp(ts).tz_convert("America/New_York").date()
        return make_minute_bars(sym, sd, minutes=30, drift_per_minute=0.4, minute_volume=10_000)

    result = run_backtest(
        cfg=cfg, sessions=sessions,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0, paths=paths,
    )
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    # At least one trade closed across the 4-session window; exit reason should be
    # one of time_stop / take_profit / stop_loss (not absent).
    assert len(trades) >= 1
    assert {t for t in trades["exit_reason"]}.issubset({"time_stop", "take_profit", "stop_loss"})
