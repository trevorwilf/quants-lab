"""Phase 8: JSON summary schema matches §D.1."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bowaka_lab.reports.markdown import ReportInputs
from bowaka_lab.reports.weekly_report import generate_weekly_report


def test_summary_json_top_level_keys(tmp_path: Path):
    res = generate_weekly_report(
        output_dir=tmp_path,
        inputs=ReportInputs(run_id="bt_test", config_hash="sha256:abc"),
    )
    summary = json.loads(res.summary_path.read_text())
    for k in ("run_id", "status_label", "config_hash", "dataset_hashes", "data", "prefilter", "performance", "top_findings", "blockers", "next_actions"):
        assert k in summary


def test_summary_performance_subkeys(tmp_path: Path):
    res = generate_weekly_report(output_dir=tmp_path, inputs=ReportInputs(run_id="bt", config_hash="sha256:c"))
    perf = json.loads(res.summary_path.read_text())["performance"]
    for k in ("trade_count", "total_pnl_pct", "mean_trade_pct", "median_trade_pct", "win_rate", "max_drawdown_pct"):
        assert k in perf


def test_summary_data_block(tmp_path: Path):
    res = generate_weekly_report(output_dir=tmp_path, inputs=ReportInputs(run_id="bt", config_hash="sha256:c"))
    data = json.loads(res.summary_path.read_text())["data"]
    assert data["vendor"] == "alpaca"
    assert "known_biases" in data
