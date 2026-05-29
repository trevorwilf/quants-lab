"""Phase 4 (audit 2026-05-29 §9 Phase 6) — empty logs root -> REAL_LOGS_DEFERRED."""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.reconcile.orchestrator import run_reconciliation


def test_no_logs_returns_deferred(tmp_path: Path) -> None:
    report = run_reconciliation(paper_logs_root=tmp_path, cfg={})
    assert report.status == "REAL_LOGS_DEFERRED"
    assert report.n_sessions == 0
    assert report.passes_all_thresholds is False
    assert report.failing_metrics == ["REAL_LOGS_DEFERRED"]
