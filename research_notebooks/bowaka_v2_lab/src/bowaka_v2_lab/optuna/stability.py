"""Parameter-stability + perturbation report."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping

import math
import statistics


def top_k_cluster_stability(
    top_k_params: list[Mapping[str, float]],
    *,
    relative_spread_threshold: float = 0.20,
) -> dict[str, bool | float]:
    """Decide whether the top-k parameter sets cluster.

    For each numeric parameter, computes the coefficient of variation (std / |mean|).
    Returns ``stable=True`` iff every parameter has CV <= ``relative_spread_threshold``.
    """
    if len(top_k_params) < 2:
        return {"stable": True, "max_cv": 0.0, "param_cvs": {}}
    by_param: dict[str, list[float]] = defaultdict(list)
    for params in top_k_params:
        for k, v in params.items():
            try:
                by_param[k].append(float(v))
            except (TypeError, ValueError):
                continue
    cvs: dict[str, float] = {}
    for k, vals in by_param.items():
        if len(vals) < 2:
            continue
        m = statistics.mean(vals)
        s = statistics.stdev(vals)
        cv = (s / abs(m)) if abs(m) > 1e-12 else (0.0 if s == 0.0 else math.inf)
        cvs[k] = cv
    max_cv = max(cvs.values(), default=0.0)
    return {"stable": max_cv <= relative_spread_threshold, "max_cv": max_cv, "param_cvs": cvs}
