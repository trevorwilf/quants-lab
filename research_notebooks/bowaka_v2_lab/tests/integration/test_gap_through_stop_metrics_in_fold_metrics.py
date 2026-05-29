"""Phase 2 (audit 2026-05-29 §8.5) — gap-through-stop metrics reach the fold +
objective penalty.

The backtester counts ``gap_stop`` exits into the summary (proven end-to-end by
``test_gap_through_stop_fills_at_open.py`` + the summary counter). This test
pins the summary -> FoldResult -> objective-penalty wiring and its default-off
parity (the penalty key is absent unless the weight is enabled).
"""
from __future__ import annotations

from types import SimpleNamespace

from bowaka_v2_lab.optuna.objective import (
    PenaltyWeights,
    fold_penalties,
    fold_result_from_backtest_result,
)


def _result_with_gap() -> SimpleNamespace:
    return SimpleNamespace(
        summary={
            "net_return_pct": 0.01, "n_trades": 20,
            "n_gap_through_events": 2, "gap_through_loss_dollars": 2000.0,
        },
        execution_quality_rows=[],
        daily_equity=[],
    )


def test_gap_through_metrics_flow_into_fold() -> None:
    fold = fold_result_from_backtest_result("f0", _result_with_gap())
    assert fold.n_gap_through_events == 2
    assert fold.gap_through_loss_dollars == 2000.0
    assert fold.metrics["n_gap_through_events"] == 2


def test_penalty_fires_only_when_weight_enabled() -> None:
    fold = fold_result_from_backtest_result("f0", _result_with_gap())
    # Default weights (gap_through_stop=0.0): the term is absent (parity).
    assert "gap_through_stop" not in fold_penalties(fold)
    # Enabled: the term appears and is positive (2000 excess -> capped 0.5).
    pen = fold_penalties(fold, weights=PenaltyWeights(gap_through_stop=1.0))
    assert pen["gap_through_stop"] > 0.0
