"""Phase 4 (audit 2026-05-29 §9 Phase 6) — fewer than min sessions -> deferred."""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile.orchestrator import (
    SessionReconcileResult,
    run_reconciliation,
)


def _ok(session_dir, cfg, lake_root) -> SessionReconcileResult:
    return SessionReconcileResult(
        session_date=session_dir.name, n_paper_candidates=5, n_sim_candidates=5,
        candidate_recall=1.0, gate_match=1.0, entry_decision_match=1.0,
        fill_match=1.0, fill_price_mae_bps=1.0, exit_reason_match=1.0,
        bracket_attach_match=1.0, daily_pnl_sign_match=1.0,
    )


def test_five_sessions_below_min_ten(tmp_path: Path) -> None:
    for day in range(1, 6):
        d = tmp_path / f"2024-09-0{day}"
        d.mkdir()
        (d / "paper_candidates.jsonl").write_text("{}\n", encoding="utf-8")
    report = run_reconciliation(
        paper_logs_root=tmp_path,
        cfg={"reconcile": {"min_sessions_for_promotion": 10}},
        reconcile_one=_ok,
    )
    assert report.n_sessions == 5
    assert report.status == "BELOW_MIN_SESSIONS"
    assert report.passes_all_thresholds is False
