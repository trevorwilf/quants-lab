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


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 9 — set / aggregate comparators (with tolerances).
#
# These augment the per-stage Phase-10 comparators above with the seven
# tolerance-aware comparators the Phase-9 reconcile CLI flags:
#
#   1. candidate-emission match           — :func:`emission_jaccard`
#   2. accept/reject reason match         — :func:`decision_reason_confusion`
#   3. fill price + qty match             — :func:`fill_residuals`
#   4. fill latency match                 — :func:`fill_latency_residuals`
#   5. OCO attempt count match            — :func:`oco_attempt_count_diff`
#   6. exit reason + timing match         — :func:`exit_reason_timing`
#   7. PnL match (closed-trade)           — :func:`pnl_residuals`
#
# Each comparator is pure (no I/O) and returns a small dataclass keyed on the
# candidate id when relevant so the report and the calibration utilities can
# tabulate matched / mismatched / flagged buckets without reaching for the
# raw records again.
# --------------------------------------------------------------------------
import statistics
from typing import Mapping, Sequence

import pandas as pd


# --------------------------------------------------------------------------
# 1. candidate-emission match (emission Jaccard).
# --------------------------------------------------------------------------
@dataclass
class EmissionJaccard:
    """Candidate-emission match by Jaccard index.

    ``jaccard`` is |A ∩ B| / |A ∪ B| over candidate-event ids
    (``intersection / union``); 1.0 means paper and lab emit the EXACT same
    candidate set, 0.0 means they share nothing. ``intersection`` /
    ``union_size`` / ``paper_only`` / ``lab_only`` are convenience mirrors of
    the underlying ``CandidateSetDiff``. ``passes`` flags whether the run met
    the tolerance threshold (defaults to ``MIN_EMISSION_JACCARD`` = 0.85).
    """

    jaccard: float
    intersection: int
    union_size: int
    paper_only: int
    lab_only: int
    threshold: float
    passes: bool


def emission_jaccard(
    paper: Iterable[PaperCandidate] | Iterable[str],
    lab: Iterable[LabCandidate] | Iterable[str],
    *,
    threshold: float = 0.85,
) -> EmissionJaccard:
    """Candidate-emission match by Jaccard index over ``event_id``.

    Accepts either typed candidate models OR the raw ``event_id`` strings. An
    empty union returns ``jaccard=1.0`` (vacuous match — neither side emitted
    anything).
    """
    p_ids = {getattr(c, "event_id", c) for c in paper}
    l_ids = {getattr(c, "event_id", c) for c in lab}
    intersection = p_ids & l_ids
    union = p_ids | l_ids
    if not union:
        jac = 1.0
    else:
        jac = len(intersection) / len(union)
    return EmissionJaccard(
        jaccard=round(jac, 6),
        intersection=len(intersection),
        union_size=len(union),
        paper_only=len(p_ids - l_ids),
        lab_only=len(l_ids - p_ids),
        threshold=float(threshold),
        passes=jac >= float(threshold),
    )


# --------------------------------------------------------------------------
# 2. accept/reject reason match (confusion matrix).
# --------------------------------------------------------------------------
@dataclass
class DecisionReasonConfusion:
    """Aggregate decision-reason confusion across all candidates.

    ``confusion`` is a nested dict ``{paper_decision: {lab_decision: count}}``
    over the comparable candidate set. ``reason_confusion`` is the equivalent
    breakdown by ``reason`` (only counted when ``decision`` matched). ``match``
    is the fraction with paper.decision == lab.decision AND paper.reason ==
    lab.reason. ``passes`` flags whether the run met the tolerance threshold
    (defaults to ``MIN_DECISION_REASON_MATCH`` = 0.90).
    """

    comparable: int
    matched: int
    match: float
    confusion: dict[str, dict[str, int]]
    reason_confusion: dict[str, dict[str, int]]
    threshold: float
    passes: bool


def decision_reason_confusion(
    paper_decisions: Iterable[PaperDecision],
    lab_decisions: Iterable[LabDecision],
    *,
    threshold: float = 0.90,
) -> DecisionReasonConfusion:
    """Build the decision/reason confusion matrix over matched candidates."""
    p_by_cid: dict[str, PaperDecision] = {}
    for d in paper_decisions:
        cid = getattr(d, "candidate_event_id", None) or getattr(d, "event_id", None)
        if cid is not None:
            p_by_cid.setdefault(str(cid), d)
    l_by_cid: dict[str, LabDecision] = {}
    for d in lab_decisions:
        cid = getattr(d, "candidate_event_id", None) or getattr(d, "event_id", None)
        if cid is not None:
            l_by_cid.setdefault(str(cid), d)
    shared = sorted(set(p_by_cid) & set(l_by_cid))
    confusion: dict[str, dict[str, int]] = {}
    reason_confusion: dict[str, dict[str, int]] = {}
    matched = 0
    for cid in shared:
        p = p_by_cid[cid]
        l = l_by_cid[cid]
        pd_ = str(p.decision or "missing")
        ld = str(l.decision or "missing")
        confusion.setdefault(pd_, {}).setdefault(ld, 0)
        confusion[pd_][ld] += 1
        pr = str(p.reason or "missing")
        lr = str(l.reason or "missing")
        reason_confusion.setdefault(pr, {}).setdefault(lr, 0)
        reason_confusion[pr][lr] += 1
        if p.decision == l.decision and p.reason == l.reason:
            matched += 1
    match = matched / len(shared) if shared else 1.0
    return DecisionReasonConfusion(
        comparable=len(shared),
        matched=matched,
        match=round(match, 6),
        confusion=confusion,
        reason_confusion=reason_confusion,
        threshold=float(threshold),
        passes=match >= float(threshold),
    )


# --------------------------------------------------------------------------
# 3. fill price + qty match (within tolerance).
# --------------------------------------------------------------------------
@dataclass
class FillResidual:
    """One paired fill — paper vs lab — with signed residuals."""

    candidate_event_id: str
    symbol: Optional[str]
    paper_price: Optional[float]
    lab_price: Optional[float]
    price_delta_bps: Optional[float]
    paper_qty: Optional[float]
    lab_qty: Optional[float]
    qty_delta: Optional[float]
    flagged: bool  # True iff price OR qty exceeded the tolerance


@dataclass
class FillResidualSummary:
    """Aggregate paper-vs-lab fill comparison.

    ``residuals`` is one row per matched candidate-event-id; ``n_flagged`` is
    the count whose abs bps delta exceeded ``price_tolerance_bps`` OR whose
    abs qty delta exceeded ``qty_tolerance_shares``. ``passes`` flags whether
    every matched fill stayed within tolerance.
    """

    comparable: int
    n_flagged: int
    price_tolerance_bps: float
    qty_tolerance_shares: float
    median_price_delta_bps: float
    p95_abs_price_delta_bps: float
    residuals: list[FillResidual]
    passes: bool


def _abs_p95(values: Sequence[float]) -> float:
    vals = sorted(abs(v) for v in values if v is not None)
    if not vals:
        return 0.0
    idx = min(len(vals) - 1, int(round(0.95 * (len(vals) - 1))))
    return round(vals[idx], 6)


def fill_residuals(
    paper_fills: Iterable[PaperFill],
    lab_fills: Iterable[LabFill],
    *,
    price_tolerance_bps: float = 5.0,
    qty_tolerance_shares: float = 0.0,
) -> FillResidualSummary:
    """Compute signed bps + qty residuals for every paired fill.

    Pairs paper and lab fills by ``candidate_event_id``. A fill is *flagged*
    when ``abs(price_delta_bps) > price_tolerance_bps`` OR
    ``abs(qty_delta) > qty_tolerance_shares``.
    """
    p_by_cid: dict[str, PaperFill] = {}
    for f in paper_fills:
        cid = f.candidate_event_id or getattr(f, "parent_order_id", None)
        if cid is not None:
            p_by_cid.setdefault(str(cid), f)
    l_by_cid: dict[str, LabFill] = {}
    for f in lab_fills:
        cid = f.candidate_event_id or getattr(f, "parent_order_id", None)
        if cid is not None:
            l_by_cid.setdefault(str(cid), f)

    rows: list[FillResidual] = []
    deltas: list[float] = []
    n_flagged = 0
    for cid in sorted(set(p_by_cid) & set(l_by_cid)):
        p = p_by_cid[cid]
        l = l_by_cid[cid]
        cmp = compare_fill(p, l)
        flagged = False
        if cmp.price_delta_bps is not None:
            deltas.append(cmp.price_delta_bps)
            if abs(cmp.price_delta_bps) > float(price_tolerance_bps):
                flagged = True
        if cmp.qty_delta is not None and abs(cmp.qty_delta) > float(qty_tolerance_shares):
            flagged = True
        if flagged:
            n_flagged += 1
        rows.append(FillResidual(
            candidate_event_id=cid,
            symbol=p.symbol or l.symbol,
            paper_price=p.avg_fill_price,
            lab_price=l.avg_fill_price,
            price_delta_bps=cmp.price_delta_bps,
            paper_qty=p.filled_qty,
            lab_qty=l.filled_qty,
            qty_delta=cmp.qty_delta,
            flagged=flagged,
        ))
    median = round(statistics.median(deltas), 6) if deltas else 0.0
    return FillResidualSummary(
        comparable=len(rows),
        n_flagged=n_flagged,
        price_tolerance_bps=float(price_tolerance_bps),
        qty_tolerance_shares=float(qty_tolerance_shares),
        median_price_delta_bps=median,
        p95_abs_price_delta_bps=_abs_p95(deltas),
        residuals=rows,
        passes=n_flagged == 0,
    )


# --------------------------------------------------------------------------
# 4. fill latency match (median + 95p diff).
# --------------------------------------------------------------------------
@dataclass
class FillLatencyResidual:
    candidate_event_id: str
    paper_latency_ms: Optional[float]
    lab_latency_ms: Optional[float]
    latency_delta_ms: Optional[float]


@dataclass
class FillLatencySummary:
    """Aggregate fill-latency residuals across all matched candidates."""

    comparable: int
    median_paper_ms: float
    median_lab_ms: float
    median_delta_ms: float
    p95_abs_delta_ms: float
    tolerance_p95_ms: float
    rows: list[FillLatencyResidual]
    passes: bool


def _latency_ms(ack_ts: Optional[str], fill_ts: Optional[str]) -> Optional[float]:
    """Milliseconds between two ISO timestamps; ``None`` if either is missing."""
    if not ack_ts or not fill_ts:
        return None
    try:
        a = pd.Timestamp(ack_ts)
        f = pd.Timestamp(fill_ts)
        return float((f - a).total_seconds() * 1000.0)
    except Exception:  # noqa: BLE001
        return None


def fill_latency_residuals(
    paper_acks: Mapping[str, str],
    paper_fills_ts: Mapping[str, str],
    lab_acks: Mapping[str, str],
    lab_fills_ts: Mapping[str, str],
    *,
    tolerance_p95_ms: float = 200.0,
) -> FillLatencySummary:
    """Compare paper vs lab ack→fill latency per matched candidate.

    Each input is a mapping ``candidate_event_id → ISO-timestamp``. The
    residual is ``lab_latency_ms - paper_latency_ms`` per matched id; the
    summary reports the median diff and the 95th-percentile abs diff. The run
    *passes* iff the p95 of the abs residuals is within ``tolerance_p95_ms``.
    """
    cids = sorted(
        set(paper_acks) & set(paper_fills_ts) & set(lab_acks) & set(lab_fills_ts)
    )
    rows: list[FillLatencyResidual] = []
    deltas: list[float] = []
    p_lats: list[float] = []
    l_lats: list[float] = []
    for cid in cids:
        p_lat = _latency_ms(paper_acks.get(cid), paper_fills_ts.get(cid))
        l_lat = _latency_ms(lab_acks.get(cid), lab_fills_ts.get(cid))
        delta = (l_lat - p_lat) if (p_lat is not None and l_lat is not None) else None
        rows.append(FillLatencyResidual(
            candidate_event_id=cid,
            paper_latency_ms=p_lat,
            lab_latency_ms=l_lat,
            latency_delta_ms=delta,
        ))
        if p_lat is not None:
            p_lats.append(p_lat)
        if l_lat is not None:
            l_lats.append(l_lat)
        if delta is not None:
            deltas.append(delta)
    median_p = round(statistics.median(p_lats), 4) if p_lats else 0.0
    median_l = round(statistics.median(l_lats), 4) if l_lats else 0.0
    median_d = round(statistics.median(deltas), 4) if deltas else 0.0
    p95 = _abs_p95(deltas)
    return FillLatencySummary(
        comparable=len(rows),
        median_paper_ms=median_p,
        median_lab_ms=median_l,
        median_delta_ms=median_d,
        p95_abs_delta_ms=p95,
        tolerance_p95_ms=float(tolerance_p95_ms),
        rows=rows,
        passes=p95 <= float(tolerance_p95_ms),
    )


# --------------------------------------------------------------------------
# 5. OCO attempt count match.
# --------------------------------------------------------------------------
@dataclass
class OCOAttemptCountDiff:
    """Per-candidate OCO attempt-count diff (paper vs lab) — aggregated."""

    comparable: int
    matched: int
    mismatched: int
    paper_total_attempts: int
    lab_total_attempts: int
    per_candidate: dict[str, tuple[int, int]]  # cid -> (paper_n, lab_n)
    passes: bool


def oco_attempt_count_diff(
    paper_attempts_by_cid: Mapping[str, int],
    lab_attempts_by_cid: Mapping[str, int],
) -> OCOAttemptCountDiff:
    """Compare OCO attach-attempt counts per candidate.

    Both inputs map ``candidate_event_id`` → integer attempt count. A
    candidate present on one side and missing on the other counts as 0 on the
    missing side (no attempts == "didn't get to OCO"). The run passes iff
    every candidate's attempt count matches exactly.
    """
    cids = sorted(set(paper_attempts_by_cid) | set(lab_attempts_by_cid))
    per_candidate: dict[str, tuple[int, int]] = {}
    matched = 0
    mismatched = 0
    p_total = 0
    l_total = 0
    for cid in cids:
        p_n = int(paper_attempts_by_cid.get(cid, 0))
        l_n = int(lab_attempts_by_cid.get(cid, 0))
        per_candidate[cid] = (p_n, l_n)
        p_total += p_n
        l_total += l_n
        if p_n == l_n:
            matched += 1
        else:
            mismatched += 1
    return OCOAttemptCountDiff(
        comparable=len(cids),
        matched=matched,
        mismatched=mismatched,
        paper_total_attempts=p_total,
        lab_total_attempts=l_total,
        per_candidate=per_candidate,
        passes=mismatched == 0,
    )


# --------------------------------------------------------------------------
# 6. exit reason + timing match.
# --------------------------------------------------------------------------
@dataclass
class ExitReasonTiming:
    """One paired exit — reason + signed timing delta."""

    candidate_event_id: str
    paper_reason: Optional[str]
    lab_reason: Optional[str]
    reason_match: bool
    paper_exit_timestamp: Optional[str]
    lab_exit_timestamp: Optional[str]
    timing_delta_seconds: Optional[float]
    flagged: bool


@dataclass
class ExitReasonTimingSummary:
    comparable: int
    reason_matches: int
    timing_flagged: int
    timing_tolerance_seconds: float
    median_timing_delta_seconds: float
    p95_abs_timing_delta_seconds: float
    rows: list[ExitReasonTiming]
    passes: bool


def exit_reason_timing(
    paper_exits: Iterable[PaperExit],
    lab_exits: Iterable[LabExit],
    *,
    timing_tolerance_seconds: float = 60.0,
) -> ExitReasonTimingSummary:
    """Compare exit reason + exit-timing per closed lot.

    Pairs by ``candidate_event_id`` (each candidate produces at most one lot
    in the synthetic / current_code_parity flow). An exit is *flagged* when
    its reason differs OR its abs timing delta exceeds
    ``timing_tolerance_seconds``.
    """
    p_by_cid = {str(e.candidate_event_id): e for e in paper_exits if e.candidate_event_id}
    l_by_cid = {str(e.candidate_event_id): e for e in lab_exits if e.candidate_event_id}

    rows: list[ExitReasonTiming] = []
    reason_matches = 0
    timing_flagged = 0
    deltas: list[float] = []
    for cid in sorted(set(p_by_cid) & set(l_by_cid)):
        p = p_by_cid[cid]
        l = l_by_cid[cid]
        reason_match = bool(p.exit_reason == l.exit_reason)
        timing_delta: Optional[float] = None
        if p.exit_timestamp and l.exit_timestamp:
            try:
                timing_delta = float(
                    (pd.Timestamp(l.exit_timestamp) - pd.Timestamp(p.exit_timestamp))
                    .total_seconds()
                )
                deltas.append(timing_delta)
            except Exception:  # noqa: BLE001
                timing_delta = None
        flagged = not reason_match
        if (
            timing_delta is not None
            and abs(timing_delta) > float(timing_tolerance_seconds)
        ):
            flagged = True
            timing_flagged += 1
        if reason_match:
            reason_matches += 1
        rows.append(ExitReasonTiming(
            candidate_event_id=cid,
            paper_reason=p.exit_reason,
            lab_reason=l.exit_reason,
            reason_match=reason_match,
            paper_exit_timestamp=p.exit_timestamp,
            lab_exit_timestamp=l.exit_timestamp,
            timing_delta_seconds=timing_delta,
            flagged=flagged,
        ))
    median = round(statistics.median(deltas), 4) if deltas else 0.0
    return ExitReasonTimingSummary(
        comparable=len(rows),
        reason_matches=reason_matches,
        timing_flagged=timing_flagged,
        timing_tolerance_seconds=float(timing_tolerance_seconds),
        median_timing_delta_seconds=median,
        p95_abs_timing_delta_seconds=_abs_p95(deltas),
        rows=rows,
        passes=(reason_matches == len(rows)) and timing_flagged == 0,
    )


# --------------------------------------------------------------------------
# 7. PnL match (closed-trade PnL within tolerance).
# --------------------------------------------------------------------------
@dataclass
class PnLResidual:
    candidate_event_id: str
    paper_pnl: Optional[float]
    lab_pnl: Optional[float]
    pnl_delta: Optional[float]
    flagged: bool


@dataclass
class PnLResidualSummary:
    comparable: int
    n_flagged: int
    pnl_tolerance_dollars: float
    median_delta_dollars: float
    p95_abs_delta_dollars: float
    rows: list[PnLResidual]
    passes: bool


def pnl_residuals(
    paper_exits: Iterable[PaperExit],
    lab_exits: Iterable[LabExit],
    *,
    pnl_tolerance_dollars: float = 1.0,
) -> PnLResidualSummary:
    """Compare closed-trade realized PnL per matched candidate.

    Pairs by ``candidate_event_id``. A row is *flagged* when
    ``abs(pnl_delta) > pnl_tolerance_dollars``.
    """
    p_by_cid = {str(e.candidate_event_id): e for e in paper_exits if e.candidate_event_id}
    l_by_cid = {str(e.candidate_event_id): e for e in lab_exits if e.candidate_event_id}
    rows: list[PnLResidual] = []
    deltas: list[float] = []
    n_flagged = 0
    for cid in sorted(set(p_by_cid) & set(l_by_cid)):
        p = p_by_cid[cid]
        l = l_by_cid[cid]
        delta = compare_pnl(p, l)
        flagged = (
            delta is not None and abs(delta) > float(pnl_tolerance_dollars)
        )
        if delta is not None:
            deltas.append(delta)
        if flagged:
            n_flagged += 1
        rows.append(PnLResidual(
            candidate_event_id=cid,
            paper_pnl=p.realized_pnl,
            lab_pnl=l.realized_pnl,
            pnl_delta=delta,
            flagged=flagged,
        ))
    median = round(statistics.median(deltas), 4) if deltas else 0.0
    return PnLResidualSummary(
        comparable=len(rows),
        n_flagged=n_flagged,
        pnl_tolerance_dollars=float(pnl_tolerance_dollars),
        median_delta_dollars=median,
        p95_abs_delta_dollars=_abs_p95(deltas),
        rows=rows,
        passes=n_flagged == 0,
    )


__all__ = [
    # Phase-10 per-stage comparators.
    "CandidateSetDiff",
    "diff_candidate_sets",
    "DecisionReasonComparison",
    "compare_decision_reason",
    "compare_order_size",
    "FillComparison",
    "compare_fill",
    "compare_exit_reason",
    "compare_pnl",
    # Realism remediation 2 Phase 9 aggregate comparators.
    "EmissionJaccard", "emission_jaccard",
    "DecisionReasonConfusion", "decision_reason_confusion",
    "FillResidual", "FillResidualSummary", "fill_residuals",
    "FillLatencyResidual", "FillLatencySummary", "fill_latency_residuals",
    "OCOAttemptCountDiff", "oco_attempt_count_diff",
    "ExitReasonTiming", "ExitReasonTimingSummary", "exit_reason_timing",
    "PnLResidual", "PnLResidualSummary", "pnl_residuals",
]
