"""One-at-a-time and grouped parameter perturbation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd


@dataclass
class SensitivityResult:
    perturbations: pd.DataFrame  # rows: (param, value, score)
    baseline_score: float


def one_at_a_time(
    *,
    baseline_params: dict[str, Any],
    evaluator: Callable[[dict[str, Any]], float],
    perturbations: dict[str, list[Any]],
) -> SensitivityResult:
    baseline_score = float(evaluator(baseline_params))
    rows: list[dict] = []
    for param, values in perturbations.items():
        for v in values:
            cfg = dict(baseline_params)
            cfg[param] = v
            rows.append({"param": param, "value": v, "score": float(evaluator(cfg))})
    return SensitivityResult(perturbations=pd.DataFrame(rows), baseline_score=baseline_score)


def grouped(
    *,
    baseline_params: dict[str, Any],
    evaluator: Callable[[dict[str, Any]], float],
    group_perturbations: dict[str, dict[str, Any]],
) -> SensitivityResult:
    baseline_score = float(evaluator(baseline_params))
    rows: list[dict] = []
    for group_name, group_cfg in group_perturbations.items():
        cfg = dict(baseline_params)
        cfg.update(group_cfg)
        rows.append({"param": "group", "value": group_name, "score": float(evaluator(cfg))})
    return SensitivityResult(perturbations=pd.DataFrame(rows), baseline_score=baseline_score)
