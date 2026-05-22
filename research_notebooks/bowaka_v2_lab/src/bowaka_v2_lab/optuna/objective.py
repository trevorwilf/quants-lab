"""Realistic walk-forward Optuna objective (realism remediation Phase 9).

Rebuilt around the substantive metrics Phase 8's ``report.json`` / ``summary.json``
already produce. The objective is intentionally conservative: it rewards real
net return after realistic costs and penalizes every way a backtest can look
good while being un-tradeable.

    objective   = median_fold_score - cross_fold_variance_penalty
    fold_score  = net_return
                   - drawdown_penalty           (DAILY mark-to-market max DD)
                   - cvar_penalty               (worst-day / tail loss)
                   - low_trade_count_penalty
                   - missing_quote_penalty
                   - missing_coverage_penalty
                   - turnover_penalty
                   - concentration_penalty
                   - fill_rate_penalty

Mark-to-market drawdown
-----------------------
The drawdown penalty uses the **daily equity curve** (``report.json`` →
``portfolio_and_risk.daily_equity`` → ``bankroll`` per session), NOT the
closed-trade equity curve that ``summary.max_drawdown_pct`` is built from. A
strategy can have a shallow closed-trade drawdown while sitting through a deep
unrealized mark-to-market hole; the audit (§14.3) requires the *daily* curve.
:func:`mark_to_market_drawdown` computes it and :func:`fold_result_from_report`
threads it onto :class:`FoldResult.max_drawdown`.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


# --------------------------------------------------------------------------
# Penalty weights. Tunable research priors — bumping them is a methodology
# decision, not a bug, but they are kept here so a study can introspect them.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PenaltyWeights:
    drawdown: float = 0.5           # x daily mark-to-market max drawdown
    cvar: float = 0.5              # x worst-day fractional loss
    turnover: float = 1.0          # x turnover
    concentration: float = 1.0     # x concentration
    low_trade_count: float = 1.0   # max magnitude of the sparse-trade penalty
    missing_quote: float = 0.02    # x missing-quote count
    missing_coverage: float = 1.0  # x coverage shortfall fraction
    fill_rate: float = 0.5         # x (1 - fill_rate) shortfall
    fold_variance: float = 0.5     # x stdev of fold scores

    #: A fold with fewer than this many trades is statistically uninformative;
    #: the low-trade-count penalty ramps to its max as n_trades -> 0.
    min_trade_count: int = 30


DEFAULT_PENALTY_WEIGHTS = PenaltyWeights()


@dataclass
class FoldResult:
    """Per-fold realistic metrics consumed by the objective.

    ``max_drawdown`` MUST be the daily mark-to-market drawdown (a fraction in
    ``[0, 1]``), not the closed-trade-curve drawdown.
    """

    fold_id: str
    net_return: float
    max_drawdown: float
    turnover: float
    concentration: float
    n_trades: int
    ambiguous_bar_count: int = 0
    missing_quote_count: int = 0
    #: Worst single-day fractional loss on the daily equity curve (>= 0).
    worst_day_loss: float = 0.0
    #: Fraction of (symbol, scan_ts) pairs backed by a historical quote, 0..1.
    quote_coverage: float = 1.0
    #: Fraction of orders that reached the fill stage and actually filled, 0..1.
    fill_rate: float = 1.0
    #: Optional raw metric bag (kept for fold-by-fold reporting).
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectiveResult:
    objective: float
    median_fold_score: float
    fold_scores: list[float]
    penalty_breakdown: dict[str, float]
    fold_variance: float


# --------------------------------------------------------------------------
# Daily mark-to-market drawdown
# --------------------------------------------------------------------------
def mark_to_market_drawdown(daily_bankroll: Sequence[float]) -> float:
    """Maximum peak-to-trough drawdown of the DAILY equity curve, as a fraction.

    ``daily_bankroll`` is the per-session bankroll series (mark-to-market — it
    includes unrealized PnL). Returns a value in ``[0, 1]``; ``0.0`` for an
    empty / single-point / monotone curve.
    """
    series = [float(v) for v in daily_bankroll if v is not None]
    if len(series) < 2:
        return 0.0
    peak = series[0]
    max_dd = 0.0
    for v in series:
        if v > peak:
            peak = v
        if peak > 0:
            max_dd = max(max_dd, (peak - v) / peak)
    return float(max_dd)


def worst_day_loss(daily_bankroll: Sequence[float]) -> float:
    """Largest single-session fractional loss on the daily equity curve.

    A crude one-point CVaR proxy: the worst day-over-day return, returned as a
    non-negative fraction (``0.0`` when every day was flat or up).
    """
    series = [float(v) for v in daily_bankroll if v is not None]
    if len(series) < 2:
        return 0.0
    worst = 0.0
    for prev, cur in zip(series, series[1:]):
        if prev > 0:
            ret = (cur - prev) / prev
            if ret < 0:
                worst = max(worst, -ret)
    return float(worst)


# --------------------------------------------------------------------------
# report.json -> FoldResult
# --------------------------------------------------------------------------
def _daily_bankroll_from_report(report: Mapping[str, Any]) -> list[float]:
    """Extract the per-session bankroll series from a Phase-8 ``report.json``."""
    pr = report.get("portfolio_and_risk") or {}
    rows = pr.get("daily_equity") or []
    out: list[float] = []
    for r in rows:
        if not isinstance(r, Mapping):
            continue
        v = r.get("bankroll")
        if v is not None:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                continue
    return out


def _metric_value(metrics: Iterable[Mapping[str, Any]], name: str, default: Any = 0.0) -> Any:
    """Look a ``{metric, value}`` row up by metric name."""
    for row in metrics or []:
        if isinstance(row, Mapping) and row.get("metric") == name:
            return row.get("value", default)
    return default


def fold_result_from_report(
    fold_id: str,
    report: Mapping[str, Any],
    summary: Mapping[str, Any] | None = None,
) -> FoldResult:
    """Build a :class:`FoldResult` from a Phase-8 ``report.json`` (+ optional summary).

    The drawdown is recomputed from the DAILY equity curve in the report — the
    closed-trade ``summary.max_drawdown_pct`` is deliberately ignored.
    """
    summary = summary or {}
    daily = _daily_bankroll_from_report(report)

    pr_metrics = (report.get("portfolio_and_risk") or {}).get("metrics") or []
    tp_metrics = (report.get("trade_performance") or {}).get("metrics") or []
    eq = (report.get("execution_quality") or {}).get("metrics") or []

    net_return = _metric_value(pr_metrics, "net_return_pct", summary.get("net_return_pct", 0.0))
    n_trades = _metric_value(tp_metrics, "n_trades", summary.get("n_trades", 0))
    fill_rate = _metric_value(eq, "fill_rate", summary.get("fill_rate", 1.0))
    quote_cov_pct = _metric_value(
        eq, "historical_quote_coverage_pct",
        summary.get("historical_quote_coverage_pct", 100.0),
    )
    missing_quote = _metric_value(eq, "missing_quote_count", summary.get("missing_quote_count", 0))

    dd = mark_to_market_drawdown(daily)
    wd = worst_day_loss(daily)
    return FoldResult(
        fold_id=fold_id,
        net_return=float(net_return or 0.0),
        max_drawdown=dd,
        turnover=float(summary.get("turnover", 0.0) or 0.0),
        concentration=float(summary.get("concentration", 0.0) or 0.0),
        n_trades=int(n_trades or 0),
        ambiguous_bar_count=int(summary.get("ambiguous_bar_count", 0) or 0),
        missing_quote_count=int(missing_quote or 0),
        worst_day_loss=wd,
        quote_coverage=float(quote_cov_pct or 0.0) / 100.0,
        fill_rate=float(fill_rate if fill_rate is not None else 1.0),
        metrics={
            "net_return_pct": float(net_return or 0.0),
            "mtm_max_drawdown_pct": dd,
            "worst_day_loss_pct": wd,
            "n_trades": int(n_trades or 0),
            "fill_rate": float(fill_rate if fill_rate is not None else 1.0),
            "historical_quote_coverage_pct": float(quote_cov_pct or 0.0),
            "missing_quote_count": int(missing_quote or 0),
        },
    )


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
def fold_penalties(
    fold: FoldResult, *, weights: PenaltyWeights = DEFAULT_PENALTY_WEIGHTS
) -> dict[str, float]:
    """Per-fold penalty breakdown (every value >= 0; subtracted from net return)."""
    # Low-trade-count penalty: ramps linearly from 0 (>= min_trade_count) to
    # the full weight as n_trades -> 0. Always finite.
    if fold.n_trades >= weights.min_trade_count:
        low_trade = 0.0
    else:
        deficit = weights.min_trade_count - max(0, fold.n_trades)
        low_trade = weights.low_trade_count * deficit / weights.min_trade_count

    coverage_shortfall = max(0.0, 1.0 - fold.quote_coverage)
    fill_shortfall = max(0.0, 1.0 - fold.fill_rate)
    return {
        "drawdown": weights.drawdown * max(0.0, fold.max_drawdown),
        "cvar": weights.cvar * max(0.0, fold.worst_day_loss),
        "turnover": weights.turnover * max(0.0, fold.turnover),
        "concentration": weights.concentration * max(0.0, fold.concentration),
        "low_trade_count": low_trade,
        "missing_quote": weights.missing_quote * max(0, fold.missing_quote_count),
        "missing_coverage": weights.missing_coverage * coverage_shortfall,
        "fill_rate": weights.fill_rate * fill_shortfall,
    }


def fold_score(
    fold: FoldResult, *, weights: PenaltyWeights = DEFAULT_PENALTY_WEIGHTS
) -> float:
    """Net return minus every per-fold penalty."""
    penalties = fold_penalties(fold, weights=weights)
    return float(fold.net_return - sum(penalties.values()))


def compute_objective(
    folds: Iterable[FoldResult], *, weights: PenaltyWeights = DEFAULT_PENALTY_WEIGHTS
) -> ObjectiveResult:
    """Median fold score minus a cross-fold metric-variance stability penalty.

    The variance penalty is the stdev of the per-fold scores scaled by
    ``weights.fold_variance`` — a strategy that scores wildly differently
    fold-to-fold is unstable and is penalized even if its median is high.
    """
    fold_list = list(folds)
    if not fold_list:
        return ObjectiveResult(
            objective=0.0, median_fold_score=0.0, fold_scores=[],
            penalty_breakdown={}, fold_variance=0.0,
        )
    scores = [fold_score(f, weights=weights) for f in fold_list]
    med = float(statistics.median(scores))
    variance = float(statistics.stdev(scores)) if len(scores) > 1 else 0.0
    var_penalty = weights.fold_variance * variance

    # Aggregate the per-fold penalty breakdown (mean across folds) for reporting.
    agg: dict[str, float] = {}
    for f in fold_list:
        for k, v in fold_penalties(f, weights=weights).items():
            agg[k] = agg.get(k, 0.0) + v
    agg = {k: v / len(fold_list) for k, v in agg.items()}
    agg["fold_variance"] = var_penalty

    objective = med - var_penalty
    if not math.isfinite(objective):
        objective = -1.0e9
    return ObjectiveResult(
        objective=objective,
        median_fold_score=med,
        fold_scores=scores,
        penalty_breakdown=agg,
        fold_variance=variance,
    )


__all__ = [
    "PenaltyWeights",
    "DEFAULT_PENALTY_WEIGHTS",
    "FoldResult",
    "ObjectiveResult",
    "mark_to_market_drawdown",
    "worst_day_loss",
    "fold_result_from_report",
    "fold_penalties",
    "fold_score",
    "compute_objective",
]
