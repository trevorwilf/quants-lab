"""Stop-ship checklist for finalist promotion (speedup report v2 §11 / Phase 5).

After the Stage-B finalist evaluation assembles its report, this module
applies a hand-reviewable promotion gate. Any single failure blocks
promotion; warnings are advisory.

The decision is computed from the assembled finalist report's
``finalist_evaluation`` block (plus the top-level ``finalists`` /
``incumbent`` rows) — it does NOT re-run any backtest, so it is cheap and
deterministic. ``evaluate_stop_ship`` is pure: same report in -> same
decision out.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


#: Promotion thresholds (operator-tunable via the finalist_evaluation config).
HOLDOUT_REGRESSION_LIMIT = 0.10          # holdout worse than incumbent by > 10%
CLUSTER_CV_THRESHOLD = 0.15              # per-param CV above this is "unstable"
CLUSTER_UNSTABLE_FRACTION_LIMIT = 0.50  # > 50% unstable params blocks
MIN_TOTAL_TRADES = 30                    # too few trades to trust
MAX_SINGLE_SYMBOL_TRADE_SHARE = 0.25     # one symbol > 25% of trades blocks


@dataclass
class StopShipDecision:
    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": bool(self.passed),
            "failures": list(self.failures),
            "warnings": list(self.warnings),
        }


def _exported_finalist(report: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    """The exported candidate = index 0 of the finalists list (the best)."""
    finalists = report.get("finalists") or []
    return finalists[0] if finalists else None


def _incumbent(report: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    return report.get("incumbent")


def _objective(row: Optional[Mapping[str, Any]], section: str) -> Optional[float]:
    if not row:
        return None
    sub = row.get(section)
    if isinstance(sub, Mapping) and "objective" in sub:
        try:
            return float(sub["objective"])
        except (TypeError, ValueError):
            return None
    return None


def evaluate_stop_ship(
    finalist_report: Mapping[str, Any],
    *,
    cluster_cv_threshold: float = CLUSTER_CV_THRESHOLD,
    min_total_trades: int = MIN_TOTAL_TRADES,
    max_single_symbol_share: float = MAX_SINGLE_SYMBOL_TRADE_SHARE,
    holdout_regression_limit: float = HOLDOUT_REGRESSION_LIMIT,
) -> StopShipDecision:
    """Apply the promotion gate to an assembled finalist report.

    Failures (any one blocks promotion):
      1. exported finalist's final-holdout objective is worse than the
         incumbent's by more than ``holdout_regression_limit``.
      2. worst-case stress objective < 0 on any axis (fold-local matrix).
      3. top-K cluster is non-clustered (> 50% of tuned params CV >
         ``cluster_cv_threshold``).
      4. total trade count across folds < ``min_total_trades``.
      5. one symbol owns > ``max_single_symbol_share`` of trades.
      6. any data-quality gate failed.
      7. feed is iex AND partial_tape_caveat is true (research-only tier).
    """
    failures: list[str] = []
    warnings: list[str] = []
    fe = finalist_report.get("finalist_evaluation") or {}
    exported = _exported_finalist(finalist_report)
    incumbent = _incumbent(finalist_report)

    # (1) Holdout regression vs incumbent.
    exp_holdout = _objective(exported, "holdout")
    inc_holdout = _objective(incumbent, "holdout")
    if exp_holdout is not None and inc_holdout is not None:
        # "worse by > 10%": for a higher-is-better objective, exported below
        # incumbent * (1 - limit). Guard the sign of the incumbent value.
        if inc_holdout > 0:
            floor = inc_holdout * (1.0 - holdout_regression_limit)
            if exp_holdout < floor:
                failures.append(
                    f"holdout regression: exported holdout objective "
                    f"{exp_holdout:.6g} < incumbent {inc_holdout:.6g} "
                    f"by more than {holdout_regression_limit:.0%}"
                )
        elif exp_holdout < inc_holdout - abs(inc_holdout) * holdout_regression_limit:
            failures.append(
                f"holdout regression: exported holdout objective "
                f"{exp_holdout:.6g} below incumbent {inc_holdout:.6g}"
            )
    else:
        warnings.append("holdout objective missing for exported finalist or incumbent")

    # (2) Worst-case stress objective < 0 (any axis).
    matrix = fe.get("fold_local_stress_matrix") or {}
    worst = matrix.get("worst_case_objective")
    if worst is not None:
        try:
            if float(worst) < 0.0:
                failures.append(
                    f"stress collapse: worst-case stress objective {float(worst):.6g} < 0"
                )
        except (TypeError, ValueError):
            pass
    else:
        warnings.append("fold-local stress matrix absent (worst-case not checked)")

    # (3) Top-K cluster stability.
    clustering = fe.get("top_k_clustering") or {}
    unstable_fraction = clustering.get("unstable_fraction")
    if unstable_fraction is not None:
        try:
            if float(unstable_fraction) > CLUSTER_UNSTABLE_FRACTION_LIMIT:
                failures.append(
                    f"top-K not clustered: {float(unstable_fraction):.0%} of tuned "
                    f"params have CV > {cluster_cv_threshold}"
                )
        except (TypeError, ValueError):
            pass

    # (4) + (5) Trade diagnostics.
    diags = fe.get("trade_diagnostics") or {}
    exported_diag = diags.get("exported") or diags.get("best") or {}
    total_trades = exported_diag.get("total_trades")
    if total_trades is not None:
        if int(total_trades) < min_total_trades:
            failures.append(
                f"too few trades: {int(total_trades)} < {min_total_trades} across folds"
            )
    else:
        warnings.append("trade count missing (min-trades gate not checked)")
    top_share = exported_diag.get("max_symbol_share")
    if top_share is not None:
        try:
            if float(top_share) > max_single_symbol_share:
                failures.append(
                    f"symbol concentration: one symbol owns "
                    f"{float(top_share):.0%} of trades (> {max_single_symbol_share:.0%})"
                )
        except (TypeError, ValueError):
            pass

    # (6) Data-quality gates.
    dq = fe.get("data_quality") or {}
    if dq.get("any_gate_failed") is True:
        failures.append("data-quality gate failed on at least one fold")

    # (7) IEX partial-tape caveat caps the tier at research-only.
    feed = str((finalist_report.get("feed") or dq.get("feed") or "")).lower()
    partial_tape = bool(dq.get("partial_tape_caveat", False))
    if feed == "iex" and partial_tape:
        failures.append(
            "partial-tape caveat on an IEX feed caps the tier at research-only; "
            "promotion past research-only is blocked"
        )

    return StopShipDecision(
        passed=(len(failures) == 0),
        failures=failures,
        warnings=warnings,
    )


__all__ = [
    "StopShipDecision",
    "evaluate_stop_ship",
    "CLUSTER_CV_THRESHOLD",
    "MIN_TOTAL_TRADES",
    "MAX_SINGLE_SYMBOL_TRADE_SHARE",
    "HOLDOUT_REGRESSION_LIMIT",
]
