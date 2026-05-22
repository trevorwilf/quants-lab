"""Paper-vs-sim/lab reconciliation.

Two layers live here:

- Phase 7 — the dict-based importer / comparator / slippage-residual path and
  the mismatch-category report (``paper_log_schema``, ``importer``,
  ``comparator``, ``slippage_residuals``, ``render_reconciliation_report``).
- Phase 10 — the realism-audit reconciliation framework: typed Pydantic
  ``schemas``, ``comparators`` keyed on ``candidate_event_id``, the
  ``replay`` path (run the lab in ``current_code_parity`` against a paper day)
  and the ``render_realism_reconciliation_report`` markdown + JSON renderer.
"""
from .paper_log_schema import (
    CANDIDATE_FIELDS, DECISION_FIELDS, ORDER_FIELDS, FILL_FIELDS,
    validate_paper_record,
)
from .importer import import_paper_logs, PaperLogImportResult
from .comparator import (
    ComparatorResult, MatchEntry, compare_candidates,
)
from .slippage_residuals import compute_slippage_residuals
from .report import (
    render_reconciliation_report, REPORT_CATEGORIES,
    build_reconcile_report, render_realism_reconciliation_report,
)
from .schemas import (
    PaperCandidate, PaperDecision, PaperOrder, PaperFill, PaperExit,
    LabCandidate, LabDecision, LabOrder, LabFill, LabExit,
    ReconcileRow, ReconcileReport,
)
from .comparators import (
    CandidateSetDiff, diff_candidate_sets,
    DecisionReasonComparison, compare_decision_reason,
    compare_order_size, FillComparison, compare_fill,
    compare_exit_reason, compare_pnl,
)
from .replay import (
    ReplayResult, replay_paper_session, load_paper_session,
    run_lab_parity_session, build_reconcile_rows,
)

__all__ = [
    # Phase 7
    "CANDIDATE_FIELDS", "DECISION_FIELDS", "ORDER_FIELDS", "FILL_FIELDS",
    "validate_paper_record",
    "import_paper_logs", "PaperLogImportResult",
    "ComparatorResult", "MatchEntry", "compare_candidates",
    "compute_slippage_residuals",
    "render_reconciliation_report", "REPORT_CATEGORIES",
    # Phase 10 — schemas
    "PaperCandidate", "PaperDecision", "PaperOrder", "PaperFill", "PaperExit",
    "LabCandidate", "LabDecision", "LabOrder", "LabFill", "LabExit",
    "ReconcileRow", "ReconcileReport",
    # Phase 10 — comparators
    "CandidateSetDiff", "diff_candidate_sets",
    "DecisionReasonComparison", "compare_decision_reason",
    "compare_order_size", "FillComparison", "compare_fill",
    "compare_exit_reason", "compare_pnl",
    # Phase 10 — replay + report
    "ReplayResult", "replay_paper_session", "load_paper_session",
    "run_lab_parity_session", "build_reconcile_rows",
    "build_reconcile_report", "render_realism_reconciliation_report",
]
