"""``_enqueue_incumbent_trial`` clamps numerics, REFUSES categoricals.

Speedup report §5.2 / Phase 0 task 5/6. Numeric out-of-bounds values are
clamped into ``[lo, hi]`` with the clamp recorded for the operator. A
categorical value not in the choice list is an explicit operator error
(silently mapping to choices[0] would mislead): the helper raises
:class:`OptunaStudyInvalidError` so the operator widens the search space or
fixes the incumbent contract before tuning. A missing required key fails the
same way.
"""
from __future__ import annotations

import optuna
import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_SPEC
from bowaka_v2_lab.optuna.walkforward_runner import _enqueue_incumbent_trial


def _midpoint_incumbent() -> dict:
    """A complete incumbent — every value is the search-space midpoint (in-bounds)."""
    out: dict = {}
    for name, entry in SEARCH_SPACE_SPEC.items():
        kind = entry[0]
        if kind == "uniform":
            out[name] = (float(entry[1]) + float(entry[2])) / 2.0
        elif kind == "log_uniform":
            out[name] = (float(entry[1]) * float(entry[2])) ** 0.5
        elif kind == "int":
            out[name] = (int(entry[1]) + int(entry[2])) // 2
        elif kind == "categorical":
            out[name] = entry[1][0]
        else:  # pragma: no cover — defensive
            out[name] = entry[1]
    return out


def _new_study() -> optuna.Study:
    return optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=1337, n_startup_trials=2),
    )


def test_float_below_lower_bound_is_clamped() -> None:
    study = _new_study()
    incumbent = _midpoint_incumbent()
    assert "signals.rvol_so_far_min" in SEARCH_SPACE_SPEC, (
        "test relies on the live search-space spec — update the test if the key changed"
    )
    entry = SEARCH_SPACE_SPEC["signals.rvol_so_far_min"]
    lo, hi = float(entry[1]), float(entry[2])
    incumbent["signals.rvol_so_far_min"] = lo - 10.0
    clamped = _enqueue_incumbent_trial(study, incumbent, search_space_overrides=None)
    assert "signals.rvol_so_far_min" in clamped
    rec = clamped["signals.rvol_so_far_min"]
    assert rec["clamped"] == lo
    assert rec["range"] == [lo, hi]
    assert rec["target"] == lo - 10.0


def test_categorical_not_in_choices_raises_without_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refuse silent clamping on categoricals; ``enqueue_trial`` must not be called."""
    study = _new_study()
    incumbent = _midpoint_incumbent()
    incumbent["exits.time_stop.exit_time"] = "16:30"  # not in TIME_STOP_EXIT_TIME_CHOICES

    def _must_not_be_called(*args, **kwargs):
        pytest.fail("study.enqueue_trial must not be called on a refused incumbent")

    monkeypatch.setattr(study, "enqueue_trial", _must_not_be_called)

    with pytest.raises(OptunaStudyInvalidError) as info:
        _enqueue_incumbent_trial(study, incumbent, search_space_overrides=None)
    assert "exits.time_stop.exit_time" in str(info.value)
    assert "16:30" in str(info.value)


def test_missing_required_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An incumbent missing any required search-space key is rejected."""
    study = _new_study()
    incumbent = _midpoint_incumbent()
    missing_key = "signals.rvol_so_far_min"
    assert missing_key in SEARCH_SPACE_SPEC, "test relies on a live search-space key"
    incumbent.pop(missing_key)

    def _must_not_be_called(*args, **kwargs):
        pytest.fail("study.enqueue_trial must not be called on a refused incumbent")

    monkeypatch.setattr(study, "enqueue_trial", _must_not_be_called)

    with pytest.raises(OptunaStudyInvalidError) as info:
        _enqueue_incumbent_trial(study, incumbent, search_space_overrides=None)
    assert missing_key in str(info.value)


def test_in_bounds_incumbent_records_no_clamps() -> None:
    study = _new_study()
    incumbent = _midpoint_incumbent()
    clamped = _enqueue_incumbent_trial(study, incumbent, search_space_overrides=None)
    assert clamped == {}
