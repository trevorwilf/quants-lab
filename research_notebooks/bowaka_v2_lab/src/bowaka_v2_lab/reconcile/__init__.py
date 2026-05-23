"""Paper-vs-sim/lab reconciliation.

Three layers live here:

- Phase 7 — the dict-based importer / comparator / slippage-residual path and
  the mismatch-category report (``paper_log_schema``, ``importer``,
  ``comparator``, ``slippage_residuals``, ``render_reconciliation_report``).
- Phase 10 — the realism-audit reconciliation framework: typed Pydantic
  ``schemas``, ``comparators`` keyed on ``candidate_event_id``, the
  ``replay`` path (run the lab in ``current_code_parity`` against a paper day)
  and the ``render_realism_reconciliation_report`` markdown + JSON renderer.
- Realism remediation 2 Phase 9 — the expanded event taxonomy + the seven
  aggregate comparators (emission Jaccard, decision-reason confusion, fill
  price+qty residuals, fill latency, OCO attempt count, exit reason+timing,
  PnL residuals), the per-(spread, ADV, volatility) slippage calibrator and
  the per-(symbol_liquidity_tier, time_of_day) OCO attach-latency calibrator,
  exposed through :func:`build_phase9_recon_report` /
  :func:`render_phase9_recon_report` and the CLI ``reconcile`` subcommand.
"""
from .paper_log_schema import (
    CANDIDATE_FIELDS, DECISION_FIELDS, ORDER_FIELDS, FILL_FIELDS,
    validate_paper_record,
    # Phase 9 typed event models.
    PaperCandidateEvent, PaperDecisionEvent,
    PaperParentSubmit, PaperParentAck, PaperParentFill,
    PaperOCOAttempt, PaperOCOAttached, PaperChildFill,
    PaperPositionClose, PaperDailySummary,
    PAPER_EVENT_MODELS, validate_paper_event,
)
from .importer import (
    import_paper_logs, PaperLogImportResult,
    # Phase 9 typed reader.
    PaperEventImportResult, PaperLogsNotFoundError,
    PAPER_EVENT_FILES, import_paper_event_logs, resolve_paper_logs_root,
)
from .comparator import (
    ComparatorResult, MatchEntry, compare_candidates,
    # Phase 9 tolerance config.
    DEFAULT_RECONCILE_TOLERANCES, load_reconcile_tolerances,
)
from .slippage_residuals import (
    compute_slippage_residuals,
    # Phase 9 slippage calibrator.
    FillFeatureRow, SlippageCalibratorArtifact,
    fit_slippage_calibrator, write_slippage_calibrator,
    load_slippage_calibrator, calibrator_lookup_bps,
    DEFAULT_SPREAD_BIN_EDGES_BPS, DEFAULT_ADV_BIN_EDGES_SHARES, DEFAULT_VOL_BIN_EDGES,
)
from .oco_latency_calibrator import (
    LIQUIDITY_TIERS, TIME_OF_DAY_BINS, time_of_day_bin,
    OCOLatencyObservation, OCOLatencyArtifact,
    fit_oco_latency_calibrator, write_oco_latency_calibrator,
    load_oco_latency_calibrator, calibrator_lookup_ms,
)
from .report import (
    render_reconciliation_report, REPORT_CATEGORIES,
    build_reconcile_report, render_realism_reconciliation_report,
    # Phase 9 report.
    build_phase9_recon_report, render_phase9_recon_report,
)
from .schemas import (
    PaperCandidate, PaperDecision, PaperOrder, PaperFill, PaperExit,
    LabCandidate, LabDecision, LabOrder, LabFill, LabExit,
    ReconcileRow, ReconcileReport,
)
from .comparators import (
    # Phase 10 per-stage comparators.
    CandidateSetDiff, diff_candidate_sets,
    DecisionReasonComparison, compare_decision_reason,
    compare_order_size, FillComparison, compare_fill,
    compare_exit_reason, compare_pnl,
    # Phase 9 aggregate comparators.
    EmissionJaccard, emission_jaccard,
    DecisionReasonConfusion, decision_reason_confusion,
    FillResidual, FillResidualSummary, fill_residuals,
    FillLatencyResidual, FillLatencySummary, fill_latency_residuals,
    OCOAttemptCountDiff, oco_attempt_count_diff,
    ExitReasonTiming, ExitReasonTimingSummary, exit_reason_timing,
    PnLResidual, PnLResidualSummary, pnl_residuals,
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
    # Phase 9 — typed event models
    "PaperCandidateEvent", "PaperDecisionEvent",
    "PaperParentSubmit", "PaperParentAck", "PaperParentFill",
    "PaperOCOAttempt", "PaperOCOAttached", "PaperChildFill",
    "PaperPositionClose", "PaperDailySummary",
    "PAPER_EVENT_MODELS", "validate_paper_event",
    # Phase 9 — typed reader
    "PaperEventImportResult", "PaperLogsNotFoundError",
    "PAPER_EVENT_FILES", "import_paper_event_logs", "resolve_paper_logs_root",
    # Phase 9 — tolerances
    "DEFAULT_RECONCILE_TOLERANCES", "load_reconcile_tolerances",
    # Phase 9 — slippage calibrator
    "FillFeatureRow", "SlippageCalibratorArtifact",
    "fit_slippage_calibrator", "write_slippage_calibrator",
    "load_slippage_calibrator", "calibrator_lookup_bps",
    "DEFAULT_SPREAD_BIN_EDGES_BPS", "DEFAULT_ADV_BIN_EDGES_SHARES",
    "DEFAULT_VOL_BIN_EDGES",
    # Phase 9 — OCO latency calibrator
    "LIQUIDITY_TIERS", "TIME_OF_DAY_BINS", "time_of_day_bin",
    "OCOLatencyObservation", "OCOLatencyArtifact",
    "fit_oco_latency_calibrator", "write_oco_latency_calibrator",
    "load_oco_latency_calibrator", "calibrator_lookup_ms",
    # Phase 9 — aggregate comparators
    "EmissionJaccard", "emission_jaccard",
    "DecisionReasonConfusion", "decision_reason_confusion",
    "FillResidual", "FillResidualSummary", "fill_residuals",
    "FillLatencyResidual", "FillLatencySummary", "fill_latency_residuals",
    "OCOAttemptCountDiff", "oco_attempt_count_diff",
    "ExitReasonTiming", "ExitReasonTimingSummary", "exit_reason_timing",
    "PnLResidual", "PnLResidualSummary", "pnl_residuals",
    # Phase 9 — report
    "build_phase9_recon_report", "render_phase9_recon_report",
]
