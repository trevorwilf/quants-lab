"""End-to-end reconciliation on the bundled minimal fixture."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from bowaka_v2_lab.reconcile.comparator import compare_candidates
from bowaka_v2_lab.reconcile.importer import import_paper_logs
from bowaka_v2_lab.reconcile.report import render_reconciliation_report
from bowaka_v2_lab.reconcile.slippage_residuals import compute_slippage_residuals


_FIX = Path(__file__).resolve().parents[1] / "fixtures" / "paper_logs_minimal"


def test_end_to_end_no_sim_substitute_with_paper() -> None:
    imp = import_paper_logs(_FIX)
    # Substitute sim==paper for the smoke run; downstream tests will swap real sim.
    cmp_c = compare_candidates(imp.candidates, imp.candidates, window_seconds=120)
    cmp_d = compare_candidates(imp.decisions, imp.decisions, window_seconds=120)
    residuals = compute_slippage_residuals(imp.fills, imp.fills)
    md = render_reconciliation_report(
        candidate_match=cmp_c, decision_match=cmp_d,
        broker_reject_mismatches=[], slippage_residuals=residuals,
    )
    assert "Paper-vs-Sim" in md
    assert cmp_c.n_match == 4
    assert cmp_d.n_match == 3
    assert (residuals["residual"] == 0.0).all()
