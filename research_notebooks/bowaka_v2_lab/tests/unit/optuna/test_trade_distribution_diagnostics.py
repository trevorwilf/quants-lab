"""Phase 5 — trade-distribution diagnostics drive symbol-concentration stop-ship.

A fixture trade set with one symbol owning 30% of trades must surface in the
trade diagnostics AND trip the stop-ship "one symbol > 25%" failure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bowaka_v2_lab.optuna.evaluate_finalists import (
    FinalistEvaluationConfig,
    evaluate_finalists,
)


@dataclass
class _StubFold:
    fold_id: str
    objective: float
    n_trades: int = 10


@dataclass
class _StubTrial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def _score(params):
    return 1.0, [_StubFold("f0", 1.0)]


def _holdout(params):
    return [_StubFold("holdout", 1.0)]


def _concentrated_trade_diag(params):
    """One symbol owns 30% of trades; 100 total trades."""
    return {
        "total_trades": 100,
        "max_symbol_share": 0.30,
        "top_symbols": [{"symbol": "AAA", "share": 0.30}],
        "exit_type_counts": {"stop": 40, "target": 30, "time_stop": 30},
        "median_hold_sessions": 1.0,
    }


def test_trade_diagnostics_present_and_trips_stop_ship(tmp_path: Path) -> None:
    trials = [
        _StubTrial(number=i, value=10.0 - i, params={"exits.stop_pct": 0.025})
        for i in range(2)
    ]
    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=False),
        score_param_set=_score,
        holdout_scorer=_holdout,
        trade_diagnostics_provider=_concentrated_trade_diag,
        output_dir=tmp_path / "f",
    )
    fe = result.report["finalist_evaluation"]
    # The diagnostics are recorded for the exported finalist.
    assert fe["trade_diagnostics"]["exported"]["max_symbol_share"] == 0.30
    # And the stop-ship checklist flags the concentration.
    decision = fe["stop_ship"]
    assert decision["passed"] is False
    assert any("symbol concentration" in f for f in decision["failures"])
