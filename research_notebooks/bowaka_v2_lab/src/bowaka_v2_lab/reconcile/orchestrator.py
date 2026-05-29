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


def _default_reconcile_one(
    session_dir: Path, cfg: Mapping[str, Any], lake_root: Optional[Path],
) -> SessionReconcileResult:
    raise NotImplementedError(
        "production per-session reconciliation requires the lab-replay comparison "
        "wired for your environment (lake + config); pass reconcile_one=... to "
        "run_reconciliation. The orchestrator's aggregation / status / gate logic "
        "is exercised with injected reconcilers in the test suite."
    )


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


__all__ = [
    "DEFAULT_THRESHOLDS",
    "DEFAULT_MIN_SESSIONS",
    "SessionReconcileResult",
    "ReconcileReport",
    "aggregate_metrics",
    "run_reconciliation",
]
