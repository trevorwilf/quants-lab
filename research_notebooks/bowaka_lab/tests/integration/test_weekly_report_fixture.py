"""Phase 8: end-to-end weekly report on a small completed-backtest fixture."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

from bowaka_lab.reports.markdown import ReportInputs
from bowaka_lab.reports.weekly_report import generate_weekly_report


def _trades_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "trade_date": date(2026, 5, 11), "entry_price": 5.0, "exit_price": 5.75, "pnl": 750, "pnl_pct": 0.15, "mfe_pct": 0.16, "mae_pct": -0.01, "exit_reason": "target_hit", "notional": 5000.0},
            {"symbol": "BBB", "trade_date": date(2026, 5, 11), "entry_price": 10.0, "exit_price": 9.2, "pnl": -400, "pnl_pct": -0.08, "mfe_pct": 0.01, "mae_pct": -0.085, "exit_reason": "stop_hit", "notional": 5000.0},
            {"symbol": "CCC", "trade_date": date(2026, 5, 11), "entry_price": 4.0, "exit_price": 4.04, "pnl": 50, "pnl_pct": 0.01, "mfe_pct": 0.015, "mae_pct": -0.005, "exit_reason": "time_stop", "notional": 5000.0},
        ]
    )


def _counterfactuals_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "would_enter": True, "pnl_pct": 0.15, "first_touch": "target", "variant": {"entry_rule": "fixed_time_0945", "stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3, "signal_fade_threshold": None, "stop_manager_model": "none"}},
            {"symbol": "BBB", "would_enter": True, "pnl_pct": -0.08, "first_touch": "stop", "variant": {"entry_rule": "fixed_time_0945", "stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3, "signal_fade_threshold": None, "stop_manager_model": "none"}},
        ]
    )


def test_weekly_report_writes_md_and_json(tmp_path: Path):
    res = generate_weekly_report(
        output_dir=tmp_path,
        inputs=ReportInputs(
            run_id="bt_2026-05-11_iex",
            config_hash="sha256:abc",
            dataset_hashes={"daily_bars": "sha256:d1", "minute_bars": "sha256:d2"},
            data_feed="iex",
            universe_mode="alpaca_current_assets",
            trades=_trades_fixture(),
            counterfactuals=_counterfactuals_fixture(),
            reconciliation=pd.DataFrame([{"classification": "candidate_match"}]),
            has_walk_forward=False,
            known_limitations=["IEX-only", "survivorship-biased"],
            next_actions=["Run SIP validation", "Add walk-forward"],
        ),
    )
    assert res.markdown_path.exists()
    md = res.markdown_path.read_text()
    # Trade-level summary appears (count, win rate) and section structure is intact.
    assert "trade_count" in md
    assert "win_rate" in md
    assert "research-grade exploratory evidence" in md

    summary = json.loads(res.summary_path.read_text())
    assert summary["run_id"] == "bt_2026-05-11_iex"
    assert summary["performance"]["trade_count"] == 3
    assert summary["performance"]["win_rate"] > 0
