"""Phase 10 expanded robustness — top-K + sensitivity + stress + holdout guard.

Speedup report §9 / Phase 10.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from bowaka_v2_lab.optuna.robustness import (
    SensitivityResult,
    StressMatrixResult,
    TopKReplayResult,
    assert_holdout_not_rescored,
    param_sensitivity_for_candidate,
    replay_top_k_candidates,
    stress_matrix_for_candidate,
)


# ---- top-K replays --------------------------------------------------------


def test_replay_top_k_writes_summary(tmp_path):
    trials = [
        MagicMock(number=i, value=v, params={"signals.gap": 0.05 + i * 0.01})
        for i, v in enumerate([0.7, 0.9, 0.5, 0.3])
    ]
    scored: dict[int, float] = {}

    def score(params: dict) -> tuple[float, list]:
        # Higher param value → higher score in this stub.
        v = float(params["signals.gap"])
        scored[id(params)] = v
        return v, []

    out = replay_top_k_candidates(
        completed_trials=trials,
        top_k=2,
        score_param_set=score,
        artifact_root=tmp_path,
    )
    assert len(out) == 2
    # Best trial (value=0.9) goes first.
    assert out[0].trial_number == 1
    assert out[1].trial_number == 0
    # Summary file exists with both rows.
    summary = json.loads((tmp_path / "top_k_summary.json").read_text(encoding="utf-8"))
    assert len(summary) == 2
    assert summary[0]["rank"] == 1
    assert summary[1]["rank"] == 2


def test_replay_top_k_default_off_means_no_artifacts(tmp_path):
    trials = [MagicMock(number=0, value=0.5, params={"x": 1.0})]

    def score(params: dict) -> tuple[float, list]:
        return 0.5, []

    out = replay_top_k_candidates(
        completed_trials=trials, top_k=1,
        score_param_set=score, artifact_root=tmp_path,
        write_artifacts=False,
    )
    assert out[0].artifact_dir is None
    assert not (tmp_path / "top_k_summary.json").exists()


def test_replay_top_k_holdout_scorer_optional(tmp_path):
    trials = [MagicMock(number=0, value=0.5, params={"x": 1.0})]
    out = replay_top_k_candidates(
        completed_trials=trials, top_k=1,
        score_param_set=lambda p: (0.5, []),
        final_holdout_scorer=lambda p: 0.42,
        artifact_root=tmp_path,
    )
    assert out[0].holdout_score == 0.42


# ---- param sensitivity ---------------------------------------------------


def test_sensitivity_sweeps_each_tunable_param(tmp_path):
    base_params = {"signals.gap_pct_max": 0.10, "signals.atr_mult": 2.0}
    spec = {
        "signals.gap_pct_max": ("uniform", 0.05, 0.20),
        "signals.atr_mult": ("uniform", 1.0, 4.0),
    }

    def score(params: dict) -> tuple[float, list]:
        # Quadratic around the base: higher delta-from-base, lower score.
        delta = sum(
            (params[k] - base_params[k]) ** 2 for k in base_params
        )
        return -delta, []

    out = param_sensitivity_for_candidate(
        base_params=base_params, search_space=spec,
        score_param_set=score, n_steps=3,
        artifact_dir=tmp_path,
    )
    assert {r.param_name for r in out} == set(spec.keys())
    # Each sweep produced several values (±n_steps within the bounds).
    for r in out:
        assert len(r.sweep_values) > 0
        assert len(r.delta_vs_baseline) == len(r.sweep_values)
    # Artifact written.
    assert (tmp_path / "sensitivity.json").is_file()


def test_sensitivity_skips_non_tuned_keys(tmp_path):
    base = {"signals.gap_pct_max": 0.10}
    spec = {
        "signals.gap_pct_max": ("uniform", 0.05, 0.20),
        "signals.something_else": ("uniform", 0.0, 1.0),  # not in base_params
    }
    out = param_sensitivity_for_candidate(
        base_params=base, search_space=spec,
        score_param_set=lambda p: (0.0, []), n_steps=2,
    )
    names = {r.param_name for r in out}
    assert "signals.gap_pct_max" in names
    assert "signals.something_else" not in names


# ---- stress matrix --------------------------------------------------------


def test_stress_matrix_writes_per_candidate_json(tmp_path):
    base = {
        "execution.max_quote_age_seconds": 60.0,
        "execution.max_spread_bps": 200.0,
    }
    seen: list[dict] = []

    def score_with_overrides(params: dict, overrides: dict) -> float:
        seen.append(overrides)
        return 0.1

    out = stress_matrix_for_candidate(
        candidate_rank=1, base_params=base,
        score_with_overrides=score_with_overrides,
        artifact_dir=tmp_path,
    )
    # Cost-stress axis exercises 3 values.
    assert set(out.cost_stress_scores.keys()) == {"conservative", "base", "aggressive"}
    # Quote-age + spread axes exercise 3 percentages each.
    assert set(out.quote_age_stress_scores.keys()) == {"100pct", "75pct", "50pct"}
    assert set(out.spread_stress_scores.keys()) == {"100pct", "75pct", "50pct"}
    # Delay axis 0/1/2 minutes.
    assert set(out.delay_stress_scores.keys()) == {"0min", "1min", "2min"}
    # Stress-matrix artifact written.
    assert (tmp_path / "stress_matrix.json").is_file()
    # The function fired score_with_overrides 12 times (3+3+3+3).
    assert len(seen) == 12


# ---- holdout rescored guard ----------------------------------------------


def test_holdout_guard_first_score_records_timestamp():
    attrs: dict = {}

    def setter(k, v):
        attrs[k] = v

    out = assert_holdout_not_rescored(study_user_attrs={}, set_user_attr=setter)
    assert out["rescored"] is False
    assert attrs["final_holdout_first_scored_at_utc"] is not None


def test_holdout_guard_second_score_flags_rescored():
    pre = {"final_holdout_first_scored_at_utc": "2025-01-01T00:00:00Z"}
    attrs: dict = {}

    def setter(k, v):
        attrs[k] = v

    out = assert_holdout_not_rescored(study_user_attrs=pre, set_user_attr=setter)
    assert out["rescored"] is True
    assert attrs.get("final_holdout_rescored") is True
    assert attrs.get("final_holdout_last_rescored_at_utc") is not None
