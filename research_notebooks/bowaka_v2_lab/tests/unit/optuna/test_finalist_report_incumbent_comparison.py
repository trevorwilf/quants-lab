"""``finalist_report`` carries per-row incumbent_comparison deltas.

Speedup report v2 §9 / Phase 5 task 2. Each finalist row records the
delta vs the incumbent on both validation and (when present) holdout.
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
    net_return: float = 0.0
    max_drawdown: float = 0.0
    worst_day_loss: float = 0.0
    fill_rate: float = 1.0
    quote_coverage: float = 1.0
    n_trades: int = 0
    turnover: float = 0.0
    concentration: float = 0.0
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class _StubTrial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def test_incumbent_comparison_delta_equals_validation_difference(
    tmp_path: Path,
) -> None:
    """Trial A objective 10, incumbent objective 8 → validation delta = 2."""
    trials = [
        _StubTrial(number=0, value=8.0, params={"x": 0.1},
                   user_attrs={"incumbent_trial": True}),
        _StubTrial(number=1, value=10.0, params={"x": 0.5}),
    ]

    def _score(params):
        return float({"0.1": 8.0, "0.5": 10.0}[str(params["x"])]), [
            _StubFold("f0", float({"0.1": 8.0, "0.5": 10.0}[str(params["x"])])),
        ]

    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=True),
        score_param_set=_score,
        output_dir=tmp_path / "f",
    )
    rows = {r["trial_number"]: r for r in result.finalists}
    # Trial #1 (objective 10) compared to incumbent (#0, objective 8) → delta 2.
    assert "incumbent_comparison" in rows[1]
    assert "validation" in rows[1]["incumbent_comparison"]
    assert abs(
        rows[1]["incumbent_comparison"]["validation"]["objective_delta"] - 2.0
    ) <= 1e-12
    # Incumbent vs itself → delta 0.
    assert abs(
        rows[0]["incumbent_comparison"]["validation"]["objective_delta"]
    ) <= 1e-12


def test_no_incumbent_comparison_when_no_incumbent_trial(tmp_path: Path) -> None:
    """When no trial is flagged as incumbent the comparison block is absent."""
    trials = [
        _StubTrial(number=0, value=8.0, params={"x": 0.1}),
        _StubTrial(number=1, value=10.0, params={"x": 0.5}),
    ]

    def _score(params):
        return 5.0, [_StubFold("f0", 5.0)]

    result = evaluate_finalists(
        completed_trials=trials,
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=True),
        score_param_set=_score,
        output_dir=tmp_path / "f",
    )
    for r in result.finalists:
        assert "incumbent_comparison" not in r or not r["incumbent_comparison"]
