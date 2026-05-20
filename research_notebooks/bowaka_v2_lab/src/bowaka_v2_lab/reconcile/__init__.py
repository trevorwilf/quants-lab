"""Paper-vs-sim reconciliation (Phase 7)."""
from .paper_log_schema import (
    CANDIDATE_FIELDS, DECISION_FIELDS, ORDER_FIELDS, FILL_FIELDS,
    validate_paper_record,
)
from .importer import import_paper_logs, PaperLogImportResult
from .comparator import (
    ComparatorResult, MatchEntry, compare_candidates,
)
from .slippage_residuals import compute_slippage_residuals
from .report import render_reconciliation_report, REPORT_CATEGORIES

__all__ = [
    "CANDIDATE_FIELDS", "DECISION_FIELDS", "ORDER_FIELDS", "FILL_FIELDS",
    "validate_paper_record",
    "import_paper_logs", "PaperLogImportResult",
    "ComparatorResult", "MatchEntry", "compare_candidates",
    "compute_slippage_residuals",
    "render_reconciliation_report", "REPORT_CATEGORIES",
]
