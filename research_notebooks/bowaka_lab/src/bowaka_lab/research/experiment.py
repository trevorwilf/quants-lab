"""High-level Experiment orchestrator for splits + studies + reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

import pandas as pd

from bowaka_lab.research.robustness import topk_convergence, parameter_sensitivity
from bowaka_lab.research.splits import WalkForwardPlan, WalkForwardSplitter
from bowaka_lab.research.walkforward import WalkForwardSummary, run_walkforward


@dataclass
class ExperimentResult:
    walk_forward: WalkForwardSummary
    trial_scores: pd.DataFrame
    sensitivity: pd.DataFrame | None = None
    convergence: dict | None = None
    holdout_score: float | None = None


@dataclass
class Experiment:
    splitter: WalkForwardSplitter
    evaluator: Callable
    param_columns: list[str] = field(default_factory=list)

    def run(
        self,
        *,
        start: date,
        end: date,
        trial_scores: pd.DataFrame | None = None,
        holdout_evaluator: Callable | None = None,
    ) -> ExperimentResult:
        plan = self.splitter.plan(start, end)
        summary = run_walkforward(plan=plan, evaluate_fn=self.evaluator)
        trials = trial_scores if trial_scores is not None else pd.DataFrame()
        convergence = topk_convergence(trials, k=10) if not trials.empty else None
        sensitivity = (
            parameter_sensitivity(trials, param_columns=self.param_columns) if (not trials.empty and self.param_columns) else None
        )
        holdout_score = None
        if holdout_evaluator is not None:
            holdout_score = float(holdout_evaluator(plan))
        return ExperimentResult(
            walk_forward=summary,
            trial_scores=trials,
            sensitivity=sensitivity,
            convergence=convergence,
            holdout_score=holdout_score,
        )
