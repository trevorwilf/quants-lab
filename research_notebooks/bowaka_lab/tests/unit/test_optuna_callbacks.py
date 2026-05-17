"""Phase optuna-1: callback behavior."""

from __future__ import annotations

import logging

import optuna
import pytest

from bowaka_lab.optuna.callbacks import (
    DegeneracyCheckCallback,
    TqdmProgressCallback,
    TrialLoggingCallback,
)


def _study(tmp_path, name: str) -> optuna.Study:
    return optuna.create_study(
        study_name=name,
        storage=f"sqlite:///{tmp_path}/{name}.db",
        direction="maximize",
        load_if_exists=False,
    )


def test_degeneracy_callback_warns_when_too_few_distinct_values(tmp_path, caplog):
    cb = DegeneracyCheckCallback(check_after_n_trials=5, min_distinct_values=10)
    study = _study(tmp_path, "deg_warn")

    def constant(trial):
        trial.suggest_float("x", 0, 1)
        return 0.42

    with caplog.at_level(logging.WARNING, logger="bowaka_lab.optuna.callbacks"):
        study.optimize(constant, n_trials=6, callbacks=[cb])
    assert any("DEGENERACY WARNING" in rec.message for rec in caplog.records)


def test_degeneracy_callback_silent_when_enough_distinct_values(tmp_path, caplog):
    cb = DegeneracyCheckCallback(check_after_n_trials=5, min_distinct_values=3)
    study = _study(tmp_path, "deg_silent")

    def varied(trial):
        x = trial.suggest_float("x", 0, 1)
        return x

    with caplog.at_level(logging.WARNING, logger="bowaka_lab.optuna.callbacks"):
        study.optimize(varied, n_trials=6, callbacks=[cb])
    assert not any("DEGENERACY WARNING" in rec.message for rec in caplog.records)


def test_degeneracy_callback_only_checks_once(tmp_path, caplog):
    cb = DegeneracyCheckCallback(check_after_n_trials=2, min_distinct_values=10)
    study = _study(tmp_path, "deg_once")
    study.optimize(lambda t: (t.suggest_float("x", 0, 1), 0.42)[1], n_trials=10, callbacks=[cb])
    warns = [r for r in caplog.records if "DEGENERACY WARNING" in r.message]
    assert len(warns) <= 1


def test_trial_logging_callback_emits_log_at_interval(tmp_path, caplog):
    cb = TrialLoggingCallback(log_every=2)
    study = _study(tmp_path, "trial_log")
    with caplog.at_level(logging.INFO, logger="bowaka_lab.optuna.callbacks"):
        study.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=5, callbacks=[cb])
    log_lines = [r.message for r in caplog.records if "Trial " in r.message]
    assert log_lines, "expected at least one trial log line"


def test_tqdm_progress_callback_advances_bar(tmp_path):
    class _Bar:
        def __init__(self):
            self.n = 0
            self.postfix = None

        def update(self, k):
            self.n += k

        def set_postfix_str(self, s):
            self.postfix = s

    bar = _Bar()
    cb = TqdmProgressCallback(bar)
    study = _study(tmp_path, "tqdm_advance")
    study.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=4, callbacks=[cb])
    assert bar.n == 4


def test_tqdm_progress_callback_show_best_updates_postfix(tmp_path):
    class _Bar:
        def __init__(self):
            self.n = 0
            self.postfix = None

        def update(self, k):
            self.n += k

        def set_postfix_str(self, s):
            self.postfix = s

    bar = _Bar()
    cb = TqdmProgressCallback(bar, show_best=True)
    study = _study(tmp_path, "tqdm_best")
    study.optimize(lambda t: t.suggest_float("x", 0, 1), n_trials=4, callbacks=[cb])
    assert bar.postfix and "best=" in bar.postfix
