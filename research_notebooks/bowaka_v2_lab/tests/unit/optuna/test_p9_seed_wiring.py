"""P9 L16 — the TPE sampler seed is configurable (was hard-coded 1337).

run.seed now threads into OptunaStudy.sampler_seed, so a study's exploration is
reproducible per seed and distinct across seeds (rather than always 1337).
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.dispatcher import OptunaStudy


def _first_random_suggestion(seed: int, tag: str) -> float:
    # Distinct dataset_hash -> distinct study name (no in-memory collision); the
    # TPE sampler seed drives the first (startup = random) suggestion.
    study = OptunaStudy(
        feed="iex", cost_stress="base", dataset_hash=f"d{tag}", config_hash="c",
        n_startup_trials=10, sampler_seed=seed,
    ).create()
    trial = study.ask()
    return round(trial.suggest_float("x", 0.0, 1.0), 10)


def test_sampler_seed_field_defaults_to_1337() -> None:
    s = OptunaStudy(feed="iex", cost_stress="base", dataset_hash="d", config_hash="c")
    assert s.sampler_seed == 1337  # default preserved when run.seed is unset


def test_sampler_seed_is_reproducible_and_distinct() -> None:
    a1 = _first_random_suggestion(1, "a")
    a1_again = _first_random_suggestion(1, "b")
    a2 = _first_random_suggestion(2, "c")
    assert a1 == a1_again, "same sampler seed must reproduce the same exploration"
    assert a1 != a2, "different sampler seed must change the exploration (was hard-coded 1337)"
