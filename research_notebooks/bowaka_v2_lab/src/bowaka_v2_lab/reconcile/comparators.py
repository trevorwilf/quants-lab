"""Paper-vs-lab comparators for the realism-audit reconciliation (Phase 10).

Each comparator takes the paper side and the lab side of one reconciliation
stage and produces a typed delta. They are pure functions over the
:mod:`reconcile.schemas` models — no I/O — so the replay path, the report and
the tests can all call them directly.

Stages
------
- :func:`diff_candidate_sets`  — paper-only / lab-only / both buckets.
- :func:`compare_decision_reason` — entry-decision reason match per candidate.
- :func:`compare_order_size` — order-size (qty) delta.
- :func:`compare_fill` — fill-price delta (signed bps) and fill-qty delta.
- :func:`compare_exit_reason` — exit-reason match per lot.
- :func:`compare_pnl` — realized-PnL delta per lot.

The Phase-7 ``reconcile.comparator.compare_candidates`` (timestamp-window
matching of dict records) is unchanged and still used by the importer-based
path; these comparators key strictly on ``candidate_event_id``, which the lab
backtester and the paper logs both stamp on every downstream record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from .schemas import (
    LabCandidate,
    LabDecision,
    LabExit,
    LabFill,
    LabOrder,
    PaperCandidate,
    PaperDecision,
    PaperExit,
    PaperFill,
    PaperOrder,
)


# --------------------------------------------------------------------------
# Candidate-set diff.
# --------------------------------------------------------------------------
@dataclass
class CandidateSetDiff:
    """Result of :func:`diff_candidate_sets`.

    ``both`` / ``paper_only`` / ``lab_only`` are sorted lists of
    ``candidate_event_id`` values. The counts are convenience mirrors.
    """

    both: list[str] = field(default_factory=list)
    paper_only: list[str] = field(default_factory=list)
    lab_only: list[str] = field(default_factory=list)

    @property
    def n_both(self) -> int:
        return len(self.both)

    @property
    def n_paper_only(self) -> int:
        return len(self.paper_only)

    @property
    def n_lab_only(self) -> int:
        return len(self.lab_only)


def diff_candidate_sets(
    paper: Iterable[PaperCandidate],
    lab: Iterable[LabCandidate],
) -> CandidateSetDiff:
    """Bucket candidate-event ids into paper-only / lab-only / both.

    Keys strictly on ``event_id`` — the lab backtester and the paper scanner
    both emit a stable candidate ``event_id`` (``strategy:session:symbol:ts``),
    so the same candidate carries the same id on both sides.
    """
    paper_ids = {c.event_id for c in paper}
    lab_ids = {c.event_id for c in lab}
    return CandidateSetDiff(
        both=sorted(paper_ids & lab_ids),
        paper_only=sorted(paper_ids - lab_ids),
        lab_only=sorted(lab_ids - paper_ids),
    )


# --------------------------------------------------------------------------
# Decision-reason match.
# --------------------------------------------------------------------------
@dataclass
class DecisionReasonComparison:
    """Per-candidate entry-decision comparison.

    ``match`` is True only when both sides resolved the candidate to the same
    ``decision`` AND the same ``reason``. ``None`` for either side means that
    side had no decision record for the candidate (not comparable).
    """

    candidate_event_id: str
    paper_decision: Optional[str]
    lab_decision: Optional[str]
    paper_reason: Optional[str]
    lab_reason: Optional[str]
    match: Optional[bool]


def compare_decision_reason(
    candidate_event_id: str,
    paper: Optional[PaperDecision],
    lab: Optional[LabDecision],
) -> DecisionReasonComparison:
    """Compare the entry-decision (``decision`` + ``reason``) for one candidate."""
    p_dec = paper.decision if paper is not None else None
    l_dec = lab.decision if lab is not None else None
    p_reason = paper.reason if paper is not None else None
    l_reason = lab.reason if lab is not None else None
    match: Optional[bool]
    if paper is None or lab is None:
        match = None
    else:
        match = (p_dec == l_dec) and (p_reason == l_reason)
    return DecisionReasonComparison(
        candidate_event_id=candidate_event_id,
        paper_decision=p_dec,
        lab_decision=l_dec,
        paper_reason=p_reason,
        lab_reason=l_reason,
        match=match,
    )


# --------------------------------------------------------------------------
# Order-size delta.
# --------------------------------------------------------------------------
def compare_order_size(
    paper: Optional[PaperOrder],
    lab: Optional[LabOrder],
) -> Optional[float]:
    """Signed order-size delta ``lab.qty - paper.qty``.

    Positive => the lab ordered MORE than paper. ``None`` when either order is
    missing or carries no quantity (not comparable).
    """
    if paper is None or lab is None:
        return None
    if paper.qty is None or lab.qty is None:
        return None
    return float(lab.qty) - float(paper.qty)


# --------------------------------------------------------------------------
# Fill comparison — price delta (bps, signed) + quantity delta.
# --------------------------------------------------------------------------
@dataclass
class FillComparison:
    """Per-fill comparison.

    ``price_delta_bps`` is the signed fill-price residual in basis points,
    expressed relative to the paper fill price:

        price_delta_bps = (lab_price - paper_price) / paper_price * 10_000

    Positive => the lab filled at a HIGHER price than paper (worse for a buy,
    better for a sell). ``qty_delta`` is ``lab_qty - paper_qty``. Either field
    is ``None`` when the inputs to it are missing.
    """

    price_delta_bps: Optional[float]
    qty_delta: Optional[float]


def compare_fill(
    paper: Optional[PaperFill],
    lab: Optional[LabFill],
) -> FillComparison:
    """Compute the signed fill-price delta (bps) and the fill-quantity delta."""
    if paper is None or lab is None:
        return FillComparison(price_delta_bps=None, qty_delta=None)
    price_delta_bps: Optional[float] = None
    if (
        paper.avg_fill_price is not None
        and lab.avg_fill_price is not None
        and float(paper.avg_fill_price) != 0.0
    ):
        price_delta_bps = (
            (float(lab.avg_fill_price) - float(paper.avg_fill_price))
            / float(paper.avg_fill_price)
            * 10_000.0
        )
    qty_delta: Optional[float] = None
    if paper.filled_qty is not None and lab.filled_qty is not None:
        qty_delta = float(lab.filled_qty) - float(paper.filled_qty)
    return FillComparison(price_delta_bps=price_delta_bps, qty_delta=qty_delta)


# --------------------------------------------------------------------------
# Exit-reason match + PnL delta (per lot).
# --------------------------------------------------------------------------
def compare_exit_reason(
    paper: Optional[PaperExit],
    lab: Optional[LabExit],
) -> Optional[bool]:
    """True when paper and lab closed the lot for the same ``exit_reason``.

    ``None`` when either side has no exit record (the lot is still open on one
    side, or paper logs do not carry exits) — not comparable.
    """
    if paper is None or lab is None:
        return None
    return paper.exit_reason == lab.exit_reason


def compare_pnl(
    paper: Optional[PaperExit],
    lab: Optional[LabExit],
) -> Optional[float]:
    """Signed realized-PnL delta ``lab.realized_pnl - paper.realized_pnl``.

    Positive => the lab booked MORE PnL than paper for the lot. ``None`` when
    either exit is missing or carries no realized PnL.
    """
    if paper is None or lab is None:
        return None
    if paper.realized_pnl is None or lab.realized_pnl is None:
        return None
    return float(lab.realized_pnl) - float(paper.realized_pnl)


__all__ = [
    "CandidateSetDiff",
    "diff_candidate_sets",
    "DecisionReasonComparison",
    "compare_decision_reason",
    "compare_order_size",
    "FillComparison",
    "compare_fill",
    "compare_exit_reason",
    "compare_pnl",
]
