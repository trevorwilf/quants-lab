"""Multi-session `reconcile` emits the markdown gate artifact.

The promotion gate (`promotion.suitability._has_paper_recon_artifact`) detects
`reconciliation_report.md`. The multi-session path historically wrote only JSON,
so a real multi-session reconciliation could not satisfy the gate. These tests
pin the renderer and that the CLI writes the `.md` next to the JSON (and only
when a real reconciliation ran, so a 0-session deferred run can't spoof it).
"""
from __future__ import annotations

from bowaka_v2_lab import cli
from bowaka_v2_lab.promotion.suitability import _has_paper_recon_artifact
from bowaka_v2_lab.reconcile import orchestrator


def _sess(**over):
    base = dict(
        session_date="2026-07-08", n_paper_candidates=4, n_sim_candidates=4,
        candidate_recall=1.0, gate_match=1.0, entry_decision_match=1.0,
        fill_match=0.9, fill_price_mae_bps=2.0, exit_reason_match=1.0,
        bracket_attach_match=1.0, daily_pnl_sign_match=1.0,
    )
    base.update(over)
    return orchestrator.SessionReconcileResult(**base)


def _report(n_sessions=1, status="BELOW_MIN_SESSIONS", failing=("fill_match",)):
    return orchestrator.ReconcileReport(
        n_sessions=n_sessions,
        aggregate={"candidate_recall": 1.0, "fill_match": 0.9, "fill_price_mae_bps": 2.0},
        per_session=[_sess()],
        thresholds=dict(orchestrator.DEFAULT_THRESHOLDS),
        passes_all_thresholds=False,
        failing_metrics=list(failing),
        status=status,
    )


def test_render_reconcile_report_md_contains_metrics():
    md = orchestrator.render_reconcile_report_md(_report())
    assert "# Bowaka v2 — Paper-vs-Lab Reconciliation" in md
    assert "candidate_recall" in md and "fill_match" in md
    assert "2026-07-08" in md          # per-session row
    assert "FAIL" in md                # verdict (passes_all_thresholds False)
    assert "fill_price_mae_bps" in md


def test_reconcile_multi_writes_md_and_gate_detects_it(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "run_reconciliation", lambda **_: _report())

    out = tmp_path / "reconcile" / "reconciliation_report.json"
    rc = cli.main(["reconcile", "--out", str(out)])

    md = out.parent / "reconciliation_report.md"
    assert md.is_file() and out.is_file()
    assert rc == 2  # BELOW_MIN_SESSIONS

    # The gate finds it via <run_dir>.parent/reconcile/reconciliation_report.md.
    run_dir = tmp_path / "lab_run"
    run_dir.mkdir()
    assert _has_paper_recon_artifact(run_dir) is True


def test_reconcile_multi_no_md_when_zero_sessions(tmp_path, monkeypatch):
    """A 0-session deferred run writes JSON only — no .md to spoof the gate."""
    monkeypatch.setattr(
        orchestrator, "run_reconciliation",
        lambda **_: orchestrator.ReconcileReport(
            n_sessions=0, aggregate={}, per_session=[],
            thresholds=dict(orchestrator.DEFAULT_THRESHOLDS),
            passes_all_thresholds=False, failing_metrics=["REAL_LOGS_DEFERRED"],
            status="REAL_LOGS_DEFERRED",
        ),
    )
    out = tmp_path / "reconcile" / "reconciliation_report.json"
    rc = cli.main(["reconcile", "--out", str(out)])

    assert out.is_file()
    assert not (out.parent / "reconciliation_report.md").exists()
    assert rc == 2

    run_dir = tmp_path / "lab_run"
    run_dir.mkdir()
    assert _has_paper_recon_artifact(run_dir) is False
