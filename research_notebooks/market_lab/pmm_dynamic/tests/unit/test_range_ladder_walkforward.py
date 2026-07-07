"""range_ladder walk-forward objective tests.

Covers: fold-plan math (§3.6), winsorized aggregation (§3.5), train-only
anchoring / leakage (§3.2), gate + prune logic (§3.4), and canonicalizer
rejection → TrialPruned.
"""

import math

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.objective.objective import REJECT_SCORE
from pmm_lab.objective.walkforward import TimeSeriesCV
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.objective_wrapper_range_ladder import (
    plan_range_ladder_folds,
    winsorized_fold_objective,
)
from tests.conftest import CANDLE_DTYPE

BAR_SECONDS = 3600


def _pair_rules(maker=0.002):
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=maker, taker_fee=maker),
    )


def _oscillating_candles(n=4400, seed=11, amplitude=12.0, period=120):
    """Range-bound oscillation around 100 — both ladder sides get filled."""
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype="int64") * BAR_SECONDS + 1_700_000_000
    close = 100.0 + amplitude * np.sin(2 * np.pi * np.arange(n) / period)
    close = close + rng.normal(0, 0.6, n)
    close = np.maximum(close, 1.0)
    o = np.roll(close, 1)
    o[0] = close[0]
    h = np.maximum(o, close) + np.abs(rng.normal(0, 0.4, n))
    l = np.minimum(o, close) - np.abs(rng.normal(0, 0.4, n))
    rows = [
        (int(ts[i]), o[i], h[i], l[i], close[i], 1.0, False) for i in range(n)
    ]
    return np.array(rows, dtype=CANDLE_DTYPE)


def _trending_candles(n=4400):
    """Monotonic ramp — buys below the anchor never fill (never two-sided)."""
    ts = np.arange(n, dtype="int64") * BAR_SECONDS + 1_700_000_000
    close = 100.0 + 0.05 * np.arange(n)
    o = np.roll(close, 1)
    o[0] = close[0]
    rows = [
        (int(ts[i]), o[i], max(o[i], close[i]) + 0.01,
         min(o[i], close[i]) - 0.01, close[i], 1.0, False)
        for i in range(n)
    ]
    return np.array(rows, dtype=CANDLE_DTYPE)


VALID_PARAMS = dict(
    n_buy=4, n_sell=4,
    buy_near_pct=0.02, buy_far_pct=0.15,
    sell_near_pct=0.02, sell_far_pct=0.15,
    buy_gamma=1.0, sell_gamma=1.0,
    k_buy=0.5, k_sell=0.5,
)


def _run_one_trial(candles, params=VALID_PARAMS, **factory_overrides):
    kwargs = dict(
        candles=candles,
        pair_rules=_pair_rules(),
        bar_interval_seconds=BAR_SECONDS,
        dataset_hash="rl_test",
        reference_price=100.0,
        strategy_name="range_ladder",
        train_days=None, test_days=None, step_days=None,  # auto §3.6 plan
        fixed_quote=1000.0,
        run_stress=True,
    )
    kwargs.update(factory_overrides)
    objective = create_objective(**kwargs)
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.RandomSampler(seed=5),
        pruner=optuna.pruners.NopPruner(),
    )
    study.enqueue_trial(dict(params))
    study.optimize(objective, n_trials=1, catch=())
    return study.trials[0]


# ----------------------------------------------------------------------
# §3.6 fold plan
# ----------------------------------------------------------------------

def test_fold_plan_capped_by_60d():
    bars = 450 * 24  # 450 days of 1h bars
    train, test, step = plan_range_ladder_folds(bars, BAR_SECONDS)
    assert test == 60.0 and step == 60.0
    assert train == pytest.approx(450 - 180)


def test_fold_plan_capped_by_total_over_5():
    bars = 250 * 24
    train, test, step = plan_range_ladder_folds(bars, BAR_SECONDS)
    assert test == 50.0  # floor(250/5) binds before 60d
    assert train >= 90.0


def test_fold_plan_preserves_min_train_at_150d():
    bars = 150 * 24
    train, test, step = plan_range_ladder_folds(bars, BAR_SECONDS)
    assert test == 20.0  # (150 - 90) / 3
    assert train == pytest.approx(90.0)


def test_fold_plan_insufficient_history_raises():
    with pytest.raises(ValueError, match="insufficient history"):
        plan_range_ladder_folds(80 * 24, BAR_SECONDS)


def test_fold_plan_yields_exactly_three_folds():
    for days in (150, 200, 365, 500):
        n = days * 24
        train, test, step = plan_range_ladder_folds(n, BAR_SECONDS)
        cv = TimeSeriesCV(
            n_bars=n, bar_interval_seconds=BAR_SECONDS,
            train_days=train, test_days=test, step_days=step,
            embargo_bars=0, macd_slow=3, natr_length=3,
        )
        assert len(cv.get_folds()) == 3, f"{days}d should produce 3 folds"


# ----------------------------------------------------------------------
# §3.5 winsorized aggregation
# ----------------------------------------------------------------------

def test_winsorized_math_hand_computed():
    # scores [10, 12, 100]: med=12, MAD=2 → clamp to [8, 16] → [10, 12, 16]
    # winsorized med=12, MAD=2 → objective = 12 − 0.5*2 = 11
    obj, w = winsorized_fold_objective([10.0, 12.0, 100.0])
    assert w == [10.0, 12.0, 16.0]
    assert obj == pytest.approx(11.0)


def test_winsorized_symmetric_scores_unchanged():
    obj, w = winsorized_fold_objective([5.0, 10.0, 15.0])
    assert w == [5.0, 10.0, 15.0]
    assert obj == pytest.approx(10.0 - 0.5 * 5.0)


def test_winsorized_empty_returns_reject():
    obj, w = winsorized_fold_objective([])
    assert obj == REJECT_SCORE and w == []


def test_winsorized_downside_outlier_clamped():
    obj_out, _ = winsorized_fold_objective([-500.0, 10.0, 12.0])
    obj_mild, _ = winsorized_fold_objective([6.0, 10.0, 12.0])
    assert obj_out <= obj_mild
    # the clamp bounds how far one catastrophic fold can drag the objective
    assert obj_out > -500.0


# ----------------------------------------------------------------------
# Objective end-to-end (single deterministic trial)
# ----------------------------------------------------------------------

def test_objective_trial_completes_with_expected_attrs():
    candles = _oscillating_candles()
    trial = _run_one_trial(candles)
    assert trial.state == optuna.trial.TrialState.COMPLETE
    ua = trial.user_attrs
    assert ua["strategy_name"] == "range_ladder"
    assert ua["dataset_hash"] == "rl_test"
    assert ua["n_folds"] == 3
    assert len(ua["fold_scores"]) == 3
    assert "fold_scores_winsorized" in ua
    assert "last_fold_rungs" in ua
    assert "cons_score_median" in ua       # run_stress=True
    assert ua["objective_score"] == pytest.approx(trial.value)
    # every fold carries the eyeball detail
    for d in ua["fold_detail"]:
        assert {"anchor", "endinv_pct", "buy_fills", "sell_fills", "two_sided"} <= set(d)


def test_anchor_is_median_of_last_three_train_closes():
    candles = _oscillating_candles()
    trial = _run_one_trial(candles)
    train, test, step = plan_range_ladder_folds(len(candles), BAR_SECONDS)
    cv = TimeSeriesCV(
        n_bars=len(candles), bar_interval_seconds=BAR_SECONDS,
        train_days=train, test_days=test, step_days=step,
        embargo_bars=0, macd_slow=3, natr_length=3,
    )
    closes = candles["close"].astype(np.float64)
    for fd, detail in zip(cv.get_folds(), trial.user_attrs["fold_detail"]):
        expected = float(np.median(closes[fd.train_end_idx - 3:fd.train_end_idx]))
        assert detail["anchor"] == pytest.approx(expected, rel=1e-12)


def test_anchor_never_sees_test_data():
    """Corrupting every fold's TEST window must not move any fold anchor."""
    candles = _oscillating_candles()
    trial_a = _run_one_trial(candles)

    train, test, step = plan_range_ladder_folds(len(candles), BAR_SECONDS)
    cv = TimeSeriesCV(
        n_bars=len(candles), bar_interval_seconds=BAR_SECONDS,
        train_days=train, test_days=test, step_days=step,
        embargo_bars=0, macd_slow=3, natr_length=3,
    )
    folds = cv.get_folds()
    mutated = candles.copy()
    first_test_start = folds[0].test_start_idx
    for field in ("open", "high", "low", "close"):
        mutated[field][first_test_start:] = mutated[field][first_test_start:] * 3.0

    trial_b = _run_one_trial(mutated)
    # Fold 0's train window [0, train_end) is untouched by the mutation
    # (train_end == first_test_start with embargo 0) → identical anchor.
    a0 = trial_a.user_attrs["fold_detail"][0]["anchor"]
    b0 = trial_b.user_attrs["fold_detail"][0]["anchor"]
    assert a0 == pytest.approx(b0, rel=1e-12)
    # ...while the fold-0 test result itself must differ (sanity that the
    # mutation actually reached the sim).
    assert (trial_a.user_attrs["fold_detail"][0]["pnl_pct"]
            != trial_b.user_attrs["fold_detail"][0]["pnl_pct"])


def test_gate_majority_violation_prunes():
    """A trending market never fills buys → not two-sided in every fold →
    majority gate violations → TrialPruned."""
    candles = _trending_candles()
    trial = _run_one_trial(candles)
    assert trial.state == optuna.trial.TrialState.PRUNED
    assert trial.user_attrs["gate_violations"] >= 2


def test_canonicalizer_rejection_prunes():
    bad = dict(VALID_PARAMS)
    bad["buy_far_pct"] = 0.031
    bad["buy_near_pct"] = 0.099   # near ≈ far after log-sampling → far < near
    candles = _oscillating_candles()
    trial = _run_one_trial(candles, params=bad)
    assert trial.state == optuna.trial.TrialState.PRUNED
    assert trial.user_attrs["reject_reason"] is not None


def test_explicit_fold_windows_are_honored():
    """Explicit train/test/step override the §3.6 auto-plan.

    The trial may legitimately end PRUNED here (short 20d windows ratchet
    inventory past the endinv gate — the gate working as designed); the
    assertion is only that the requested fold layout was used.
    """
    candles = _oscillating_candles(n=3000)
    trial = _run_one_trial(
        candles, train_days=60.0, test_days=20.0, step_days=20.0,
    )
    assert trial.state in (
        optuna.trial.TrialState.COMPLETE, optuna.trial.TrialState.PRUNED,
    )
    assert trial.user_attrs["fold_plan_days"]["test"] == 20.0
    assert trial.user_attrs["fold_plan_days"]["train"] == 60.0
    assert trial.user_attrs["n_folds"] == 3
    assert len(trial.user_attrs["fold_detail"]) == 3
