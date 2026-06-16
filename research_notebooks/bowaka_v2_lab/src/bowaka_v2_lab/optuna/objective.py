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
                   - pick_quality_penalty       (frac of trades below the
                                                 0.5% per-pick minimum)

Per-pick quality
----------------
``net_return`` is the portfolio's fold return (overall PnL) and stays the
primary positive driver. The ``pick_quality`` penalty additionally subtracts
``weight x (fraction of trades that did NOT clear the per-trade minimum
profit bar`` (``metrics.PICK_QUALITY_MIN_PCT`` = 0.5%), so a config whose
individual picks are weak is penalized even when a few large winners prop up
``net_return``. The 4% "ideal" upside (``PICK_QUALITY_STRETCH_PCT``) is left
to ``net_return`` (bigger winners -> bigger PnL) and surfaced in the metrics
for review, rather than scored separately, to avoid pushing the optimizer
into ultra-selectivity.

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

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --------------------------------------------------------------------------
# Realism remediation 2 Phase 8 (audit §P1-008) — unit consistency.
#
# Every term in the objective MUST be in DECIMAL RETURNS (``0.03`` = 3%) — not
# in PERCENT (``3.0`` = 3%). Mixed units silently swap which penalty dominates
# the objective by two orders of magnitude. ``MetricUnits`` is a Pydantic guard
# that validates incoming fold metrics and raises ``MetricUnitsError`` on a
# value that is plainly in the wrong units.
# --------------------------------------------------------------------------
class MetricUnitsError(ValueError):
    """Raised when a fold metric is in the wrong units (percent vs decimal)."""


#: Maximum plausible decimal value for a fold-level RETURN — `>2.0` (200%) is a
#: dead giveaway that the metric is in percent (e.g. ``3.0`` for ``3%`` instead
#: of ``0.03``). A walk-forward fold returning 200%+ in a single quarter is not
#: a credible research result; it almost always indicates a units bug.
_RETURN_DECIMAL_MAX = 2.0
#: Maximum plausible decimal value for a fold-level DRAWDOWN / LOSS — these are
#: always in ``[0, 1]``; ``>1.5`` is a percent-vs-decimal mix-up.
_LOSS_DECIMAL_MAX = 1.5
#: Decimal-coverage fields are always in ``[0, 1]``; ``>1.5`` is a percent input.
_COVERAGE_DECIMAL_MAX = 1.5


class MetricUnits(BaseModel):
    """Pydantic guard for per-fold metrics passed to the objective.

    Every metric is REQUIRED to be in decimal returns (e.g. ``0.03`` for 3%,
    ``0.85`` for an 85% fill rate). The validators below reject values that are
    plainly in percent units — they raise :class:`MetricUnitsError` with the
    offending field name and a one-line "you probably meant" hint.

    Range checks are done in :py:meth:`_validate_unit_ranges` (not via Pydantic
    ``Field(ge=..., le=...)``) so every failure routes through
    :class:`MetricUnitsError` rather than the generic Pydantic ValidationError.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=False)

    net_return: float = Field(..., description="Decimal return, e.g. 0.03 for +3%")
    max_drawdown: float = Field(...,
                                description="Daily MTM max drawdown fraction, [0, 1]")
    worst_day_loss: float = Field(...,
                                  description="Worst single-day fractional loss, [0, 1]")
    quote_coverage: float = Field(...,
                                  description="Fraction of (sym, scan_ts) with a real quote, [0, 1]")
    fill_rate: float = Field(...,
                             description="Fraction of orders that filled, [0, 1]")
    turnover: float = Field(0.0)
    concentration: float = Field(0.0)
    n_trades: int = Field(0)
    missing_quote_count: int = Field(0)
    ambiguous_bar_count: int = Field(0)

    @classmethod
    def build(cls, **kwargs: Any) -> "MetricUnits":
        """Construct + validate, re-raising any Pydantic ValidationError as MetricUnitsError.

        Tests and the runtime path call this rather than the raw constructor so
        every failure routes through :class:`MetricUnitsError` — the audit
        §P1-008 contract requires a single error type for downstream catching.
        """
        try:
            return cls(**kwargs)
        except MetricUnitsError:
            raise
        except Exception as exc:  # noqa: BLE001 — Pydantic ValidationError -> MetricUnitsError
            raise MetricUnitsError(str(exc)) from exc

    @model_validator(mode="after")
    def _validate_unit_ranges(self) -> "MetricUnits":
        # net_return: decimal returns; |v| > _RETURN_DECIMAL_MAX means percent.
        if not math.isfinite(self.net_return):
            raise MetricUnitsError(f"net_return must be finite, got {self.net_return!r}")
        if abs(self.net_return) > _RETURN_DECIMAL_MAX:
            raise MetricUnitsError(
                f"net_return={self.net_return!r} is out of the decimal-return "
                f"range (|v| > {_RETURN_DECIMAL_MAX}). The objective expects "
                f"decimal returns (0.03 = 3%), not percent (3.0 = 3%). "
                f"Convert with /100."
            )
        if self.max_drawdown < 0.0 or self.max_drawdown > _LOSS_DECIMAL_MAX:
            raise MetricUnitsError(
                f"max_drawdown={self.max_drawdown!r} out of [0, 1] — looks like "
                f"a percent (e.g. 8.0 instead of 0.08)."
            )
        if self.worst_day_loss < 0.0 or self.worst_day_loss > _LOSS_DECIMAL_MAX:
            raise MetricUnitsError(
                f"worst_day_loss={self.worst_day_loss!r} out of [0, 1] — looks "
                f"like a percent."
            )
        if self.quote_coverage < 0.0 or self.quote_coverage > _COVERAGE_DECIMAL_MAX:
            raise MetricUnitsError(
                f"quote_coverage={self.quote_coverage!r} out of [0, 1] — looks "
                f"like a percent (e.g. 95.0 instead of 0.95)."
            )
        if self.fill_rate < 0.0 or self.fill_rate > _COVERAGE_DECIMAL_MAX:
            raise MetricUnitsError(
                f"fill_rate={self.fill_rate!r} out of [0, 1] — looks like a "
                f"percent (e.g. 95.0 instead of 0.95)."
            )
        if self.turnover < 0.0:
            raise MetricUnitsError(f"turnover={self.turnover!r} must be >= 0")
        if self.concentration < 0.0 or self.concentration > 1.0:
            raise MetricUnitsError(
                f"concentration={self.concentration!r} out of [0, 1]"
            )
        if self.n_trades < 0:
            raise MetricUnitsError(f"n_trades={self.n_trades!r} must be >= 0")
        if self.missing_quote_count < 0:
            raise MetricUnitsError(
                f"missing_quote_count={self.missing_quote_count!r} must be >= 0"
            )
        if self.ambiguous_bar_count < 0:
            raise MetricUnitsError(
                f"ambiguous_bar_count={self.ambiguous_bar_count!r} must be >= 0"
            )
        return self


def validate_metric_units(fold: "FoldResult") -> "FoldResult":
    """Validate a :class:`FoldResult`'s metric units. Returns ``fold`` unchanged.

    Realism remediation 2 Phase 8 (audit §P1-008): every term must be in decimal
    returns; raises :class:`MetricUnitsError` if any term is in the wrong units.
    Called by :func:`compute_objective` so every study run is unit-validated.
    """
    MetricUnits.build(
        net_return=fold.net_return,
        max_drawdown=fold.max_drawdown,
        worst_day_loss=fold.worst_day_loss,
        quote_coverage=fold.quote_coverage,
        fill_rate=fold.fill_rate,
        turnover=fold.turnover,
        concentration=fold.concentration,
        n_trades=fold.n_trades,
        missing_quote_count=fold.missing_quote_count,
        ambiguous_bar_count=fold.ambiguous_bar_count,
    )
    return fold


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

    #: Per-pick quality (operator goal 2026-05-28): each pick should clear a
    #: minimum profit bar (0.5%, see ``metrics.PICK_QUALITY_MIN_PCT``). This
    #: weight x the fraction of trades that FAIL that bar is subtracted from
    #: the fold score, so a config whose picks are individually weak is
    #: penalized even when a few big winners prop up ``net_return``. Kept
    #: modest so ``net_return`` (overall PnL) stays the primary driver and the
    #: optimizer is not pushed into ultra-selectivity (the 4% upside is
    #: already rewarded through ``net_return``). Tune here if you want pick
    #: quality to weigh more / less.
    pick_quality: float = 0.10     # x fraction of trades below the min profit bar

    #: A fold with fewer than this many trades is statistically uninformative;
    #: the low-trade-count penalty ramps to its max as n_trades -> 0.
    #:
    #: 2026-05-28 (operator): lowered 30 -> 10 to match the live strategy's
    #: natural selectivity. The strategy trades ~1-6 names/day; a validation
    #: fold is one month (~21 sessions), so even the LOW end of normal
    #: (1/day) is ~21 trades/fold. A floor of 10 (~0.5/day) leaves the entire
    #: 1-6/day range unpenalized and only flags genuinely degenerate configs
    #: (gates so tight the strategy barely trades). Trade COUNT is a
    #: statistical-significance floor only — per-pick profitability + overall
    #: PnL are carried by ``net_return`` (and, if enabled, the per-trade
    #: quality terms).
    min_trade_count: int = 10

    #: Audit 2026-05-29 §8.5 / Phase 4b — timing-adjacent stress penalties. Both
    #: default to 0.0 so the unstressed objective is byte-identical; the
    #: stress-matrix / paper-candidate path raises them to activate the penalty.
    gap_through_stop: float = 0.0          # multiplier on gap_through_stop_penalty
    same_minute_ambiguity: float = 0.0     # multiplier on same_minute_ambiguity_penalty


DEFAULT_PENALTY_WEIGHTS = PenaltyWeights()


# --------------------------------------------------------------------------
# Audit 2026-05-29 §9 Phase 5 — fold-level activity gates.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class FoldActivityGates:
    min_trades_per_fold: int = 5
    min_active_days_per_fold: int = 3


def fold_is_active_enough(
    fold_metrics: Mapping[str, Any], gates: "FoldActivityGates" = FoldActivityGates(),
) -> bool:
    """True iff the fold cleared BOTH the minimum trade count and the minimum
    distinct-active-days floor — a statistically informative fold."""
    return (
        int(fold_metrics.get("n_trades", 0) or 0) >= gates.min_trades_per_fold
        and int(fold_metrics.get("n_active_days", 0) or 0) >= gates.min_active_days_per_fold
    )


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
    #: Fraction of closed trades whose per-trade return cleared the minimum
    #: profit bar (``metrics.PICK_QUALITY_MIN_PCT`` = 0.5%), 0..1. Defaults to
    #: 1.0 (no quality penalty) when unknown / no trades.
    frac_trades_ge_min_profit: float = 1.0
    #: Fold health (audit 2026-05-29 §A.5 / Phase 0 task 6). ``"ok"`` for a
    #: fold whose backtest ran; ``"degraded"`` when a non-structural exception
    #: forced :func:`_degraded_fold`. A trial with ANY non-``"ok"`` fold is
    #: rejected by the valid-trial filter and flags the study invalid
    #: (``DEGRADED_FOLDS_PRESENT``) — a degraded fold is not a valid datapoint.
    fold_status: str = "ok"
    #: Audit 2026-05-29 §8.5 / Phase 4b — gap-through-stop counters (a bar that
    #: opens past the stop fills at the open, taking the gap loss). Default 0 so
    #: a fold without gap-through events (or built before Phase 2) is penalty-free.
    n_gap_through_events: int = 0
    gap_through_loss_dollars: float = 0.0
    expected_gap_through_loss_dollars: float = 0.0
    #: Audit 2026-05-29 §9 Phase 5 — distinct sessions with >=1 fill in the fold.
    n_active_days: int = 0
    #: Optional raw metric bag (kept for fold-by-fold reporting).
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectiveResult:
    objective: float
    median_fold_score: float
    fold_scores: list[float]
    penalty_breakdown: dict[str, float]
    fold_variance: float
    #: Realism remediation 2 Phase 8 (audit §P1-008) — every term's contribution
    #: to the final objective. ``median_net_return`` is the positive driver; the
    #: rest are penalties (subtracted). The keys mirror ``fold_penalties()`` plus
    #: ``median_net_return`` and ``fold_variance``. Verifiable invariant:
    #: ``median_net_return - sum(<the penalty terms>) - fold_variance ≈ objective``.
    objective_terms: dict[str, float] = field(default_factory=dict)


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


def fold_result_from_backtest_result(
    fold_id: str,
    result: Any,
) -> FoldResult:
    """Build a :class:`FoldResult` from a :class:`BacktestResult` in memory.

    Speedup report §5.1 / §11.2 Phase 1: when ``run_backtest`` was called with
    ``artifact_mode="objective_minimal"`` no ``report.json`` exists on disk,
    so the objective consumes the in-memory result fields directly. The
    drawdown is recomputed from ``result.daily_equity`` (mark-to-market) —
    the closed-trade ``summary.max_drawdown_pct`` is deliberately ignored.
    The fill-rate / quote-coverage / missing-quote-count lookup order
    matches :func:`fold_result_from_report` exactly: execution_quality_rows
    first, summary fallback.
    """
    summary = dict(result.summary or {})
    eq_rows = list(getattr(result, "execution_quality_rows", []) or [])
    daily_rows = list(getattr(result, "daily_equity", []) or [])
    bankroll = [
        float(r.get("bankroll", 0.0))
        for r in daily_rows
        if isinstance(r, Mapping) and r.get("bankroll") is not None
    ]

    net_return = summary.get("net_return_pct", 0.0)
    n_trades = summary.get("n_trades", 0)
    fill_rate = _metric_value(eq_rows, "fill_rate", summary.get("fill_rate", 1.0))
    quote_cov_pct = _metric_value(
        eq_rows, "historical_quote_coverage_pct",
        summary.get("historical_quote_coverage_pct", 100.0),
    )
    missing_quote = _metric_value(
        eq_rows, "missing_quote_count", summary.get("missing_quote_count", 0)
    )

    dd = mark_to_market_drawdown(bankroll)
    wd = worst_day_loss(bankroll)
    frac_ge_min = float(summary.get("frac_trades_ge_min_profit", 1.0) or 1.0)
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
        frac_trades_ge_min_profit=frac_ge_min,
        n_gap_through_events=int(summary.get("n_gap_through_events", 0) or 0),
        gap_through_loss_dollars=float(summary.get("gap_through_loss_dollars", 0.0) or 0.0),
        expected_gap_through_loss_dollars=float(
            summary.get("expected_gap_through_loss_dollars", 0.0) or 0.0),
        n_active_days=int(summary.get("n_active_days", 0) or 0),
        metrics={
            "net_return_pct": float(net_return or 0.0),
            "mtm_max_drawdown_pct": dd,
            "worst_day_loss_pct": wd,
            "n_trades": int(n_trades or 0),
            "fill_rate": float(fill_rate if fill_rate is not None else 1.0),
            "historical_quote_coverage_pct": float(quote_cov_pct or 0.0),
            "missing_quote_count": int(missing_quote or 0),
            "n_gap_through_events": int(summary.get("n_gap_through_events", 0) or 0),
            # Per-pick quality (operator goal: each pick >= 0.5%, ideally 4%).
            "frac_trades_ge_min_profit": frac_ge_min,
            "frac_trades_ge_stretch_profit": float(
                summary.get("frac_trades_ge_stretch_profit", 0.0) or 0.0
            ),
            "avg_trade_return_pct": float(summary.get("avg_trade_return_pct", 0.0) or 0.0),
            "median_trade_return_pct": float(
                summary.get("median_trade_return_pct", 0.0) or 0.0
            ),
            "win_rate": float(summary.get("win_rate", 0.0) or 0.0),
        },
    )


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
    # Per-pick quality: prefer the report's trade_performance metric, fall back
    # to the summary (which build_summary always populates), default 1.0.
    frac_ge_min = float(
        _metric_value(
            tp_metrics, "frac_trades_ge_min_profit",
            summary.get("frac_trades_ge_min_profit", 1.0),
        ) or 1.0
    )
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
        frac_trades_ge_min_profit=frac_ge_min,
        n_gap_through_events=int(summary.get("n_gap_through_events", 0) or 0),
        gap_through_loss_dollars=float(summary.get("gap_through_loss_dollars", 0.0) or 0.0),
        expected_gap_through_loss_dollars=float(
            summary.get("expected_gap_through_loss_dollars", 0.0) or 0.0),
        n_active_days=int(summary.get("n_active_days", 0) or 0),
        metrics={
            "net_return_pct": float(net_return or 0.0),
            "mtm_max_drawdown_pct": dd,
            "worst_day_loss_pct": wd,
            "n_trades": int(n_trades or 0),
            "fill_rate": float(fill_rate if fill_rate is not None else 1.0),
            "historical_quote_coverage_pct": float(quote_cov_pct or 0.0),
            "missing_quote_count": int(missing_quote or 0),
            "frac_trades_ge_min_profit": frac_ge_min,
            "frac_trades_ge_stretch_profit": float(
                _metric_value(
                    tp_metrics, "frac_trades_ge_stretch_profit",
                    summary.get("frac_trades_ge_stretch_profit", 0.0),
                ) or 0.0
            ),
            "avg_trade_return_pct": float(
                _metric_value(
                    tp_metrics, "avg_trade_return_pct",
                    summary.get("avg_trade_return_pct", 0.0),
                ) or 0.0
            ),
            "win_rate": float(
                _metric_value(tp_metrics, "win_rate", summary.get("win_rate", 0.0)) or 0.0
            ),
        },
    )


# --------------------------------------------------------------------------
# Audit 2026-05-29 §8.5 / Phase 4b — timing-adjacent objective penalties.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class GapThroughStopMetrics:
    n_gap_through_events: int
    gap_through_loss_dollars_total: float
    expected_gap_through_loss_dollars: float   # n_events * mean planned stop-loss


def gap_through_stop_penalty(
    metrics: GapThroughStopMetrics,
    *,
    max_penalty: float = 0.5,
    expected_loss_scale: float = 1000.0,    # $1000 of excess loss = full penalty
) -> float:
    """Penalty proportional to the dollar loss in EXCESS of the stop-as-planned.

    ``max_penalty`` (default 0.5) caps the penalty so a few gap-through events
    do not dominate the objective.
    """
    excess = max(
        0.0,
        float(metrics.gap_through_loss_dollars_total)
        - float(metrics.expected_gap_through_loss_dollars),
    )
    return float(min(max_penalty, excess / expected_loss_scale))


@dataclass(frozen=True)
class SameMinuteAmbiguityMetrics:
    n_ambiguous_bars: int
    n_resolved_as_stop: int       # conservative tie-break count


def same_minute_ambiguity_penalty(
    metrics: SameMinuteAmbiguityMetrics,
    *,
    max_penalty: float = 0.2,
    per_event: float = 0.005,
) -> float:
    """Penalty proportional to the count of ambiguous (stop AND target in one
    bar) bars. Caps at ``max_penalty``; per-event default 0.005."""
    return float(min(max_penalty, per_event * max(0, int(metrics.n_ambiguous_bars))))


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
    # Per-pick quality: penalize the fraction of trades that did NOT clear the
    # minimum profit bar. ``getattr`` default keeps stub folds (no such field)
    # penalty-free. No double-penalty for 0-trade folds — they default to 1.0.
    frac_ge_min = float(getattr(fold, "frac_trades_ge_min_profit", 1.0))
    pick_quality_shortfall = max(0.0, 1.0 - max(0.0, min(1.0, frac_ge_min)))
    out = {
        "drawdown": weights.drawdown * max(0.0, fold.max_drawdown),
        "cvar": weights.cvar * max(0.0, fold.worst_day_loss),
        "turnover": weights.turnover * max(0.0, fold.turnover),
        "concentration": weights.concentration * max(0.0, fold.concentration),
        "low_trade_count": low_trade,
        "missing_quote": weights.missing_quote * max(0, fold.missing_quote_count),
        "missing_coverage": weights.missing_coverage * coverage_shortfall,
        "fill_rate": weights.fill_rate * fill_shortfall,
        "pick_quality": weights.pick_quality * pick_quality_shortfall,
    }
    # Audit 2026-05-29 §8.5 / Phase 4b — the gap-through-stop and same-minute
    # ambiguity terms are added ONLY when their weight is enabled (>0), so the
    # default penalty breakdown (and the objective) is byte-identical to pre-
    # Phase-2 for the unstressed weights.
    if weights.gap_through_stop > 0:
        out["gap_through_stop"] = weights.gap_through_stop * gap_through_stop_penalty(
            GapThroughStopMetrics(
                n_gap_through_events=int(getattr(fold, "n_gap_through_events", 0)),
                gap_through_loss_dollars_total=float(
                    getattr(fold, "gap_through_loss_dollars", 0.0)),
                expected_gap_through_loss_dollars=float(
                    getattr(fold, "expected_gap_through_loss_dollars", 0.0)),
            )
        )
    if weights.same_minute_ambiguity > 0:
        out["same_minute_ambiguity"] = weights.same_minute_ambiguity * same_minute_ambiguity_penalty(
            SameMinuteAmbiguityMetrics(
                n_ambiguous_bars=int(getattr(fold, "ambiguous_bar_count", 0)),
                n_resolved_as_stop=int(getattr(fold, "ambiguous_bar_count", 0)),
            )
        )
    return out


def fold_score(
    fold: FoldResult, *, weights: PenaltyWeights = DEFAULT_PENALTY_WEIGHTS
) -> float:
    """Net return minus every per-fold penalty."""
    penalties = fold_penalties(fold, weights=weights)
    return float(fold.net_return - sum(penalties.values()))


def compute_objective(
    folds: Iterable[FoldResult],
    *,
    weights: PenaltyWeights = DEFAULT_PENALTY_WEIGHTS,
    validate_units: bool = True,
) -> ObjectiveResult:
    """Median fold score minus a cross-fold metric-variance stability penalty.

    The variance penalty is the stdev of the per-fold scores scaled by
    ``weights.fold_variance`` — a strategy that scores wildly differently
    fold-to-fold is unstable and is penalized even if its median is high.

    Realism remediation 2 Phase 8 (audit §P1-008): every per-fold metric is
    validated through :class:`MetricUnits` (decimal returns only); raises
    :class:`MetricUnitsError` on a mixed-units fold. Pass ``validate_units=False``
    only when the caller has already validated (e.g. fixture-driven unit tests
    that exercise edge cases the strict validator would reject).
    """
    fold_list = list(folds)
    if not fold_list:
        return ObjectiveResult(
            objective=0.0, median_fold_score=0.0, fold_scores=[],
            penalty_breakdown={}, fold_variance=0.0, objective_terms={},
        )
    if validate_units:
        for f in fold_list:
            validate_metric_units(f)
    # p2 #6: compute fold_penalties ONCE per fold — it was called twice (inside
    # fold_score AND the aggregation loop below). scores[i] is byte-identical to
    # fold_score(f) (defined as float(net_return - sum(penalties.values()))), and
    # the agg loop reuses the same dicts. Pure dedup; no behavior change.
    fold_penalty_dicts = [fold_penalties(f, weights=weights) for f in fold_list]
    scores = [float(f.net_return - sum(p.values()))
              for f, p in zip(fold_list, fold_penalty_dicts)]
    med = float(statistics.median(scores))
    variance = float(statistics.stdev(scores)) if len(scores) > 1 else 0.0
    var_penalty = weights.fold_variance * variance

    # Aggregate the per-fold penalty breakdown (mean across folds) for reporting.
    agg: dict[str, float] = {}
    for p in fold_penalty_dicts:
        for k, v in p.items():
            agg[k] = agg.get(k, 0.0) + v
    agg = {k: v / len(fold_list) for k, v in agg.items()}
    agg["fold_variance"] = var_penalty

    objective = med - var_penalty
    if not math.isfinite(objective):
        objective = -1.0e9

    # Realism remediation 2 Phase 8 (audit §P1-008) — explicit term breakdown.
    # The keys are: ``median_net_return`` (positive driver) + every penalty key
    # from ``fold_penalties()`` (subtracted) + ``fold_variance`` (subtracted).
    # A consumer can verify median_net_return - sum(penalty keys) - fold_variance
    # ≈ objective up to median-vs-mean rounding (we report the mean penalty
    # across folds, not the per-fold median, so this is an inspectable
    # decomposition, not an exact equality).
    median_net_return = float(statistics.median([f.net_return for f in fold_list]))
    objective_terms: dict[str, float] = {"median_net_return": median_net_return}
    for k, v in agg.items():
        objective_terms[k] = float(v)
    objective_terms["objective"] = float(objective)
    objective_terms["median_fold_score"] = float(med)

    return ObjectiveResult(
        objective=objective,
        median_fold_score=med,
        fold_scores=scores,
        penalty_breakdown=agg,
        fold_variance=variance,
        objective_terms=objective_terms,
    )


__all__ = [
    "PenaltyWeights",
    "DEFAULT_PENALTY_WEIGHTS",
    "FoldResult",
    "ObjectiveResult",
    "MetricUnits",
    "MetricUnitsError",
    "validate_metric_units",
    "mark_to_market_drawdown",
    "worst_day_loss",
    "fold_result_from_backtest_result",
    "fold_result_from_report",
    "fold_penalties",
    "fold_score",
    "compute_objective",
    "GapThroughStopMetrics",
    "gap_through_stop_penalty",
    "SameMinuteAmbiguityMetrics",
    "same_minute_ambiguity_penalty",
    "FoldActivityGates",
    "fold_is_active_enough",
]
