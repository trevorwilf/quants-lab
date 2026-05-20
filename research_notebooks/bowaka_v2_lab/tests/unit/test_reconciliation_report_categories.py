"""Report includes the canonical mismatch categories."""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.reconcile.comparator import ComparatorResult
from bowaka_v2_lab.reconcile.report import REPORT_CATEGORIES, render_reconciliation_report


def test_report_includes_all_categories() -> None:
    md = render_reconciliation_report(
        candidate_match=ComparatorResult(matches=[], n_match=1, n_miss=2, n_extra=3),
        decision_match=ComparatorResult(matches=[], n_match=5, n_miss=0, n_extra=0),
        broker_reject_mismatches=[],
        slippage_residuals=pd.DataFrame({"residual": [0.01, 0.02, 0.5]}),
    )
    for cat in REPORT_CATEGORIES:
        assert cat in md, f"missing category {cat}"
