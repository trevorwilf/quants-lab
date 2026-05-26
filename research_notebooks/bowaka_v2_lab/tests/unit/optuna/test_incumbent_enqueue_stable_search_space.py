"""Incumbent enqueue keeps Optuna's resolved search-space distributions stable.

Speedup report §4 P0-B / §5.2 / Phase 0 task 5. The deprecated
``_suggest_incumbent_params`` collapsed each search-space entry to a
near-singleton dynamic distribution for trial 0 only — every later trial
reverted to the full bounds. Optuna 3.x records the per-trial distribution on
the trial and asserts on subsequent ``suggest_*`` calls that the distribution
matches; the dynamic-range trick triggered "CategoricalDistribution does not
support dynamic value space" and "FloatDistribution does not match the previous
trial" errors that put every non-incumbent trial into the FAILED state.

The enqueue path delivers the incumbent value to Optuna without modifying the
resolved distribution — trial 0's ``suggest_*`` calls return the enqueued
values, and trial 1+'s calls sample from the SAME ``(lo, hi)`` / choices.
"""
from __future__ import annotations

import logging

import optuna
import pytest

from bowaka_v2_lab.optuna.search_space import (
    SEARCH_SPACE_SPEC,
    TIME_STOP_EXIT_TIME_CHOICES,
    suggest_params,
)
from bowaka_v2_lab.optuna.walkforward_runner import _enqueue_incumbent_trial


def _full_incumbent_params() -> dict:
    """A complete incumbent params dict — one entry for every search-space key."""
    params: dict = {}
    for name, entry in SEARCH_SPACE_SPEC.items():
        kind = entry[0]
        if kind == "uniform":
            lo, hi = float(entry[1]), float(entry[2])
            params[name] = (lo + hi) / 2.0
        elif kind == "log_uniform":
            lo, hi = float(entry[1]), float(entry[2])
            # Geometric midpoint, safe for positive ranges.
            params[name] = (lo * hi) ** 0.5
        elif kind == "int":
            lo, hi = int(entry[1]), int(entry[2])
            params[name] = (lo + hi) // 2
        elif kind == "categorical":
            params[name] = entry[1][0]
        else:  # pragma: no cover — defensive
            params[name] = entry[1]
    # Pin the time-stop choice explicitly for the test's last assertion.
    if "exits.time_stop.exit_time" in params:
        params["exits.time_stop.exit_time"] = "15:45"
    return params


def test_incumbent_enqueue_does_not_warn_about_dynamic_distributions(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """3 trials of the same objective with an enqueued incumbent: no FAIL, no
    'dynamic value space' warning.
    """
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=1337, n_startup_trials=2),
    )
    incumbent = _full_incumbent_params()
    clamped = _enqueue_incumbent_trial(study, incumbent, search_space_overrides=None)
    assert clamped == {}, (
        "the midpoint incumbent is in-bounds for every search-space entry; got "
        f"unexpected clamps: {clamped}"
    )

    def obj(t: optuna.Trial) -> float:
        suggest_params(t, overrides=None)
        return 0.0

    caplog.set_level(logging.WARNING, logger="optuna")
    study.optimize(obj, n_trials=3)

    # No FAIL state on any trial.
    for t in study.trials:
        assert t.state == optuna.trial.TrialState.COMPLETE, (
            f"trial {t.number} not COMPLETE: state={t.state.name}"
        )

    # No 'dynamic value space' / 'does not match' messages from Optuna.
    for record in caplog.records:
        msg = record.getMessage()
        assert "dynamic value space" not in msg, (
            f"unexpected Optuna dynamic-distribution warning: {msg}"
        )
        assert "does not match the previous trial" not in msg, (
            f"unexpected Optuna distribution-mismatch warning: {msg}"
        )

    # Trial 0 carries the incumbent flag + values; later trials sample freely.
    assert study.trials[0].user_attrs.get("incumbent_trial") is True
    assert study.trials[0].params["exits.time_stop.exit_time"] == "15:45"
    for t in study.trials[1:]:
        # Later trials may sample any value in the categorical choice list.
        assert t.params["exits.time_stop.exit_time"] in TIME_STOP_EXIT_TIME_CHOICES
