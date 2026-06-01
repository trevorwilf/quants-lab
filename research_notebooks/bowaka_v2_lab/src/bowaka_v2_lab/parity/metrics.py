"""Production-vs-lab parity metrics — audit 2026-05-29 §14.5 adapted.

The audit's Phase 6 paper-vs-sim thresholds apply almost verbatim to sim-vs-sim;
the difference is that both sides are deterministic so a divergence is provably
code-level drift (not a market-realism effect), so ``trade_intersection_rate``
gets a stricter floor (90% vs the paper-recon 85%).
"""
from __future__ import annotations

import statistics
from datetime import date
from typing import Iterable, Mapping, Optional, Sequence

from .schemas import NormalizedCandidate, NormalizedTrade, ParityReport

#: Audit 2026-05-29 §14.5 — sim-vs-sim adaptation. Set per-metric so the report
#: renderer can show "actual vs threshold" alongside each row.
DEFAULT_THRESHOLDS: dict[str, float] = {
    "candidate_recall":          0.99,
    "gate_match_rate":           0.95,
    "trade_intersection_rate":   0.90,   # stricter than paper-recon (0.85)
    "fill_price_mae_bps":        5.0,    # LOWER is better — see _LOWER_IS_BETTER
    "exit_reason_match_rate":    0.90,
    "daily_pnl_sign_match_rate": 0.95,
}

#: Metrics where a lower value is better; thresholds are upper bounds for these.
_LOWER_IS_BETTER: frozenset[str] = frozenset({"fill_price_mae_bps"})


def _by_key(trades: Iterable[NormalizedTrade]) -> dict[tuple[date, str, "object"], NormalizedTrade]:
    return {t.join_key: t for t in trades}


def _cand_by_key(
    cands: Iterable[NormalizedCandidate],
) -> dict[tuple[date, str, "object"], NormalizedCandidate]:
    return {c.join_key: c for c in cands}


def _fill_diff_bps(prod: NormalizedTrade, lab: NormalizedTrade) -> float:
    """Signed entry-price diff (lab vs prod) in bps. ``0.0`` if prod fill is 0."""
    if prod.entry_price <= 0:
        return 0.0
    return (lab.entry_price - prod.entry_price) / prod.entry_price * 10_000.0


def evaluate_thresholds(
    report: ParityReport,
    *,
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
) -> tuple[bool, list[str]]:
    """Return ``(passes, failing_metrics)`` for ``report`` against ``thresholds``.

    A metric in :data:`_LOWER_IS_BETTER` (``fill_price_mae_bps``) is failed when
    its value EXCEEDS the threshold; every other metric is failed when its
    value FALLS SHORT of the threshold.
    """
    failing: list[str] = []
    for name, threshold in thresholds.items():
        raw = getattr(report, name)
        if raw is None:
            # Phase 0 (parity oracle): "not measured" — excluded from the
            # verdict. A missing data source must never count as PASS or FAIL.
            continue
        value = float(raw)
        if name in _LOWER_IS_BETTER:
            if value > threshold:
                failing.append(name)
        else:
            if value < threshold:
                failing.append(name)
    return (not failing, failing)


def _candidate_metrics(
    prod_cands: Sequence[NormalizedCandidate],
    lab_cands: Sequence[NormalizedCandidate],
) -> tuple[Optional[float], Optional[float]]:
    """(candidate_recall, gate_match_rate), or ``(None, None)`` when NOT MEASURED.

    Phase 0 (parity oracle): production emits no candidate telemetry by default
    and the lab emits it only under ``debug_first_n_trials``. When EITHER side
    lacks candidates the metric is meaningless, so return ``(None, None)``
    instead of the old degenerate ``1.0`` — a missing data source must never
    report a candidate/gate PASS.
    """
    if not prod_cands or not lab_cands:
        return None, None
    prod_by_key = _cand_by_key(prod_cands)
    lab_by_key = _cand_by_key(lab_cands)
    matched_keys = prod_by_key.keys() & lab_by_key.keys()
    recall = (len(matched_keys) / len(prod_by_key)) if prod_by_key else 1.0
    if not matched_keys:
        return float(recall), 1.0
    gate_agree = sum(
        1 for k in matched_keys
        if prod_by_key[k].gate_passed == lab_by_key[k].gate_passed
    )
    return float(recall), float(gate_agree / len(matched_keys))


def _trade_intersection_rate(
    prod_trades: Sequence[NormalizedTrade],
    lab_trades: Sequence[NormalizedTrade],
) -> tuple[float, set, set, set]:
    """(jaccard, matched_keys, prod_only_keys, lab_only_keys)."""
    prod_keys = {t.join_key for t in prod_trades}
    lab_keys = {t.join_key for t in lab_trades}
    union = prod_keys | lab_keys
    if not union:
        return 1.0, set(), set(), set()
    matched = prod_keys & lab_keys
    return (
        float(len(matched) / len(union)),
        matched,
        prod_keys - matched,
        lab_keys - matched,
    )


def _per_session_pnl_signs(
    prod_trades: Sequence[NormalizedTrade], lab_trades: Sequence[NormalizedTrade],
) -> tuple[float, list[Mapping[str, object]]]:
    """Per-session daily-PnL sign match.

    For each session present on EITHER side, sum the side's PnL and compare
    sign (``sign(0) = 0`` matches ``sign(0)``).
    """
    sessions = sorted({t.session_date for t in prod_trades} | {t.session_date for t in lab_trades})
    if not sessions:
        return 1.0, []
    rows: list[Mapping[str, object]] = []
    agree = 0
    for s in sessions:
        prod_sum = sum(t.pnl_dollars for t in prod_trades if t.session_date == s)
        lab_sum = sum(t.pnl_dollars for t in lab_trades if t.session_date == s)
        prod_sign = 0 if prod_sum == 0 else (1 if prod_sum > 0 else -1)
        lab_sign = 0 if lab_sum == 0 else (1 if lab_sum > 0 else -1)
        signs_agree = prod_sign == lab_sign
        if signs_agree:
            agree += 1
        rows.append({
            "session_date": s.isoformat(),
            "prod_pnl_dollars": float(prod_sum),
            "lab_pnl_dollars": float(lab_sum),
            "signs_agree": bool(signs_agree),
        })
    return float(agree / len(sessions)), rows


def compute_parity_metrics(
    *,
    window_start: date,
    window_end: date,
    universe_size: int,
    prod_trades: Sequence[NormalizedTrade],
    prod_candidates: Sequence[NormalizedCandidate],
    lab_trades: Sequence[NormalizedTrade],
    lab_candidates: Sequence[NormalizedCandidate],
    requested_sessions: Sequence[date] | None = None,
    prod_summary: Mapping[str, object] | None = None,
    lab_result: object | None = None,  # noqa: ARG001 — accepted for symmetry
    thresholds: Mapping[str, float] = DEFAULT_THRESHOLDS,
    worst_n: int = 10,
) -> ParityReport:
    """Fold both sides' normalized streams into a :class:`ParityReport`."""
    prod_by_key = _by_key(prod_trades)
    lab_by_key = _by_key(lab_trades)
    jaccard, matched_keys, prod_only_keys, lab_only_keys = _trade_intersection_rate(
        prod_trades, lab_trades,
    )

    # Matched-trade diffs.
    matched_diffs: list[tuple[NormalizedTrade, NormalizedTrade, float]] = []
    exit_mismatch_pairs: list[tuple[NormalizedTrade, NormalizedTrade]] = []
    for k in matched_keys:
        p, l = prod_by_key[k], lab_by_key[k]
        matched_diffs.append((p, l, _fill_diff_bps(p, l)))
        if p.exit_reason != l.exit_reason:
            exit_mismatch_pairs.append((p, l))

    abs_diffs = [abs(d) for *_, d in matched_diffs]
    fill_price_mae_bps = float(statistics.mean(abs_diffs)) if abs_diffs else 0.0

    exit_reason_match_rate = (
        float(1.0 - len(exit_mismatch_pairs) / len(matched_diffs))
        if matched_diffs else 1.0
    )

    candidate_recall, gate_match_rate = _candidate_metrics(
        prod_candidates, lab_candidates,
    )
    daily_pnl_sign_match_rate, daily_pnl_rows = _per_session_pnl_signs(
        prod_trades, lab_trades,
    )

    prod_gross_pnl = float(sum(t.pnl_dollars for t in prod_trades))
    lab_gross_pnl = float(sum(t.pnl_dollars for t in lab_trades))
    # Phase 0 (parity oracle): report the REQUESTED XNYS session count (threaded
    # in by the runner) so coverage isn't understated by counting only
    # trade-bearing sessions. ``n_trade_sessions`` keeps the old count.
    n_trade_sessions = len({t.session_date for t in prod_trades}
                           | {t.session_date for t in lab_trades})
    n_sessions = (
        len(requested_sessions) if requested_sessions is not None
        else n_trade_sessions
    )

    # Drill-down: worst N.
    prod_only_sorted = sorted(
        [prod_by_key[k] for k in prod_only_keys],
        key=lambda t: -abs(t.pnl_dollars),
    )[:worst_n]
    lab_only_sorted = sorted(
        [lab_by_key[k] for k in lab_only_keys],
        key=lambda t: -abs(t.pnl_dollars),
    )[:worst_n]
    largest_fill_diffs = [
        {
            "session_date": p.session_date.isoformat(),
            "symbol": p.symbol,
            "entry_ts_minute": p.entry_ts_minute.isoformat(),
            "prod_entry_price": p.entry_price,
            "lab_entry_price": l.entry_price,
            "fill_diff_bps": float(d),
        }
        for (p, l, d) in sorted(matched_diffs, key=lambda x: -abs(x[2]))[:worst_n]
    ]
    exit_mismatches = [
        {
            "session_date": p.session_date.isoformat(),
            "symbol": p.symbol,
            "entry_ts_minute": p.entry_ts_minute.isoformat(),
            "prod_exit_reason": p.exit_reason,
            "lab_exit_reason": l.exit_reason,
        }
        for (p, l) in exit_mismatch_pairs[:worst_n]
    ]

    report = ParityReport(
        window_start=window_start, window_end=window_end,
        universe_size=int(universe_size), n_sessions=int(n_sessions),
        n_trade_sessions=int(n_trade_sessions),
        prod_n_candidates=len(prod_candidates),
        prod_n_trades=len(prod_trades),
        prod_gross_pnl=prod_gross_pnl,
        lab_n_candidates=len(lab_candidates),
        lab_n_trades=len(lab_trades),
        lab_gross_pnl=lab_gross_pnl,
        candidate_recall=candidate_recall,
        gate_match_rate=gate_match_rate,
        trade_intersection_rate=jaccard,
        fill_price_mae_bps=fill_price_mae_bps,
        exit_reason_match_rate=exit_reason_match_rate,
        daily_pnl_sign_match_rate=daily_pnl_sign_match_rate,
        prod_only_trades=prod_only_sorted,
        lab_only_trades=lab_only_sorted,
        largest_fill_diffs=largest_fill_diffs,
        exit_reason_mismatches=exit_mismatches,
        daily_pnl_per_session=daily_pnl_rows,
    )
    passes, failing = evaluate_thresholds(report, thresholds=thresholds)
    # ParityReport is frozen; build a fresh one with the threshold-pass fields.
    from dataclasses import replace
    return replace(report, passes_audit_thresholds=passes, failing_metrics=failing)


__all__ = [
    "DEFAULT_THRESHOLDS",
    "compute_parity_metrics",
    "evaluate_thresholds",
]
