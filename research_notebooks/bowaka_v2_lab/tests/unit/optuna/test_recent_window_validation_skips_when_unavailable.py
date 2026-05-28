"""Phase 5 — recent-window validation skips gracefully when unavailable."""
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
    n_trades: int = 5


@dataclass
class _StubTrial:
    number: int
    value: float
    params: dict[str, Any]
    user_attrs: dict[str, Any] = field(default_factory=dict)


def _score(params):
    return 1.0, [_StubFold("f0", 1.0)]


def _trials():
    return [_StubTrial(number=i, value=10.0 - i, params={"exits.stop_pct": 0.025})
            for i in range(2)]


def test_recent_window_skipped_when_no_scorer(tmp_path: Path) -> None:
    result = evaluate_finalists(
        completed_trials=_trials(),
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=False),
        score_param_set=_score,
        output_dir=tmp_path / "f",
    )
    rw = result.report["finalist_evaluation"]["recent_window"]
    assert rw["skipped"] is True


def test_recent_window_skipped_when_scorer_returns_none(tmp_path: Path) -> None:
    result = evaluate_finalists(
        completed_trials=_trials(),
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=False),
        score_param_set=_score,
        recent_window_scorer=lambda params: None,  # no slice available
        output_dir=tmp_path / "f",
    )
    rw = result.report["finalist_evaluation"]["recent_window"]
    assert rw["skipped"] is True
    assert "no recent slice" in rw["reason"]


def test_recent_window_present_when_scorer_returns_metrics(tmp_path: Path) -> None:
    result = evaluate_finalists(
        completed_trials=_trials(),
        finalist_cfg=FinalistEvaluationConfig(top_k=2, include_incumbent=False),
        score_param_set=_score,
        recent_window_scorer=lambda params: {"objective": 0.9, "n_trades": 12},
        output_dir=tmp_path / "f",
    )
    rw = result.report["finalist_evaluation"]["recent_window"]
    assert rw.get("skipped") is not True
    assert rw["objective"] == 0.9
