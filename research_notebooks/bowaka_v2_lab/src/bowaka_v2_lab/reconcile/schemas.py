"""Pydantic schemas for the paper-vs-lab reconciliation framework (Phase 10).

These are the *typed* records the realism-audit reconciliation path keys on.
They normalise two record sources into a single comparable shape:

- ``Paper*`` — a record read from a paper-trading session log
  (the ``reconcile.importer`` ingests raw JSONL into dicts; these models
  validate and normalise one row each).
- ``Lab*`` — the equivalent record produced by a lab backtest run in
  ``simulation.mode == current_code_parity`` over the same lake / universe /
  date (extracted from the :class:`~bowaka_v2_lab.sim.backtester.BacktestResult`).

``ReconcileRow`` is the side-by-side join of a paper record set and a lab
record set for one ``candidate_event_id``; ``ReconcileReport`` is the full
run-level reconciliation summary.

The Phase-7 ``reconcile`` package (``comparator`` / ``importer`` /
``paper_log_schema`` / ``slippage_residuals``) keeps its dict-based surface;
these models sit *alongside* it and are what the Phase-10 ``replay`` /
``comparators`` / realism-audit ``report`` consume.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class _ReconBase(BaseModel):
    """Tolerant base — paper logs evolve, so unknown keys are kept, not rejected."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


# --------------------------------------------------------------------------
# Paper-side records (one row of a paper-trading session log).
# --------------------------------------------------------------------------
class PaperCandidate(_ReconBase):
    """A candidate-signal event from a paper session's ``candidate_events`` log."""

    event_id: str
    session_date: Optional[str] = None
    symbol: str
    scan_timestamp: Optional[str] = None
    signal_strength: Optional[float] = None


class PaperDecision(_ReconBase):
    """An entry-decision from a paper session's ``entry_decisions`` log."""

    event_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    session_date: Optional[str] = None
    symbol: str
    decision: Optional[str] = None
    reason: Optional[str] = None
    decision_timestamp: Optional[str] = None


class PaperOrder(_ReconBase):
    """A parent order from a paper session's ``orders`` log."""

    parent_order_id: str
    candidate_event_id: Optional[str] = None
    symbol: str
    side: Optional[str] = None
    qty: Optional[float] = None
    limit_price: Optional[float] = None
    submit_timestamp: Optional[str] = None
    status: Optional[str] = None


class PaperFill(_ReconBase):
    """A fill from a paper session's ``fills`` log."""

    parent_order_id: str
    candidate_event_id: Optional[str] = None
    symbol: str
    filled_qty: Optional[float] = None
    avg_fill_price: Optional[float] = None
    fill_timestamp: Optional[str] = None


class PaperExit(_ReconBase):
    """A lot exit from a paper session's ``exits`` log (per closed lot)."""

    parent_order_id: Optional[str] = None
    position_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    symbol: str
    exit_reason: Optional[str] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_timestamp: Optional[str] = None


# --------------------------------------------------------------------------
# Lab-side records (extracted from a current_code_parity BacktestResult).
# --------------------------------------------------------------------------
class LabCandidate(_ReconBase):
    """A candidate-signal event produced by the lab backtester."""

    event_id: str
    session_date: Optional[str] = None
    symbol: str
    scan_timestamp: Optional[str] = None
    signal_strength: Optional[float] = None


class LabDecision(_ReconBase):
    """An entry-decision produced by the lab backtester."""

    event_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    session_date: Optional[str] = None
    symbol: str
    decision: Optional[str] = None
    reason: Optional[str] = None
    decision_timestamp: Optional[str] = None


class LabOrder(_ReconBase):
    """A parent order produced by the lab backtester."""

    parent_order_id: str
    candidate_event_id: Optional[str] = None
    symbol: str
    side: Optional[str] = None
    qty: Optional[float] = None
    limit_price: Optional[float] = None
    submit_timestamp: Optional[str] = None
    status: Optional[str] = None


class LabFill(_ReconBase):
    """A fill produced by the lab backtester."""

    parent_order_id: str
    candidate_event_id: Optional[str] = None
    symbol: str
    filled_qty: Optional[float] = None
    avg_fill_price: Optional[float] = None
    fill_timestamp: Optional[str] = None


class LabExit(_ReconBase):
    """A lot exit produced by the lab backtester (per closed lot / trade)."""

    parent_order_id: Optional[str] = None
    position_id: Optional[str] = None
    candidate_event_id: Optional[str] = None
    symbol: str
    exit_reason: Optional[str] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    exit_timestamp: Optional[str] = None


# --------------------------------------------------------------------------
# Reconciliation row + report.
# --------------------------------------------------------------------------
class ReconcileRow(BaseModel):
    """Side-by-side paper vs lab records for one ``candidate_event_id``.

    ``presence`` is the candidate-set bucket: ``"both"`` (paper and lab both
    produced this candidate), ``"paper_only"`` (paper had it, the lab did not)
    or ``"lab_only"`` (the lab had it, paper did not).
    """

    model_config = ConfigDict(extra="forbid")

    candidate_event_id: str
    symbol: Optional[str] = None
    presence: str  # "both" | "paper_only" | "lab_only"

    paper_candidate: Optional[PaperCandidate] = None
    lab_candidate: Optional[LabCandidate] = None
    paper_decision: Optional[PaperDecision] = None
    lab_decision: Optional[LabDecision] = None
    paper_order: Optional[PaperOrder] = None
    lab_order: Optional[LabOrder] = None
    paper_fill: Optional[PaperFill] = None
    lab_fill: Optional[LabFill] = None
    paper_exit: Optional[PaperExit] = None
    lab_exit: Optional[LabExit] = None

    # Per-stage comparator outcomes (populated by ``comparators``). None means
    # the stage was not comparable (a record was missing on one side).
    decision_reason_match: Optional[bool] = None
    order_size_delta: Optional[float] = None
    fill_price_delta_bps: Optional[float] = None
    fill_qty_delta: Optional[float] = None
    exit_reason_match: Optional[bool] = None
    pnl_delta: Optional[float] = None


class ReconcileReport(BaseModel):
    """Run-level reconciliation summary for one paper session.

    ``stage_counts`` carries per-stage matched / mismatched / comparable counts;
    ``systematic_biases`` is an ordered list of detected directional biases (e.g.
    "lab over-fills"); ``residual_distributions`` carries the numeric residual
    summaries; ``calibration_suggestions`` is the operator-facing tuning advice.
    """

    model_config = ConfigDict(extra="forbid")

    session_date: str
    scaffolding_only: bool = False
    note: Optional[str] = None

    n_paper_candidates: int = 0
    n_lab_candidates: int = 0
    n_both: int = 0
    n_paper_only: int = 0
    n_lab_only: int = 0

    stage_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    systematic_biases: list[str] = Field(default_factory=list)
    residual_distributions: dict[str, dict[str, float]] = Field(default_factory=dict)
    calibration_suggestions: list[str] = Field(default_factory=list)
    rows: list[ReconcileRow] = Field(default_factory=list)


__all__ = [
    "PaperCandidate",
    "PaperDecision",
    "PaperOrder",
    "PaperFill",
    "PaperExit",
    "LabCandidate",
    "LabDecision",
    "LabOrder",
    "LabFill",
    "LabExit",
    "ReconcileRow",
    "ReconcileReport",
]
