"""Render reconciliation_report.md with mismatch categories per [Report §13.10]."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


REPORT_CATEGORIES = (
    "candidate_miss",
    "entry_decision_miss",
    "broker_rejection_mismatch",
    "slippage_outlier",
)


def render_reconciliation_report(
    *,
    candidate_match,
    decision_match,
    broker_reject_mismatches: Iterable[dict] | None = None,
    slippage_residuals: pd.DataFrame | None = None,
    out_path: Path | None = None,
) -> str:
    lines = ["# Paper-vs-Sim Reconciliation Report", ""]
    # Candidates section
    lines.append("## Candidates")
    lines.append(f"- match: {candidate_match.n_match}")
    lines.append(f"- candidate_miss (paper without sim): {candidate_match.n_miss}")
    lines.append(f"- extra (sim without paper): {candidate_match.n_extra}")
    lines.append("")
    # Decisions section
    lines.append("## Entry Decisions")
    lines.append(f"- match: {decision_match.n_match}")
    lines.append(f"- entry_decision_miss: {decision_match.n_miss}")
    lines.append(f"- extra: {decision_match.n_extra}")
    lines.append("")
    # Broker rejection mismatches
    lines.append("## Broker Rejection Mismatches")
    n_brm = len(list(broker_reject_mismatches)) if broker_reject_mismatches is not None else 0
    lines.append(f"- broker_rejection_mismatch count: {n_brm}")
    lines.append("")
    # Slippage outliers
    lines.append("## Slippage")
    if slippage_residuals is not None and not slippage_residuals.empty:
        q99 = slippage_residuals["residual"].abs().quantile(0.99)
        outliers = slippage_residuals[slippage_residuals["residual"].abs() > q99]
        lines.append(f"- n trades compared: {len(slippage_residuals)}")
        lines.append(f"- residual abs p99: {q99:.5f}")
        lines.append(f"- slippage_outlier count: {len(outliers)}")
    else:
        lines.append("- (no slippage residuals provided)")
    lines.append("")
    content = "\n".join(lines) + "\n"
    if out_path is not None:
        Path(out_path).write_text(content, encoding="utf-8")
    return content
