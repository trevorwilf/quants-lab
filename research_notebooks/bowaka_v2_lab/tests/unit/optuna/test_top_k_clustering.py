"""Phase 5 — top-K cluster stability section."""
from __future__ import annotations

from bowaka_v2_lab.optuna.evaluate_finalists import _build_top_k_clustering


def _row(trial_number, params, incumbent=False):
    return {"trial_number": trial_number, "is_incumbent": incumbent, "params": params}


def test_tight_cluster_all_stable() -> None:
    rows = [
        _row(1, {"a": 1.00, "b": 10.0}),
        _row(2, {"a": 1.01, "b": 10.1}),
        _row(3, {"a": 0.99, "b": 9.9}),
    ]
    out = _build_top_k_clustering(rows, cv_threshold=0.15)
    assert set(out["stable_params"]) == {"a", "b"}
    assert out["unstable_params"] == []
    assert out["unstable_fraction"] == 0.0


def test_one_param_wildly_varying_is_unstable() -> None:
    rows = [
        _row(1, {"a": 1.0, "b": 1.0}),
        _row(2, {"a": 1.0, "b": 50.0}),
        _row(3, {"a": 1.0, "b": -40.0}),
    ]
    out = _build_top_k_clustering(rows, cv_threshold=0.15)
    assert "b" in out["unstable_params"]
    assert "a" in out["stable_params"]
    assert out["unstable_fraction"] > 0.0
    # b should be the top drifting param.
    assert out["top_drifting"][0]["param"] == "b"


def test_incumbent_excluded_from_clustering() -> None:
    rows = [
        _row(1, {"a": 1.0}),
        _row(2, {"a": 1.0}),
        _row(0, {"a": 100.0}, incumbent=True),  # incumbent outlier ignored
    ]
    out = _build_top_k_clustering(rows, cv_threshold=0.15)
    assert out["n_finalists"] == 2
    assert out["unstable_fraction"] == 0.0
