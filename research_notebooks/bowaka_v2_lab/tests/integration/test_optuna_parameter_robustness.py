"""The best-trial report includes parameter-neighbourhood robustness (Task 5).

Realism remediation Phase 9. A single high objective value is not enough — if
the score collapses for parameter sets just next to the best one, the result is
a fragile spike, not a tradeable plateau. The study re-scores 5 neighbours
around the best params and records their scores, plus fold-by-fold metrics and a
stability rank.
"""
from __future__ import annotations

import datetime as dt

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.devtools.wf_lake import (
    write_walkforward_test_config as write_test_config,
)
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_best_trial_report_includes_neighbour_scores(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    result = run_walkforward_study(cfg_path, allow_smoke=True)
    assert result["status"] == "ok"

    report = result["best_trial_report"]
    assert report, "best-trial report is empty"

    # --- parameter-neighbourhood robustness ---
    robustness = report["robustness"]
    assert robustness["n_neighbours"] == 5
    assert len(robustness["neighbour_scores"]) == 5
    assert len(robustness["neighbours"]) == 5
    for neigh in robustness["neighbours"]:
        assert "params" in neigh and "score" in neigh
        assert isinstance(neigh["params"], dict) and neigh["params"]

    # --- fold-by-fold metrics for the best trial ---
    fbf = report["fold_by_fold"]
    assert "fold_scores" in fbf
    assert "fold_metrics" in fbf
    assert "penalty_breakdown" in fbf

    # --- stability rank (fold-metric variance) ---
    stability = report["stability"]
    assert "fold_score_variance" in stability
    assert "n_folds" in stability


def test_best_trial_report_present_in_persisted_results(tmp_path, lab_root):
    import json
    from pathlib import Path

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf2.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    result = run_walkforward_study(cfg_path, allow_smoke=True)
    persisted = json.loads(Path(result["results_path"]).read_text(encoding="utf-8"))
    assert "best_trial_report" in persisted
    assert "top_k_clustering" in persisted
    assert persisted["best_trial_report"]["robustness"]["n_neighbours"] == 5
