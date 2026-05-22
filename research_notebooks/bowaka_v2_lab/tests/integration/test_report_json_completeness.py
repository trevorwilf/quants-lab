"""Phase 8 — report.json is written and carries every required metric table.

The machine-readable ``report.json`` is the artifact downstream Optuna and
reconciliation consume. It must mirror the report's sections and present every
metric in tabular form (lists of row dicts), not as free text.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.reports.render_run_report import REPORT_SECTIONS
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars


def _run(tmp_path: Path):
    paths = BowakaV2Paths(
        lab_root=tmp_path / "r" / "bowaka_v2_lab",
        data_root=tmp_path / "r" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "r" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    sd = _dt.date(2024, 9, 4)
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "sip", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                 "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                 "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                     "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                            minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {sd: {"universe_hash": "sha256:t",
                     "symbols": [{"symbol": "AAA", "exchange": "NASDAQ",
                                  "venue_code": "XNAS",
                                  "instrument_class": "operating_equity",
                                  "eligible_for_bowaka_equity_bucket": True}]}}
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                      "avg_dollar_volume_20d": 5_000_000,
                                      "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}])}
    return run_backtest(
        cfg=cfg, sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda s, t: bars,
        daily_bars_supplier=lambda s, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0, paths=paths,
    )


def test_report_json_written(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert (result.run_dir / "report.json").is_file(), "report.json not written"


def test_report_json_carries_every_section(tmp_path: Path) -> None:
    result = _run(tmp_path)
    rpt = json.loads((result.run_dir / "report.json").read_text(encoding="utf-8"))
    assert rpt.get("sections") == list(REPORT_SECTIONS)
    for section in REPORT_SECTIONS:
        assert section in rpt, f"report.json missing section {section!r}"
    assert rpt.get("suitability_tier")
    assert rpt.get("schema_version") == 1


def test_report_json_metric_tables_are_tabular(tmp_path: Path) -> None:
    """Every metric surface is a list of row dicts (consumable without parsing MD)."""
    result = _run(tmp_path)
    rpt = json.loads((result.run_dir / "report.json").read_text(encoding="utf-8"))

    # Header — field/value rows.
    assert isinstance(rpt["header"]["fields"], list)
    assert all({"field", "value"} <= set(r) for r in rpt["header"]["fields"])

    # Data quality — checks list.
    assert isinstance(rpt["data_quality"]["checks"], list)

    # Execution quality — metric/value rows.
    assert isinstance(rpt["execution_quality"]["metrics"], list)
    if rpt["execution_quality"]["metrics"]:
        assert all({"metric", "value"} <= set(r)
                   for r in rpt["execution_quality"]["metrics"])

    # Trade performance — metric/value rows + a numeric trade count.
    assert isinstance(rpt["trade_performance"]["metrics"], list)
    assert isinstance(rpt["trade_performance"]["n_closed_trades"], int)

    # Entry decision funnel — stage/count rows.
    assert isinstance(rpt["entry_decision_funnel"]["stages"], list)
    assert all({"stage", "count"} <= set(r)
               for r in rpt["entry_decision_funnel"]["stages"])

    # Portfolio and risk — metric rows.
    assert isinstance(rpt["portfolio_and_risk"]["metrics"], list)

    # Exit analysis — exit-reason counts table.
    ea = rpt["exit_analysis"]
    assert "available" in ea
    if ea.get("available"):
        assert isinstance(ea["exit_reason_counts"], list)
        assert all({"exit_reason", "count"} <= set(r)
                   for r in ea["exit_reason_counts"])

    # Config diff + lineage — lineage rows + mismatch path list.
    cdl = rpt["config_diff_and_lineage"]
    assert isinstance(cdl["lineage"], list)
    assert isinstance(cdl["unannotated_mismatch_paths"], list)

    # Promotion checklist — every check has item / status / evidence(dict).
    checks = rpt["promotion_checklist"]["checks"]
    assert isinstance(checks, list) and checks
    for c in checks:
        assert {"item", "status", "evidence"} <= set(c)
        assert isinstance(c["evidence"], dict)
    totals = rpt["promotion_checklist"]["totals"]
    assert {"pass", "fail", "unknown", "total"} <= set(totals)
