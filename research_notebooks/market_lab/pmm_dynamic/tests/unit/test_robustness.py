"""Tests for pmm_lab.objective.robustness — robust aggregation."""

import pytest
from pmm_lab.objective.robustness import robust_aggregate
from pmm_lab.objective.objective import REJECT_SCORE


class TestRobustAggregate:
    def test_constant_scores(self):
        """All scores identical → robust_aggregate == that score (MAD = 0)."""
        scores = [5.0, 5.0, 5.0, 5.0]
        result = robust_aggregate(scores)
        assert abs(result - 5.0) < 1e-9

    def test_variable_scores_penalized(self):
        """Scores = [10, 8, 6, -5]. Median = 7, MAD > 0. Assert robust_aggregate < median."""
        scores = [10.0, 8.0, 6.0, -5.0]
        result = robust_aggregate(scores)
        import numpy as np
        median_val = float(np.median(scores))
        assert result < median_val

    def test_all_reject_scores(self):
        """All scores = REJECT_SCORE. Assert result == REJECT_SCORE."""
        scores = [REJECT_SCORE, REJECT_SCORE, REJECT_SCORE]
        result = robust_aggregate(scores)
        assert result == REJECT_SCORE

    def test_empty_scores(self):
        """Empty list → REJECT_SCORE."""
        result = robust_aggregate([])
        assert result == REJECT_SCORE

    def test_lambda_zero_equals_median(self):
        """With lambda_mad=0, robust_aggregate == median(scores)."""
        import numpy as np
        scores = [1.0, 3.0, 5.0, 7.0, 9.0]
        result = robust_aggregate(scores, lambda_mad=0.0)
        assert abs(result - float(np.median(scores))) < 1e-9

    def test_higher_lambda_more_penalty(self):
        """Same scores, lambda=0.5 vs lambda=1.0. lambda=1.0 produces lower aggregate."""
        scores = [10.0, 8.0, 12.0, 6.0]
        result_05 = robust_aggregate(scores, lambda_mad=0.5)
        result_10 = robust_aggregate(scores, lambda_mad=1.0)
        assert result_10 < result_05
