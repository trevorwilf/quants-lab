"""Multi-session paper-vs-sim reconciliation orchestrator (audit 2026-05-29 §8.7
/ §9 Phase 6 / §14).

For each session under ``reconcile.paper_logs_root`` the per-session reconcile
(``reconcile_one``) imports the paper event logs, replays the simulator at the
same parameters, compares event-by-event, and computes the audit's acceptance
metrics. Results are aggregated (session-weighted) into a :class:`ReconcileReport`.

Status semantics (operator context: no real paper logs yet):

- ``REAL_LOGS_DEFERRED`` — the paper-logs root is empty / absent (0 sessions).
- ``BELOW_MIN_SESSIONS`` — fewer than ``min_sessions_for_promotion`` sessions.
- ``ok`` — enough sessions; ``passes_all_thresholds`` is then meaningful.

``reconcile_one`` is injectable so tests use cheap stubs; the default raises a
clear error directing the operator to wire the lab-replay comparison (the
production path is environment-specific and is only reached once real sessions
exist on disk).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from .importer import discover_sessions

#: Audit 2026-05-29 §8.7 acceptance thresholds (IEX current-code-parity).
DEFAULT_THRESHOLDS: dict[str, float] = {
    "candidate_recall": 0.99,
    "gate_match": 0.95,
    "entry_decision_match": 0.95,
    "fill_match": 0.85,
    "exit_reason_match": 0.90,
    "bracket_attach_match": 1.00,
    "daily_pnl_sign_match": 0.90,
}
DEFAULT_MIN_SESSIONS = 10

#: Metric fields gated against the thresholds (in aggregate).
_GATED_METRICS = tuple(DEFAULT_THRESHOLDS.keys())


@dataclass(frozen=True)
class SessionReconcileResult:
    session_date: str
    n_paper_candidates: int
    n_sim_candidates: int
    candidate_recall: float
    gate_match: float
    entry_decision_match: float
    fill_match: float
    fill_price_mae_bps: float
    exit_reason_match: float
    bracket_attach_match: float
    daily_pnl_sign_match: float
    per_symbol_fill_error_bps: dict[str, float] = field(default_factory=dict)
    per_adv_bucket_fill_error_bps: dict[str, float] = field(default_factory=dict)
    per_tod_bucket_fill_error_bps: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ReconcileReport:
    n_sessions: int
    aggregate: Mapping[str, float]
    per_session: list[SessionReconcileResult]
    thresholds: Mapping[str, float]
    passes_all_thresholds: bool
    failing_metrics: list[str]
    status: str    # "ok" | "REAL_LOGS_DEFERRED" | "BELOW_MIN_SESSIONS"


def _reconcile_cfg(cfg: Mapping[str, Any]) -> dict[str, Any]:
    rec = dict((cfg or {}).get("reconcile") or {})
    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds.update(rec.get("thresholds") or {})
    return {
        "paper_logs_root": rec.get("paper_logs_root", "data/paper_logs"),
        "min_sessions_for_promotion": int(
            rec.get("min_sessions_for_promotion", DEFAULT_MIN_SESSIONS)
        ),
        "thresholds": {k: float(v) for k, v in thresholds.items()},
    }


def aggregate_metrics(results: Sequence[SessionReconcileResult]) -> dict[str, float]:
    """Session-weighted mean of each gated metric + the fill-price MAE."""
    if not results:
        return {}
    weights = [max(1, r.n_paper_candidates) for r in results]
    total_w = float(sum(weights))
    agg: dict[str, float] = {}
    for metric in _GATED_METRICS:
        agg[metric] = sum(
            getattr(r, metric) * w for r, w in zip(results, weights)
        ) / total_w
    agg["fill_price_mae_bps"] = sum(
        r.fill_price_mae_bps * w for r, w in zip(results, weights)
    ) / total_w
    return agg


def _sign(x: float) -> int:
    return 1 if x > 1e-9 else (-1 if x < -1e-9 else 0)


def _decision(rec: Any) -> Optional[str]:
    d = getattr(rec, "decision", None)
    return str(d).strip().lower() if d else None


def _session_result_from_rows(
    session_date: str, rows: Sequence[Any], tol: Mapping[str, float],
) -> SessionReconcileResult:
    """Compute the §8.7 acceptance metrics for one session from its reconcile rows.

    Match-rate metrics are the fraction of COMPARABLE rows (a record present on
    both sides) that agree; a metric with no comparable rows is 1.0 (no observed
    disagreement). Fill match uses the single P9 tolerances (fill_price_tolerance_bps
    / fill_qty_tolerance_shares); daily_pnl_sign_match compares the SESSION's summed
    realized-PnL sign across paper vs lab.
    """
    price_tol = float(tol.get("fill_price_tolerance_bps", 5.0))
    qty_tol = float(tol.get("fill_qty_tolerance_shares", 0.0))

    n_paper = sum(1 for r in rows if r.presence in ("both", "paper_only"))
    n_sim = sum(1 for r in rows if r.presence in ("both", "lab_only"))
    n_both = sum(1 for r in rows if r.presence == "both")

    def _rate(items: list, pred) -> float:
        return (sum(1 for x in items if pred(x)) / len(items)) if items else 1.0

    candidate_recall = (n_both / n_paper) if n_paper else 1.0

    dec_rows = [r for r in rows if r.paper_decision is not None and r.lab_decision is not None]
    gate_match = _rate(dec_rows, lambda r: _decision(r.paper_decision) == _decision(r.lab_decision))
    entry_decision_match = _rate(dec_rows, lambda r: bool(r.decision_reason_match))

    fill_rows = [r for r in rows if r.paper_fill is not None and r.lab_fill is not None]
    fill_match = _rate(
        fill_rows,
        lambda r: (r.fill_price_delta_bps is not None and abs(r.fill_price_delta_bps) <= price_tol)
        and (r.fill_qty_delta is None or abs(r.fill_qty_delta) <= qty_tol),
    )
    deltas = [abs(r.fill_price_delta_bps) for r in fill_rows if r.fill_price_delta_bps is not None]
    fill_price_mae_bps = (sum(deltas) / len(deltas)) if deltas else 0.0

    exit_rows = [r for r in rows if r.paper_exit is not None and r.lab_exit is not None]
    exit_reason_match = _rate(exit_rows, lambda r: bool(r.exit_reason_match))

    # Bracket attach: among rows filled on BOTH sides, both must carry a parent
    # (bracket) order — a fill without its protective bracket is a hard divergence
    # (threshold 1.00).
    bracket_attach_match = _rate(
        fill_rows, lambda r: r.paper_order is not None and r.lab_order is not None
    )

    paper_pnl = sum((r.paper_exit.realized_pnl or 0.0) for r in rows if r.paper_exit is not None)
    lab_pnl = sum((r.lab_exit.realized_pnl or 0.0) for r in rows if r.lab_exit is not None)
    daily_pnl_sign_match = 1.0 if _sign(paper_pnl) == _sign(lab_pnl) else 0.0

    by_sym: dict[str, list[float]] = {}
    for r in fill_rows:
        if r.fill_price_delta_bps is not None:
            by_sym.setdefault(str(r.symbol or "?"), []).append(abs(r.fill_price_delta_bps))
    per_symbol = {s: sum(v) / len(v) for s, v in by_sym.items() if v}

    return SessionReconcileResult(
        session_date=session_date,
        n_paper_candidates=n_paper,
        n_sim_candidates=n_sim,
        candidate_recall=candidate_recall,
        gate_match=gate_match,
        entry_decision_match=entry_decision_match,
        fill_match=fill_match,
        fill_price_mae_bps=fill_price_mae_bps,
        exit_reason_match=exit_reason_match,
        bracket_attach_match=bracket_attach_match,
        daily_pnl_sign_match=daily_pnl_sign_match,
        per_symbol_fill_error_bps=per_symbol,
    )


def _default_reconcile_one(
    session_dir: Path, cfg: Mapping[str, Any], lake_root: Optional[Path],
) -> SessionReconcileResult:
    """Reconcile ONE real paper session against a current_code_parity lab replay.

    ``session_dir`` is a ``YYYY-MM-DD`` directory (from :func:`discover_sessions`)
    holding that session's paper-log JSONLs. Replays the lab over the same date /
    lake / config, joins paper vs lab event-by-event (``replay_paper_session``), and
    computes the §8.7 acceptance metrics with the single P9 tolerance set.
    """
    from .comparator import load_reconcile_tolerances
    from .replay import replay_paper_session

    session_date = Path(session_dir).name
    lab_cfg: dict[str, Any] = dict(cfg or {})
    if lake_root is not None:
        md = dict(lab_cfg.get("market_data") or {})
        md["shared_root"] = str(lake_root)
        lab_cfg["market_data"] = md
    replay = replay_paper_session(session_date, session_dir, lab_cfg)
    tol = load_reconcile_tolerances((cfg or {}).get("reconcile", {}).get("tolerances"))
    return _session_result_from_rows(session_date, replay.rows, tol)


def run_reconciliation(
    *,
    paper_logs_root: Path | str,
    cfg: Mapping[str, Any],
    lake_root: Optional[Path] = None,
    reconcile_one: Optional[
        Callable[[Path, Mapping[str, Any], Optional[Path]], SessionReconcileResult]
    ] = None,
) -> ReconcileReport:
    """Reconcile every session under ``paper_logs_root`` and aggregate."""
    rcfg = _reconcile_cfg(cfg)
    thresholds = rcfg["thresholds"]
    min_sessions = rcfg["min_sessions_for_promotion"]

    sessions = discover_sessions(paper_logs_root)
    if not sessions:
        return ReconcileReport(
            n_sessions=0, aggregate={}, per_session=[], thresholds=thresholds,
            passes_all_thresholds=False, failing_metrics=["REAL_LOGS_DEFERRED"],
            status="REAL_LOGS_DEFERRED",
        )

    runner = reconcile_one or _default_reconcile_one
    results = [runner(s, cfg, lake_root) for s in sessions]
    agg = aggregate_metrics(results)
    failing = [m for m, thr in thresholds.items() if agg.get(m, 0.0) < thr]
    status = "BELOW_MIN_SESSIONS" if len(sessions) < min_sessions else "ok"
    return ReconcileReport(
        n_sessions=len(sessions),
        aggregate=agg,
        per_session=results,
        thresholds=thresholds,
        passes_all_thresholds=(not failing and status == "ok"),
        failing_metrics=failing,
        status=status,
    )


def render_reconcile_report_md(report: ReconcileReport) -> str:
    """Render a multi-session :class:`ReconcileReport` as markdown.

    This is the human-readable + promotion-gate artifact for the multi-session
    path (``promotion.suitability._has_paper_recon_artifact`` detects
    ``reconciliation_report.md``). The single-session path has its own renderer;
    this one summarises the session-weighted aggregate + a per-session table.
    """
    lines: list[str] = ["# Bowaka v2 — Paper-vs-Lab Reconciliation", ""]
    verdict = "PASS" if report.passes_all_thresholds else "FAIL"
    lines.append(f"- **Status:** {report.status}")
    lines.append(f"- **Sessions reconciled:** {report.n_sessions}")
    lines.append(f"- **Verdict:** {verdict}")
    failing = ", ".join(report.failing_metrics) if report.failing_metrics else "none"
    lines.append(f"- **Failing metrics:** {failing}")
    lines += ["", "## Aggregate metrics (session-weighted)", ""]
    lines.append("| Metric | Value | Threshold | Pass |")
    lines.append("|--------|-------|-----------|------|")
    agg = dict(report.aggregate or {})
    for metric, thr in report.thresholds.items():
        val = agg.get(metric)
        val_s = f"{val:.4f}" if isinstance(val, (int, float)) else "—"
        ok = "PASS" if (isinstance(val, (int, float)) and val >= thr) else "FAIL"
        lines.append(f"| {metric} | {val_s} | {thr:.2f} | {ok} |")
    mae = agg.get("fill_price_mae_bps")
    if isinstance(mae, (int, float)):
        lines.append(f"| fill_price_mae_bps | {mae:.3f} | — | — |")
    if report.per_session:
        lines += ["", "## Per-session", ""]
        lines.append(
            "| Session | n_paper | n_sim | cand_recall | gate | entry_dec | "
            "fill | fill_mae_bps | exit_reason | pnl_sign |"
        )
        lines.append(
            "|---------|---------|-------|-------------|------|-----------|"
            "------|--------------|-------------|----------|"
        )
        for r in report.per_session:
            lines.append(
                f"| {r.session_date} | {r.n_paper_candidates} | {r.n_sim_candidates} | "
                f"{r.candidate_recall:.3f} | {r.gate_match:.3f} | {r.entry_decision_match:.3f} | "
                f"{r.fill_match:.3f} | {r.fill_price_mae_bps:.2f} | {r.exit_reason_match:.3f} | "
                f"{r.daily_pnl_sign_match:.3f} |"
            )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_THRESHOLDS",
    "DEFAULT_MIN_SESSIONS",
    "SessionReconcileResult",
    "ReconcileReport",
    "aggregate_metrics",
    "run_reconciliation",
    "render_reconcile_report_md",
]
