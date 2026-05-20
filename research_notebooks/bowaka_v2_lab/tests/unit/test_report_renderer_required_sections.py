"""All 8 sections from [Report §13.12] present in render_run_report output."""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.reports.render_run_report import render_run_report


_EXPECTED_HEADINGS = [
    "# Bowaka v2 Backtest Report",
    "## Run Metrics",
    "## Data Quality",
    "## Trade Metrics",
    "## Liquidity & Execution",
    "## MFE / MAE",
    "## Gate Funnel",
]


def test_required_sections_present(tmp_path: Path) -> None:
    rd = tmp_path / "run"
    rd.mkdir()
    (rd / "summary.json").write_text(json.dumps({
        "run_id": "x", "feed": "iex", "cost_stress": "base", "n_trades": 0,
        "win_rate": 0.0, "total_pnl": 0.0, "net_return_pct": 0.0, "max_drawdown_pct": 0.0,
        "candidate_events_count": 0, "entry_decisions_count": 0, "accepted_count": 0,
        "rejected_count": 0, "broker_reject_count": 0, "ambiguous_bar_count": 0,
    }))
    (rd / "run_manifest.json").write_text(json.dumps({
        "run_id": "x", "strategy_version": "0.1.0", "created_at": "2024-09-04T00:00:00Z",
    }))
    (rd / "data_quality_report.json").write_text(json.dumps({"schema_version": 1, "notes": ""}))
    (rd / "dataset_manifest.json").write_text(json.dumps({
        "provider": "fixture", "feed": "iex", "bar_count": 0, "symbols": [],
    }))
    out = render_run_report(rd, suitability="backtesting_only")
    for heading in _EXPECTED_HEADINGS:
        assert heading in out, f"missing required heading: {heading!r}"
    # Suitability tier appears in the report.
    assert "backtesting_only" in out
