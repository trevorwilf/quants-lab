"""Tests for Optuna failure telemetry wrapper."""

import optuna
import pytest

from pmm_lab.optuna.study import run_optimization


def test_failed_trial_records_exception_info():
    """Failed trials should have failure_type and failure_message user attrs."""
    def bad_objective(trial):
        trial.suggest_int("x", 0, 10)
        raise ValueError("intentional test failure")

    study = optuna.create_study()
    run_optimization(study, bad_objective, n_trials=3)

    failed = [t for t in study.trials if t.state == optuna.trial.TrialState.FAIL]
    assert len(failed) == 3
    for t in failed:
        assert t.user_attrs.get("failure_type") == "ValueError"
        assert "intentional test failure" in t.user_attrs.get("failure_message", "")


def test_successful_trials_unaffected():
    """Wrapper is transparent to successful trials."""
    def good_objective(trial):
        x = trial.suggest_float("x", -10, 10)
        return x ** 2

    study = optuna.create_study()
    run_optimization(study, good_objective, n_trials=5)

    completed = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    assert len(completed) == 5
    for t in completed:
        assert "failure_type" not in t.user_attrs
        assert "failure_message" not in t.user_attrs
