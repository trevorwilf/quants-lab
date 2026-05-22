"""Phase 6 — execution_quality.parquet carries the required execution metrics.

A backtest's ``execution_quality.parquet`` must include spread / quote-age /
slippage distributions (p50/p90/p99), fill rate, partial-fill rate, missing-
quote count, liquidity participation, fees paid and the quote source mix.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.reports.execution_quality import build_execution_quality_frame
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def test_execution_quality_frame_has_required_metrics():
    """The report builder produces every required metric row directly."""
    fills = [
        {"filled": True, "is_partial": False, "quote_spread_pct": 0.001,
         "quote_age_seconds": 2.0, "slippage_bps": 10.0,
         "liquidity_participation_frac": 0.02, "commission": 0.5,
         "regulatory_fees": 0.1, "quote_source": "synthetic_calibrated"},
        {"filled": True, "is_partial": True, "quote_spread_pct": 0.003,
         "quote_age_seconds": 4.0, "slippage_bps": 25.0,
         "liquidity_participation_frac": 0.10, "commission": 0.8,
         "regulatory_fees": 0.2, "quote_source": "synthetic_calibrated"},
        {"filled": False, "is_partial": False, "quote_spread_pct": 0.002,
         "quote_age_seconds": 3.0, "slippage_bps": 0.0,
         "liquidity_participation_frac": 0.0, "commission": 0.0,
         "regulatory_fees": 0.0, "quote_source": "synthetic_zero_spread", "reason": "marketable_limit_timeout"},
    ]
    df = build_execution_quality_frame(fills, missing_quote_count=7)
    metrics = set(df["metric"])
    for required in (
        "fill_rate", "partial_fill_rate", "missing_quote_count",
        "spread_bps_p50", "spread_bps_p90", "spread_bps_p99",
        "quote_age_seconds_p50", "quote_age_seconds_p90", "quote_age_seconds_p99",
        "slippage_bps_p50", "slippage_bps_p90", "slippage_bps_p99",
        "liquidity_participation_p50", "liquidity_participation_p90",
        "liquidity_participation_p99", "fees_commission_total",
        "fees_regulatory_total", "fees_total",
    ):
        assert required in metrics, f"missing metric: {required}"
    # Source mix rows are present per resolved source.
    assert any(m.startswith("source_mix.") for m in metrics)
    vals = dict(zip(df["metric"], df["value"]))
    assert vals["missing_quote_count"] == 7.0
    assert vals["fill_rate"] == 2 / 3  # 2 filled of 3 orders
    assert vals["fees_total"] == round(0.5 + 0.1 + 0.8 + 0.2, 6)


def test_backtest_writes_execution_quality_with_distributions(tmp_path: Path):
    """An end-to-end smoke backtest writes a populated execution_quality.parquet."""
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sd = _dt.date(2024, 9, 4)
    symbols = ["AAA", "BBB", "CCC"]
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 10, "max_entries_per_scan": 10,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 500, "max_quote_age_seconds": 60,
                                     "order_type": "market"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000,
                   "min_order_notional": 100},
        "risk": {"max_concurrent_positions": 10, "max_total_entries_per_day": 50,
                 "max_gross_exposure_pct": 0.99, "daily_loss_pct": 0.99,
                 "max_stopouts_per_day": 99, "stop_trading_after_consecutive_stopouts": 99},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04", "cost_stress": "conservative"},
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
    bars_by_sym = {s: make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5,
                                       minute_volume=20_000) for s in symbols}
    daily_by_sym = {s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=5) for s in symbols}

    result = run_backtest(
        cfg=cfg, sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars_by_sym[sym],
        daily_bars_supplier=lambda sym, d: daily_by_sym[sym][daily_by_sym[sym]["session_date"] == d],
        initial_bankroll=100_000.0, paths=paths,
        run_dir=tmp_path / "run",
    )
    eq = pd.read_parquet(result.run_dir / "execution_quality.parquet")
    assert {"metric", "value"}.issubset(eq.columns)
    metrics = set(eq["metric"])
    for required in (
        "fill_rate", "partial_fill_rate", "missing_quote_count",
        "spread_bps_p50", "spread_bps_p90", "spread_bps_p99",
        "quote_age_seconds_p50", "slippage_bps_p50",
        "liquidity_participation_p50", "fees_total",
        "historical_quote_coverage_pct",
    ):
        assert required in metrics, f"execution_quality.parquet missing {required}"
    # The summary surfaces the execution-quality counters too.
    assert "fill_rate" in result.summary
    assert "missing_quote_count" in result.summary
    assert "historical_quote_coverage_pct" in result.summary
