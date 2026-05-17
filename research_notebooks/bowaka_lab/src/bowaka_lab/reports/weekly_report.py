"""Weekly research-report orchestrator.

Combines candidate, trade, counterfactual, and reconciliation artifacts into a
Markdown report plus a JSON summary that matches ``[Report §D.1]``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from bowaka_lab.reports.markdown import ReportInputs, build_markdown, research_status_flags


@dataclass
class WeeklyReportResult:
    markdown_path: Path
    summary_path: Path
    summary: dict[str, Any]


def generate_weekly_report(
    *,
    output_dir: Path | str,
    inputs: ReportInputs,
) -> WeeklyReportResult:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"weekly_report_{inputs.run_id}.md"
    json_path = output_dir / f"weekly_report_{inputs.run_id}.json"

    md_path.write_text(build_markdown(inputs), encoding="utf-8")

    trades = inputs.trades
    summary = {
        "run_id": inputs.run_id,
        "status_label": "RESEARCH_ONLY",
        "config_hash": inputs.config_hash,
        "dataset_hashes": inputs.dataset_hashes,
        "data": {
            "vendor": inputs.data_vendor,
            "feed": inputs.data_feed,
            "adjustment": inputs.adjustment,
            "universe_mode": inputs.universe_mode,
            "known_biases": research_status_flags(inputs),
        },
        "prefilter": {
            "signal_dates": int(inputs.prefilter_metadata.get("n_signal_dates", 0)),
            "total_candidates": int(inputs.prefilter_metadata.get("n_candidates", 0)),
            "median_candidates_per_day": float(inputs.prefilter_metadata.get("median_candidates_per_day", 0.0) or 0.0),
        },
        "performance": _performance_block(trades),
        "top_findings": [],
        "blockers": [],
        "next_actions": list(inputs.next_actions),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    return WeeklyReportResult(markdown_path=md_path, summary_path=json_path, summary=summary)


def _performance_block(trades: pd.DataFrame) -> dict[str, Any]:
    if trades is None or trades.empty:
        return {
            "trade_count": 0,
            "total_pnl_pct": 0.0,
            "mean_trade_pct": 0.0,
            "median_trade_pct": 0.0,
            "win_rate": 0.0,
            "max_drawdown_pct": 0.0,
        }
    pnl = trades.get("pnl_pct", pd.Series(dtype=float))
    wins = (pnl > 0).sum() if not pnl.empty else 0
    return {
        "trade_count": int(trades.shape[0]),
        "total_pnl_pct": float(pnl.sum()) if not pnl.empty else 0.0,
        "mean_trade_pct": float(pnl.mean()) if not pnl.empty else 0.0,
        "median_trade_pct": float(pnl.median()) if not pnl.empty else 0.0,
        "win_rate": float(wins / max(1, trades.shape[0])),
        "max_drawdown_pct": 0.0,
    }
