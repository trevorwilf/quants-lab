"""Phase fidelity-8: encode the §10 acceptance criteria as code.

Reads a run directory (under ``artifacts/<run_id>/``) and returns a
``PromotionCriteria`` describing whether the run earns ``paper_candidate``
or ``live_candidate`` status. The presence of blockers prevents promotion
silently passing; every blocker is named and added to the list so the
weekly report can render them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class PromotionCriteria:
    backtest_valid: bool
    paper_candidate: bool
    live_candidate: bool
    blockers: list[str] = field(default_factory=list)
    promotion_status: str = "research_only_paper_not_evaluated"


def _exists(path: Path) -> bool:
    try:
        return path.exists()
    except Exception:
        return False


def _read_json(path: Path) -> dict | None:
    if not _exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def evaluate_promotion(run_dir: Path | str) -> PromotionCriteria:
    """Return the promotion criteria for ``run_dir``.

    Acceptance steps:

    1. Required artifacts (config.json, summary.json, trades.parquet,
       candidates.parquet) must exist for ``backtest_valid``.
    2. Reconciliation status must be ``status='ok'`` with all
       implementation_mismatch / broker_rejection_mismatch /
       candidate_missing_in_backtest counts zero for ``paper_candidate``.
       ``status='skipped_no_paper_logs'`` → ``research_only_paper_not_evaluated``
       (never ``paper_candidate``).
    3. ``live_candidate`` requires SIP data + point-in-time universe,
       which is out of scope for the current phase — always False.
    """
    run_dir = Path(run_dir)
    blockers: list[str] = []

    # Required artifacts.
    required = [
        ("config.json",      run_dir / "config.json"),
        ("summary.json",     run_dir / "summary.json"),
        ("trades.parquet",   run_dir / "trades.parquet"),
        ("candidates.parquet", run_dir / "candidates.parquet"),
    ]
    for name, p in required:
        if not _exists(p):
            blockers.append(f"missing_required_artifact:{name}")
    backtest_valid = all(_exists(p) for _, p in required)

    # Reconciliation status.
    recon_status_json = _read_json(run_dir / "reconciliation_status.json")
    promotion_status = "research_only_paper_not_evaluated"
    paper_candidate = False
    if recon_status_json is None:
        blockers.append("missing_reconciliation_status_json")
    else:
        status = recon_status_json.get("status")
        if status == "skipped_no_paper_logs":
            promotion_status = "research_only_paper_not_evaluated"
            # not a blocker — research-only runs are explicitly allowed.
        elif status == "ok":
            unexplained = 0
            for key in (
                "implementation_mismatch_count",
                "broker_rejection_mismatch_count",
                "candidate_missing_in_backtest_count",
            ):
                v = recon_status_json.get(key)
                if v is not None and int(v) > 0:
                    unexplained += int(v)
                    blockers.append(f"reconciliation_unexplained:{key}={v}")
            if unexplained == 0 and backtest_valid:
                paper_candidate = True
                promotion_status = "paper_candidate"
            else:
                promotion_status = "paper_blocked"
        else:
            blockers.append(f"reconciliation_status_unrecognized:{status!r}")

    # Live candidate gated on SIP + point-in-time universe (out of scope).
    live_candidate = False

    return PromotionCriteria(
        backtest_valid=backtest_valid,
        paper_candidate=paper_candidate,
        live_candidate=live_candidate,
        blockers=blockers,
        promotion_status=promotion_status,
    )
