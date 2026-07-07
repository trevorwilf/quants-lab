"""range_ladder search-space tests: ranges, log flags, fixed params."""

import optuna
import pytest
from optuna.distributions import FloatDistribution, IntDistribution

from pmm_lab.optuna.search_space_range_ladder import (
    DEFAULT_FUND_QUOTE,
    PHASE_A_COOLDOWN_SECONDS,
    suggest_range_ladder_params,
)


@pytest.fixture
def sampled():
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=7))
    trial = study.ask()
    params = suggest_range_ladder_params(trial)
    return trial, params


def test_ten_generative_params_sampled(sampled):
    trial, _ = sampled
    assert set(trial.params.keys()) == {
        "n_buy", "n_sell",
        "buy_near_pct", "buy_far_pct", "sell_near_pct", "sell_far_pct",
        "buy_gamma", "sell_gamma", "k_buy", "k_sell",
    }


def test_int_ranges(sampled):
    trial, _ = sampled
    for name in ("n_buy", "n_sell"):
        dist = trial.distributions[name]
        assert isinstance(dist, IntDistribution)
        assert dist.low == 3 and dist.high == 10


def test_log_scale_flags(sampled):
    trial, _ = sampled
    for name, lo, hi in (
        ("buy_near_pct", 0.005, 0.10),
        ("sell_near_pct", 0.005, 0.10),
        ("buy_far_pct", 0.03, 0.45),
        ("sell_far_pct", 0.03, 0.45),
    ):
        dist = trial.distributions[name]
        assert isinstance(dist, FloatDistribution)
        assert dist.log is True, f"{name} must be log-scaled"
        assert dist.low == lo and dist.high == hi


def test_linear_params(sampled):
    trial, _ = sampled
    for name, lo, hi in (
        ("buy_gamma", 0.5, 2.0), ("sell_gamma", 0.5, 2.0),
        ("k_buy", -2.0, 4.0), ("k_sell", -2.0, 4.0),
    ):
        dist = trial.distributions[name]
        assert isinstance(dist, FloatDistribution)
        assert dist.log is False
        assert dist.low == lo and dist.high == hi


def test_fixed_params_not_sampled(sampled):
    trial, params = sampled
    # fund/timing are threaded through but never exposed to the sampler
    for fixed in ("fund_quote", "quote_frac", "cooldown_time", "executor_refresh_time"):
        assert fixed in params
        assert fixed not in trial.params
    assert params["cooldown_time"] == PHASE_A_COOLDOWN_SECONDS
    assert params["fund_quote"] == DEFAULT_FUND_QUOTE


def test_fixed_quote_overrides_fund():
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=8))
    trial = study.ask()
    params = suggest_range_ladder_params(trial, fixed_quote=250.0)
    assert params["fund_quote"] == 250.0
