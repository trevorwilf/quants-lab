"""All Phase-8 substantive sections present in render_run_report output."""
from __future__ import annotations

import json
from pathlib import Path

from bowaka_v2_lab.reports.render_run_report import render_run_report


#: The Phase-8 substantive section set the report always carries.
_EXPECTED_HEADINGS = [
    "# Bowaka v2 Backtest Report",
    "## Header",
    "## Data Quality",
    "## Universe Funnel",
    "## Scan Replay Summary",
    "## Gate Funnel",
    "## Entry Decision Funnel",
    "## Execution Quality",
    "## Portfolio and Risk",
    "## Trade Performance",
    "## Exit Analysis",
    "## Regime Analysis",
    "## Config Diff and Lineage",
    "## Known Limitations",
    "## Promotion Checklist",
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
        "run_kind": "backtest",
    }))
    (rd / "data_quality_report.json").write_text(json.dumps({
        "schema_version": 2, "notes": "", "checks": [], "regime": "synthetic",
        "passed": 0, "failed": 0, "warned": 0, "required_failures": [],
    }))
    (rd / "dataset_manifest.json").write_text(json.dumps({
        "provider": "fixture", "feed": "iex", "bar_count": 0, "symbols": [],
    }))
    out = render_run_report(rd, suitability="backtesting_only")
    for heading in _EXPECTED_HEADINGS:
        assert heading in out, f"missing required heading: {heading!r}"
    # Suitability tier appears in the report.
    assert "backtesting_only" in out
    # The Phase-8 report must not carry stub language.
    lowered = out.lower()
    assert "stub" not in lowered
    assert "phase 5 fills" not in lowered
    assert "phase n fills" not in lowered
