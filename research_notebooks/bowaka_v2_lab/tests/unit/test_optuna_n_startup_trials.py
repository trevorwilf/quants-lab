"""optuna.n_startup_trials parses, validates, and reaches the TPE sampler.

Realism Phase 1, Task D, audit P0-013. ``n_startup_trials`` is the number of
random-sampling trials before TPE-guided search begins; it must be in
``[0, n_trials]`` and must actually configure ``TPESampler``.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from bowaka_v2_lab.config.models import OptunaConfig
from bowaka_v2_lab.optuna.dispatcher import OptunaStudy


def test_n_startup_trials_parses() -> None:
    cfg = OptunaConfig(n_trials=500, n_startup_trials=100)
    assert cfg.n_startup_trials == 100


def test_n_startup_trials_default_is_none() -> None:
    """Unset -> None (sampler default applies)."""
    cfg = OptunaConfig(n_trials=50)
    assert cfg.n_startup_trials is None


def test_n_startup_trials_rejects_above_n_trials() -> None:
    with pytest.raises(ValidationError):
        OptunaConfig(n_trials=50, n_startup_trials=51)


def test_n_startup_trials_rejects_negative() -> None:
    with pytest.raises(ValidationError):
        OptunaConfig(n_trials=50, n_startup_trials=-1)


def test_n_startup_trials_accepts_boundary_values() -> None:
    assert OptunaConfig(n_trials=50, n_startup_trials=0).n_startup_trials == 0
    assert OptunaConfig(n_trials=50, n_startup_trials=50).n_startup_trials == 50


def test_n_startup_trials_reaches_tpe_sampler() -> None:
    """The configured count must reach optuna.samplers.TPESampler."""
    study = OptunaStudy(
        feed="sip",
        cost_stress="conservative",
        dataset_hash="d" * 16,
        config_hash="c" * 16,
        n_startup_trials=7,
    )
    study.create()
    assert study.study is not None
    assert study.study.sampler._n_startup_trials == 7
