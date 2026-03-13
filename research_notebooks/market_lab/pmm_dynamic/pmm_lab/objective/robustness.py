"""
Robust aggregation of scores across folds and stress scenarios.
"""

import numpy as np
from typing import List

from pmm_lab.objective.objective import REJECT_SCORE


def robust_aggregate(
    scores: List[float],
    lambda_mad: float = 0.5,
    min_valid_fraction: float = 0.5,
) -> float:
    """Compute a robust aggregate score.

    Formula: robust_score = median(scores) - lambda_mad * MAD(scores)
    Where MAD = median(|scores - median(scores)|)

    If more than (1 - min_valid_fraction) of folds are REJECT_SCORE,
    the entire result is rejected. This prevents a single lucky fold
    from producing a misleadingly positive aggregate.

    Parameters
    ----------
    scores : List[float]
        Objective scores from individual folds or scenarios.
    lambda_mad : float
        Penalty weight for variability. Default 0.5.
    min_valid_fraction : float
        Minimum fraction of scores that must be non-rejected.
        Default 0.5 — at least half the folds must produce real results.

    Returns
    -------
    float
        Robust aggregate score.
        Returns REJECT_SCORE if scores is empty, all REJECT_SCORE,
        or too few valid scores.
    """
    if not scores:
        return REJECT_SCORE

    arr = np.array(scores, dtype="float64")
    valid = arr[arr != REJECT_SCORE]

    if len(valid) == 0:
        return REJECT_SCORE

    # Reject if too many folds failed
    valid_fraction = len(valid) / len(arr)
    if valid_fraction < min_valid_fraction:
        return REJECT_SCORE

    median_val = float(np.median(valid))
    mad = float(np.median(np.abs(valid - median_val)))

    return median_val - lambda_mad * mad
