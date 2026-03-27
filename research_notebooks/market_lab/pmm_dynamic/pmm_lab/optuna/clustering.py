"""
Top-k trial parameter clustering analysis.

Checks whether the best trials converge to similar parameter regions
or scatter across the search space. Clustered top-k = robust signal.
Scattered top-k = likely overfit to noise.

Usage (post-optimization):
    report = analyze_top_k(study, k=10)
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Parameters to include in clustering analysis (continuous only)
CLUSTER_PARAMS = [
    "buy_spread_base", "buy_spread_ratio",
    "sell_spread_base", "sell_spread_ratio",
    "buy_side_weight", "amount_skew",
    "stop_loss", "take_profit",
    "executor_refresh_time", "cooldown_time",
    "total_amount_quote",
]


@dataclass
class ClusteringReport:
    """Result of top-k clustering analysis."""
    k: int
    param_cv: Dict[str, float]         # coefficient of variation per param (std/mean)
    mean_cv: float                      # average CV across all params
    max_cv: float                       # worst (highest) CV
    clustered_params: List[str]         # params with CV < threshold
    scattered_params: List[str]         # params with CV >= threshold
    is_clustered: bool                  # True if mean_cv < threshold
    param_ranges: Dict[str, Dict[str, float]]  # param -> {min, max, mean, std}


def analyze_top_k(
    study,
    k: int = 10,
    cv_threshold: float = 0.50,
    cluster_params: Optional[List[str]] = None,
) -> ClusteringReport:
    """Analyze parameter clustering among the top-k trials.

    Parameters
    ----------
    study : optuna.Study
        Completed study.
    k : int
        Number of top trials to analyze.
    cv_threshold : float
        Coefficient of variation threshold. CV < threshold = clustered.
    cluster_params : List[str], optional
        Which params to analyze. If None, uses CLUSTER_PARAMS.

    Returns
    -------
    ClusteringReport
    """
    import optuna

    if cluster_params is None:
        cluster_params = CLUSTER_PARAMS

    # Get top-k completed trials by value
    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    completed.sort(key=lambda t: t.value if t.value is not None else float('-inf'), reverse=True)
    top_k = completed[:k]

    if len(top_k) < 2:
        return ClusteringReport(
            k=len(top_k), param_cv={}, mean_cv=1.0, max_cv=1.0,
            clustered_params=[], scattered_params=list(cluster_params),
            is_clustered=False, param_ranges={},
        )

    # Extract parameter values
    param_cv = {}
    param_ranges = {}
    clustered = []
    scattered = []

    for param_name in cluster_params:
        values = []
        for trial in top_k:
            if param_name in trial.params:
                values.append(float(trial.params[param_name]))

        if len(values) < 2:
            continue

        arr = np.array(values)
        mean = float(np.mean(arr))
        std = float(np.std(arr, ddof=1))
        cv = std / abs(mean) if abs(mean) > 1e-10 else float('inf')

        param_cv[param_name] = cv
        param_ranges[param_name] = {
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "mean": mean,
            "std": std,
        }

        if cv < cv_threshold:
            clustered.append(param_name)
        else:
            scattered.append(param_name)

    # Aggregate
    cv_values = list(param_cv.values())
    mean_cv = float(np.mean(cv_values)) if cv_values else 1.0
    max_cv = float(np.max(cv_values)) if cv_values else 1.0

    return ClusteringReport(
        k=len(top_k),
        param_cv=param_cv,
        mean_cv=mean_cv,
        max_cv=max_cv,
        clustered_params=clustered,
        scattered_params=scattered,
        is_clustered=mean_cv < cv_threshold,
        param_ranges=param_ranges,
    )
