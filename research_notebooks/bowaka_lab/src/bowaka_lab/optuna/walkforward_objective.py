"""Phase fidelity-8: walk-forward Optuna objective that runs the full pipeline.

Replaces the smoke objective for production use. Each Optuna trial:

1. Suggests params via ``suggest_params(trial, cfg=base_cfg)``.
2. For each ``(train_start, train_end, test_start, test_end)`` fold (excluding
   the final holdout fold), instantiates ``BowakaPortfolioBacktester``
   against the test window, collects ``FoldStats``.
3. Aggregates via ``evaluate_objective``, then subtracts extra penalties:
   confirmation-fail rate, stop-gap concentration, capacity-violation rate.

The final entry in ``ctx.folds`` is the holdout — ``build_walkforward_objective``
slices ``ctx.folds[:-1]`` and refuses to tune on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import optuna

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.optuna.objective import (
    FoldStats,
    ObjectiveWeights,
    evaluate_objective,
)
from bowaka_lab.optuna.search_space import suggest_params


FoldTuple = tuple[date, date, date, date]


@dataclass
class WalkforwardObjectiveContext:
    """Bundles every input the walk-forward objective needs."""

    base_cfg: BowakaBacktestConfig
    folds: list[FoldTuple]
    weights: ObjectiveWeights = field(default_factory=ObjectiveWeights)
    daily_bars_path: Path | None = None
    minute_bars_path: Path | None = None
    quotes_path: Path | None = None
    asset_snapshot_path: Path | None = None
    backtest_runner: Callable | None = None  # for tests to inject a fake


def _apply_trial_params(cfg: BowakaBacktestConfig, params: dict) -> BowakaBacktestConfig:
    """Map suggested params onto a ``BowakaBacktestConfig`` copy.

    The search space returns nested keys for prefilter / exits gates;
    we route them through ``model_copy(update=...)`` on the leaf model.
    """
    pref_updates = {k: v for k, v in params.items() if k in {
        "rvol_min", "atr_pct_min", "range_expansion_min", "close_location_min",
        "ema_distance_min", "ema_slope_min", "price_min", "price_max",
        "avg_dollar_volume_min",
    }}
    exits_updates = {k: v for k, v in params.items() if k in {
        "stop_pct", "target_pct", "max_hold_days",
    }}
    entry_updates = {k: v for k, v in params.items() if k in {
        "default_rule",
    }}
    updates: dict = {}
    if pref_updates:
        updates["prefilter"] = cfg.prefilter.model_copy(update=pref_updates)
    if exits_updates:
        updates["exits"] = cfg.exits.model_copy(update=exits_updates)
    if entry_updates:
        updates["entry"] = cfg.entry.model_copy(update=entry_updates)
    return cfg.model_copy(update=updates) if updates else cfg


def _fold_stats_from_result(result) -> FoldStats:
    """Build a ``FoldStats`` from a runner result.

    The real runner returns a ``BowakaBacktestResult``; tests inject a
    smaller object with the same shape (``trades`` iterable of objects
    carrying ``pnl_pct``).
    """
    trades = getattr(result, "trades", None) or []
    test_returns = []
    for t in trades:
        pct = getattr(t, "pnl_pct", None)
        if pct is None and isinstance(t, dict):
            pct = t.get("pnl_pct")
        if pct is not None:
            test_returns.append(float(pct))
    worst = min(test_returns) if test_returns else 0.0
    return FoldStats(
        test_returns=test_returns,
        trade_count=len(trades),
        max_drawdown_pct=float(getattr(result, "max_drawdown_pct", 0.0)),
        turnover=float(getattr(result, "turnover", 0.0)),
        worst_trade_pct=worst,
    )


def build_walkforward_objective(
    ctx: WalkforwardObjectiveContext,
) -> Callable[[optuna.Trial], float]:
    """Return an objective callable usable by ``Study.optimize``.

    CRITICAL: ``ctx.folds[-1]`` is the holdout. The optimizer only sees
    ``ctx.folds[:-1]``. The holdout fold is for non-tuning evaluation only.
    """

    if len(ctx.folds) < 2:
        raise ValueError(
            "walk-forward context needs at least 2 folds (one train + one holdout)"
        )

    def objective(trial: optuna.Trial) -> float:
        params = _suggest_with_cfg(trial, ctx.base_cfg)
        cfg = _apply_trial_params(ctx.base_cfg, params)
        fold_stats: list[FoldStats] = []
        # Slice off the holdout fold — never tune on it.
        for fold in ctx.folds[:-1]:
            tr_start, tr_end, te_start, te_end = fold
            sub_cfg = cfg.model_copy(update={
                "data": cfg.data.model_copy(update={
                    "start_date": te_start, "end_date": te_end,
                })
            })
            runner = ctx.backtest_runner
            if runner is None:
                raise NotImplementedError(
                    "Production walk-forward objective requires ctx.backtest_runner. "
                    "Tests inject a fake runner; notebook 10 wires the real one."
                )
            result = runner(sub_cfg)
            fold_stats.append(_fold_stats_from_result(result))
        score = evaluate_objective(folds=fold_stats, weights=ctx.weights)
        # Extra penalties: confirmation-fail rate, stop-gap concentration,
        # capacity-violation rate. The current FoldStats schema doesn't
        # carry these yet; the placeholders below return 0 so the penalty
        # is a no-op until the engine emits them.
        confirmation_fail_rate = _compute_confirmation_fail_rate(fold_stats)
        stop_gap_concentration = _compute_stop_gap_concentration(fold_stats)
        capacity_violation_rate = _compute_capacity_violation_rate(fold_stats)
        score -= 1.0 * max(0.0, confirmation_fail_rate - 0.20) ** 2
        score -= 1.0 * max(0.0, stop_gap_concentration - 0.30) ** 2
        score -= 1.0 * capacity_violation_rate
        return score

    return objective


def _suggest_with_cfg(trial: optuna.Trial, cfg: BowakaBacktestConfig) -> dict:
    """Wrapper around ``suggest_params`` that future-proofs for the
    config-aware signature. Existing ``suggest_params(trial)`` keeps working.
    """
    try:
        return suggest_params(trial, cfg=cfg)  # type: ignore[call-arg]
    except TypeError:
        return suggest_params(trial)


def _compute_confirmation_fail_rate(folds: list[FoldStats]) -> float:
    rates = [getattr(f, "confirmation_fail_rate", 0.0) for f in folds]
    return float(sum(rates) / len(rates)) if rates else 0.0


def _compute_stop_gap_concentration(folds: list[FoldStats]) -> float:
    rates = [getattr(f, "stop_gap_rate", 0.0) for f in folds]
    return float(sum(rates) / len(rates)) if rates else 0.0


def _compute_capacity_violation_rate(folds: list[FoldStats]) -> float:
    rates = [getattr(f, "capacity_violation_rate", 0.0) for f in folds]
    return float(sum(rates) / len(rates)) if rates else 0.0
