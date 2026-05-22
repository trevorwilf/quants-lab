"""Phase 7 — the exit-lifecycle metrics reach the run report + artifacts.

An end-to-end ``current_code_parity`` backtest (which uses the per-lot minute
exit path) must:

* close lots through the minute path with Phase-7 exit reasons,
* write ``exit_analysis.json`` carrying the exit-reason distribution,
  exit-slippage distribution and per-trade MFE/MAE,
* surface the exit-reason distribution in ``summary.json``,
* render the ``## Exit Analysis (Phase 7)`` section in ``report.md``.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.reports.exit_analysis import EXIT_REASONS, build_exit_analysis
from bowaka_v2_lab.sim.backtester import run_backtest


def _minute_session(symbol: str, session_date: _dt.date, *, target_hit: bool) -> pd.DataFrame:
    """A full regular-session minute path (09:30..16:00 ET).

    When ``target_hit`` the price climbs hard enough that the +15% target is
    reached intraday; otherwise it stays flat so the lot rides to the time-stop.
    """
    start = pd.Timestamp(f"{session_date} 09:30", tz="America/New_York")
    end = pd.Timestamp(f"{session_date} 16:00", tz="America/New_York")
    rows = []
    ts = start
    price = 100.0
    i = 0
    while ts <= end:
        if target_hit:
            # Climb steadily so a +15% target is comfortably hit before noon.
            price = 100.0 + i * 0.30
        o = price
        h = price + (5.0 if target_hit else 0.4)
        l = price - 0.4
        c = price + (1.0 if target_hit else 0.0)
        rows.append({
            "symbol": symbol, "timestamp": ts.tz_convert("UTC"),
            "open": o, "high": h, "low": l, "close": c, "volume": 50_000.0,
        })
        ts = ts + pd.Timedelta(minutes=1)
        i += 1
    return pd.DataFrame(rows)


def test_exit_lifecycle_metrics_in_report(tmp_path: Path) -> None:
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB"]
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        # current_code_parity drives the per-lot minute exit path; relaxed so
        # the test need not set every live signal gate.
        "simulation": {"mode": "current_code_parity", "allow_research_relaxed": True,
                       "same_minute_resolution": "conservative"},
        "market_data": {"feed": "iex", "max_bar_age_seconds": 6000},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 6000},
        "signals": {},
        "execution": {"max_spread_bps": 800, "max_quote_age_seconds": 600,
                      "order_type": "market"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000,
                   "min_order_notional": 100},
        "risk": {"max_concurrent_positions": 10, "max_total_entries_per_day": 50,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99},
        # Frozen-contract exits: 8% stop / 15% target / 3-day hold / 15:45 time
        # stop. signal_fade omitted (not under test here).
        "exits": {"stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3,
                  "time_stop": {"enabled": True, "exit_time": "15:45"}},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                     "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }
    universe = {sd: {"universe_hash": "sha256:t",
                     "symbols": [{"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                                  "instrument_class": "operating_equity",
                                  "eligible_for_bowaka_equity_bucket": True}
                                 for s in symbols]}}
    daily_cache = {sd: pd.DataFrame([{"symbol": s, "prior_close": 100.0,
                                      "avg_dollar_volume_20d": 500_000_000,
                                      "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
                                     for s in symbols])}
    # AAA climbs into its target; BBB stays flat and rides to the 15:45 time-stop.
    session_minutes = {
        "AAA": _minute_session("AAA", sd, target_hit=True),
        "BBB": _minute_session("BBB", sd, target_hit=False),
    }
    # The forming-session (entry) minute bars: a short rising path so both
    # symbols emit a candidate at the scan time.
    def minute_supplier(sym, ts):
        full = session_minutes[sym]
        tsv = pd.to_datetime(full["timestamp"], utc=True)
        return full[tsv <= pd.Timestamp(ts)]

    def session_minute_supplier(sym, session_date):
        return session_minutes.get(sym)

    daily_by_sym = {s: pd.DataFrame([{
        "symbol": s, "session_date": sd, "open": 100.0, "high": 130.0,
        "low": 95.0, "close": 110.0, "volume": 1_000_000.0,
    }]) for s in symbols}

    result = run_backtest(
        cfg=cfg, sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T13:45:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=lambda sym, d: daily_by_sym[sym],
        session_minute_supplier=session_minute_supplier,
        initial_bankroll=100_000.0, paths=paths,
        run_dir=tmp_path / "run",
    )

    # ---- exit_analysis.json ----------------------------------------------
    ea_path = result.run_dir / "exit_analysis.json"
    assert ea_path.is_file(), "exit_analysis.json artifact not written"
    ea = json.loads(ea_path.read_text(encoding="utf-8"))
    dist = ea["exit_reason_distribution"]
    # Every canonical exit reason has a count entry (0 when unused).
    for reason in EXIT_REASONS:
        assert reason in dist["counts"], f"exit-reason distribution missing {reason}"
    assert "exit_slippage_bps" in ea
    assert "mfe_mae_per_trade" in ea

    # ---- trades closed via the minute path -------------------------------
    trades = pd.read_parquet(result.run_dir / "trades.parquet")
    assert len(trades) >= 1, "no trades closed in the minute-path run"
    # Minute-path exit reasons only — never the legacy daily-bar reason names.
    seen = set(trades["exit_reason"])
    assert seen.issubset(set(EXIT_REASONS)), f"unexpected exit reasons: {seen}"
    # The per-trade MFE/MAE columns exist on the closed trades.
    for col in ("mfe_pct", "mae_pct", "exit_slippage_bps", "exit_timestamp"):
        assert col in trades.columns, f"trades.parquet missing {col}"

    # ---- summary.json surfaces the distribution --------------------------
    summary = json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8"))
    assert "exit_reason_distribution" in summary
    assert "exit_slippage_bps" in summary

    # ---- report.md renders the exit-analysis section ---------------------
    report = (result.run_dir / "report.md").read_text(encoding="utf-8")
    assert "## Exit Analysis (Phase 7)" in report
    assert "Exit-reason distribution" in report
    assert "MFE / MAE per trade" in report

    # The build_exit_analysis helper is consistent with the run's trades.
    rebuilt = build_exit_analysis(list(trades.to_dict("records")))
    assert (
        rebuilt["exit_reason_distribution"]["n_trades"] == len(trades)
    )
