"""
Robust aggregation of scores across folds and stress scenarios.
"""

import numpy as np
from typing import List, Optional

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


def robust_aggregate_v2(
    fold_scores: List[float],
    fold_stress_scores: Optional[List[List[float]]] = None,
    lambda_mad: float = 0.5,
    stress_weight: float = 0.4,
    stress_percentile: float = 20.0,
    sensitivity_penalty: float = 0.0,
    sensitivity_weight: float = 0.2,
    min_valid_fraction: float = 0.5,
) -> float:
    """Robust aggregation v2 with fold-local stress and sensitivity penalty.

    Formula:
      J_fold(f) = (1 - stress_weight) * baseline_score(f)
                + stress_weight * q20(stress_scores(f))

      J_opt = median(J_fold) - lambda_mad * MAD(J_fold) - sensitivity_weight * sensitivity_penalty

    Parameters
    ----------
    fold_scores : List[float]
        Baseline objective score per fold.
    fold_stress_scores : List[List[float]], optional
        Per-fold stress scores. fold_stress_scores[f] = list of scenario scores for fold f.
        If None, only baseline scores are used.
    lambda_mad : float
        MAD penalty weight.
    stress_weight : float
        Weight of stress component in fold score (0.4 = 40% stress, 60% baseline).
    stress_percentile : float
        Percentile of stress scores to use (20 = pessimistic 20th percentile).
    sensitivity_penalty : float
        Pre-computed sensitivity penalty (0 = stable, 1 = fragile).
    sensitivity_weight : float
        How much to penalize sensitivity.
    min_valid_fraction : float
        Minimum fraction of non-rejected folds.

    Returns
    -------
    float
        Robust aggregate score.
    """
    if not fold_scores:
        return REJECT_SCORE

    arr = np.array(fold_scores, dtype="float64")
    valid_mask = arr != REJECT_SCORE
    valid = arr[valid_mask]

    if len(valid) == 0 or len(valid) / len(arr) < min_valid_fraction:
        return REJECT_SCORE

    # Compute per-fold combined scores
    combined_fold_scores = []
    for i, score in enumerate(fold_scores):
        if score == REJECT_SCORE:
            combined_fold_scores.append(REJECT_SCORE)
            continue

        if fold_stress_scores is not None and i < len(fold_stress_scores):
            stress = fold_stress_scores[i]
            valid_stress = [s for s in stress if s != REJECT_SCORE]
            if valid_stress:
                stress_q = float(np.percentile(valid_stress, stress_percentile))
                fold_combined = (1.0 - stress_weight) * score + stress_weight * stress_q
            else:
                fold_combined = score
        else:
            fold_combined = score

        combined_fold_scores.append(fold_combined)

    # Filter valid combined scores
    combined_arr = np.array(combined_fold_scores, dtype="float64")
    combined_valid = combined_arr[combined_arr != REJECT_SCORE]

    if len(combined_valid) == 0:
        return REJECT_SCORE

    median_val = float(np.median(combined_valid))
    mad = float(np.median(np.abs(combined_valid - median_val)))

    result = median_val - lambda_mad * mad - sensitivity_weight * sensitivity_penalty

    return result
