"""Suitability tiers per [Report §9.11].

HARD CAP per [Report §1.2, §21]: any of these conditions caps the tier at
``backtesting_only`` or below:
- ``feed == "iex"``      → ``research_only``
- no walk-forward holdout evidence in run_dir
- no paper-recon residual artifact in run_dir

This is mechanical: the promotion code in this lab can NEVER claim higher than
``backtesting_only`` because SIP walk-forward + paper-vs-sim reconciliation are
explicit prerequisites for higher tiers and the lab does not produce both.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

SUITABILITY_TIERS = ("research_only", "backtesting_only", "paper_candidate", "live_candidate")
SuitabilityTier = Literal["research_only", "backtesting_only", "paper_candidate", "live_candidate"]


def _summary(run_dir: Path) -> dict:
    p = Path(run_dir) / "summary.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def _has_walkforward_holdout_artifact(run_dir: Path) -> bool:
    """Check for a walk-forward holdout evidence file in run_dir or sibling optuna dir."""
    rd = Path(run_dir)
    for cand in (rd / "walkforward_holdout.json", rd.parent / "optuna" / "walkforward_holdout.json"):
        if cand.is_file():
            return True
    return False


def _has_paper_recon_artifact(run_dir: Path) -> bool:
    rd = Path(run_dir)
    for cand in (
        rd / "reconciliation_report.md",
        rd / "slippage_residuals.parquet",
        rd.parent / "reconcile" / "reconciliation_report.md",
    ):
        if cand.is_file():
            return True
    return False


def decide_suitability(run_dir: Path, checklist_results: dict | None = None) -> SuitabilityTier:
    """Mechanical suitability decision.

    Returns the highest tier consistent with available evidence, subject to the
    documented hard caps. Never returns ``paper_candidate`` or ``live_candidate``
    from this lab's evidence alone (Report §1.2 / §21).
    """
    rd = Path(run_dir)
    summary = _summary(rd)
    feed = summary.get("feed", "iex")

    # Check for blocking gate failures (anything that's "fail" in the checklist).
    if checklist_results:
        for item_id, (status, _ev) in checklist_results.items():
            if status == "fail":
                return "research_only"

    # IEX → research_only hard cap.
    if feed == "iex":
        return "research_only"

    # Without walk-forward holdout evidence → backtesting_only at best.
    has_wf = _has_walkforward_holdout_artifact(rd)
    has_recon = _has_paper_recon_artifact(rd)
    if not has_wf or not has_recon:
        return "backtesting_only"

    # Even with both evidence types, this lab's mechanical verdict caps at
    # backtesting_only — promoting requires an out-of-band operator decision per §21.
    return "backtesting_only"
