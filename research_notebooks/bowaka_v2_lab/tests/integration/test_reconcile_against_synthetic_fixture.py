"""Phase 4 (audit 2026-05-29 §9 Phase 6) — reconcile against the synthetic fixture.

The single frozen session reconciles near-perfectly (injected matching
reconciler) but the report is still BELOW_MIN_SESSIONS (1 < 10), so it is not
promotion-eligible.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile.orchestrator import (
    SessionReconcileResult,
    run_reconciliation,
)


def _matching(session_dir, cfg, lake_root) -> SessionReconcileResult:
    return SessionReconcileResult(
        session_date=session_dir.name, n_paper_candidates=8, n_sim_candidates=8,
        candidate_recall=1.0, gate_match=1.0, entry_decision_match=1.0,
        fill_match=1.0, fill_price_mae_bps=1.5, exit_reason_match=1.0,
        bracket_attach_match=1.0, daily_pnl_sign_match=1.0,
    )


def test_reconcile_fixture_one_session_below_min(lab_root: Path) -> None:
    root = lab_root / "tests" / "fixtures" / "paper_logs"
    report = run_reconciliation(paper_logs_root=root, cfg={}, reconcile_one=_matching)
    assert report.n_sessions == 1
    assert report.aggregate["candidate_recall"] == 1.0
    assert report.status == "BELOW_MIN_SESSIONS"
    assert report.passes_all_thresholds is False
