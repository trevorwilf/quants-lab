"""Tests for pmm_lab.optuna.clustering — top-k parameter clustering analysis."""

import optuna
import pytest

from pmm_lab.optuna.clustering import analyze_top_k, ClusteringReport, CLUSTER_PARAMS


def _make_mock_study(param_sets, scores):
    """Create an in-memory study with manually added trials."""
    study = optuna.create_study(direction="maximize")
    for params, score in zip(param_sets, scores):
        # Build distributions that contain the actual param values
        distributions = {}
        for k, v in params.items():
            lo = min(0.0, v - abs(v) - 1.0)
            hi = max(v + abs(v) + 1.0, 100.0)
            distributions[k] = optuna.distributions.FloatDistribution(lo, hi)
        study.add_trial(
            optuna.trial.create_trial(
                params=params,
                values=[score],
                distributions=distributions,
                state=optuna.trial.TrialState.COMPLETE,
            )
        )
    return study


def _make_tight_params(base_val=1.0, noise=0.01):
    """Generate clustered params with small noise."""
    import random
    return {
        "buy_spread_base": base_val + random.uniform(-noise, noise),
        "buy_spread_ratio": 2.0 + random.uniform(-noise, noise),
        "sell_spread_base": base_val + random.uniform(-noise, noise),
        "sell_spread_ratio": 2.0 + random.uniform(-noise, noise),
        "buy_side_weight": 0.5 + random.uniform(-noise, noise),
        "amount_skew": 1.0 + random.uniform(-noise, noise),
        "stop_loss": 0.03 + random.uniform(-noise, noise),
        "take_profit": 0.015 + random.uniform(-noise, noise),
        "executor_refresh_time": 3000.0 + random.uniform(-10, 10),
        "cooldown_time": 3000.0 + random.uniform(-10, 10),
        "total_amount_quote": 100.0 + random.uniform(-1, 1),
    }


def _make_scattered_params():
    """Generate widely scattered params."""
    import random
    return {
        "buy_spread_base": random.uniform(0.01, 50.0),
        "buy_spread_ratio": random.uniform(0.5, 20.0),
        "sell_spread_base": random.uniform(0.01, 50.0),
        "sell_spread_ratio": random.uniform(0.5, 20.0),
        "buy_side_weight": random.uniform(0.01, 5.0),
        "amount_skew": random.uniform(0.01, 20.0),
        "stop_loss": random.uniform(0.001, 1.0),
        "take_profit": random.uniform(0.001, 1.0),
        "executor_refresh_time": random.uniform(10, 50000),
        "cooldown_time": random.uniform(10, 50000),
        "total_amount_quote": random.uniform(10, 1000),
    }


class TestClusteredTrialsLowCv:
    def test_clustered_trials_low_cv(self):
        import random
        random.seed(42)
        param_sets = [_make_tight_params() for _ in range(10)]
        scores = [10.0 - i * 0.1 for i in range(10)]
        study = _make_mock_study(param_sets, scores)
        report = analyze_top_k(study, k=10)
        assert report.is_clustered
        assert report.mean_cv < 0.5


class TestScatteredTrialsHighCv:
    def test_scattered_trials_high_cv(self):
        import random
        random.seed(42)
        param_sets = [_make_scattered_params() for _ in range(10)]
        scores = [10.0 - i * 0.1 for i in range(10)]
        study = _make_mock_study(param_sets, scores)
        report = analyze_top_k(study, k=10)
        assert not report.is_clustered
        assert report.mean_cv >= 0.5


class TestClusteringReportHasRanges:
    def test_clustering_report_has_ranges(self):
        import random
        random.seed(42)
        param_sets = [_make_tight_params() for _ in range(10)]
        scores = [10.0 - i * 0.1 for i in range(10)]
        study = _make_mock_study(param_sets, scores)
        report = analyze_top_k(study, k=10)
        assert isinstance(report.param_ranges, dict)
        for param_name in CLUSTER_PARAMS:
            assert param_name in report.param_ranges
            r = report.param_ranges[param_name]
            assert "min" in r and "max" in r and "mean" in r and "std" in r
            assert r["min"] <= r["max"]


class TestInsufficientTrials:
    def test_insufficient_trials(self):
        param_sets = [{"buy_spread_base": 1.0}]
        scores = [5.0]
        study = _make_mock_study(param_sets, scores)
        report = analyze_top_k(study, k=10)
        assert not report.is_clustered
        assert report.k == 1


class TestCustomClusterParams:
    def test_custom_cluster_params(self):
        import random
        random.seed(42)
        param_sets = [_make_tight_params() for _ in range(5)]
        scores = [10.0 - i for i in range(5)]
        study = _make_mock_study(param_sets, scores)
        custom = ["buy_spread_base", "stop_loss"]
        report = analyze_top_k(study, k=5, cluster_params=custom)
        assert set(report.param_cv.keys()) == set(custom)
