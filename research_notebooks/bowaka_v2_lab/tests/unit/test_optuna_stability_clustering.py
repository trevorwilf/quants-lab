"""Top trials clustered → stable=True; scattered → stable=False."""
from __future__ import annotations

from bowaka_v2_lab.optuna.stability import top_k_cluster_stability


def test_clustered_params_stable() -> None:
    top = [{"a": 1.0, "b": 5.0}, {"a": 1.05, "b": 5.10}, {"a": 0.98, "b": 4.95}]
    out = top_k_cluster_stability(top, relative_spread_threshold=0.20)
    assert out["stable"] is True


def test_scattered_params_unstable() -> None:
    top = [{"a": 1.0, "b": 5.0}, {"a": 5.0, "b": 0.5}, {"a": 0.1, "b": 50.0}]
    out = top_k_cluster_stability(top, relative_spread_threshold=0.20)
    assert out["stable"] is False
    assert out["max_cv"] > 0.20


def test_single_trial_is_trivially_stable() -> None:
    out = top_k_cluster_stability([{"a": 1.0}])
    assert out["stable"] is True
