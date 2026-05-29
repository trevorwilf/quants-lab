"""Phase 4 (audit 2026-05-29 §9 Phase 6) — reconcile CLI exit codes.

0 = all thresholds pass; 1 = a threshold failed; 2 = deferred / below-min.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from bowaka_v2_lab import cli
from bowaka_v2_lab.reconcile import orchestrator as orch
from bowaka_v2_lab.reconcile.orchestrator import ReconcileReport


def _args(tmp_path: Path, root) -> argparse.Namespace:
    return argparse.Namespace(
        session_date=None, paper_logs_root=str(root), config=None,
        out=str(tmp_path / "recon.json"),
    )


def test_empty_root_exits_2(tmp_path: Path) -> None:
    # Real run over an empty dir -> REAL_LOGS_DEFERRED -> exit 2.
    rc = cli._cmd_reconcile(_args(tmp_path, tmp_path / "empty"))
    assert rc == 2


def test_below_min_exits_2(tmp_path: Path, monkeypatch) -> None:
    report = ReconcileReport(
        n_sessions=1, aggregate={}, per_session=[], thresholds={},
        passes_all_thresholds=False, failing_metrics=[], status="BELOW_MIN_SESSIONS",
    )
    monkeypatch.setattr(orch, "run_reconciliation", lambda **kw: report)
    assert cli._cmd_reconcile(_args(tmp_path, tmp_path)) == 2


def test_all_pass_exits_0(tmp_path: Path, monkeypatch) -> None:
    report = ReconcileReport(
        n_sessions=12, aggregate={"candidate_recall": 1.0}, per_session=[],
        thresholds={}, passes_all_thresholds=True, failing_metrics=[], status="ok",
    )
    monkeypatch.setattr(orch, "run_reconciliation", lambda **kw: report)
    assert cli._cmd_reconcile(_args(tmp_path, tmp_path)) == 0


def test_threshold_fail_exits_1(tmp_path: Path, monkeypatch) -> None:
    report = ReconcileReport(
        n_sessions=12, aggregate={}, per_session=[], thresholds={},
        passes_all_thresholds=False, failing_metrics=["fill_match"], status="ok",
    )
    monkeypatch.setattr(orch, "run_reconciliation", lambda **kw: report)
    assert cli._cmd_reconcile(_args(tmp_path, tmp_path)) == 1
