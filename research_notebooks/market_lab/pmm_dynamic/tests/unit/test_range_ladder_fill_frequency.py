"""Fill-frequency preference tests (Phase A.2 §3): per-rung train-touch
constraint, fill-frequency gates, and the consistency-blended objective."""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.objective_wrapper_range_ladder import (
    GatePolicy,
    frac_positive_windows,
)
from pmm_lab.strategies.range_ladder_gen import count_rung_touches
from tests.conftest import CANDLE_DTYPE

BAR_SECONDS = 3600


# ----------------------------------------------------------------------
# count_rung_touches
# ----------------------------------------------------------------------

def test_touch_counts_known_series():
    high = np.array([101.0] * 5 + [96.0] * 3)
    low = np.array([99.0] * 5 + [95.0] * 3)
    rungs = np.array([100.0, 95.5, 90.0])
    touches = count_rung_touches(high, low, rungs)
    assert list(touches) == [5, 3, 0]


def test_touch_boundary_inclusive():
    high = np.array([102.0])
    low = np.array([100.0])
    assert list(count_rung_touches(high, low, np.array([100.0]))) == [1]
    assert list(count_rung_touches(high, low, np.array([102.0]))) == [1]
    assert list(count_rung_touches(high, low, np.array([99.999]))) == [0]
    assert list(count_rung_touches(high, low, np.array([102.001]))) == [0]


def test_touch_empty_inputs():
    assert list(count_rung_touches(np.array([]), np.array([]), np.array([100.0]))) == [0]
    assert len(count_rung_touches(np.array([1.0]), np.array([0.5]), np.array([]))) == 0


# ----------------------------------------------------------------------
# Touch constraint in the objective (leakage-free, cheap rejection)
# ----------------------------------------------------------------------

def _pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.002, taker_fee=0.002),
    )


def _oscillating_candles(n=4400, seed=11, amplitude=12.0, period=120):
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype="int64") * BAR_SECONDS + 1_700_000_000
    close = 100.0 + amplitude * np.sin(2 * np.pi * np.arange(n) / period)
    close = close + rng.normal(0, 0.6, n)
    close = np.maximum(close, 1.0)
    o = np.roll(close, 1)
    o[0] = close[0]
    h = np.maximum(o, close) + np.abs(rng.normal(0, 0.4, n))
    l = np.minimum(o, close) - np.abs(rng.normal(0, 0.4, n))
    rows = [(int(ts[i]), o[i], h[i], l[i], close[i], 1.0, False) for i in range(n)]
    return np.array(rows, dtype=CANDLE_DTYPE)


def _run_one_trial(candles, params, gate_policy, objective_mode="median_ann",
                   train_days=None, test_days=None, step_days=None):
    objective = create_objective(
        candles=candles,
        pair_rules=_pair_rules(),
        bar_interval_seconds=BAR_SECONDS,
        dataset_hash="ff_test",
        reference_price=100.0,
        strategy_name="range_ladder",
        train_days=train_days, test_days=test_days, step_days=step_days,
        fixed_quote=1000.0,
        run_stress=True,
        gate_policy=gate_policy,
        objective_mode=objective_mode,
    )
    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.RandomSampler(seed=5),
        pruner=optuna.pruners.NopPruner(),
    )
    study.enqueue_trial(dict(params))
    study.optimize(objective, n_trials=1, catch=())
    return study.trials[0]


NEAR_PARAMS = dict(
    n_buy=4, n_sell=4,
    buy_near_pct=0.02, buy_far_pct=0.10,   # inside the ±12% oscillation → touched
    sell_near_pct=0.02, sell_far_pct=0.10,
    buy_gamma=1.0, sell_gamma=1.0, k_buy=0.5, k_sell=0.5,
)
DEEP_PARAMS = dict(
    n_buy=4, n_sell=4,
    buy_near_pct=0.02, buy_far_pct=0.40,   # 40% deep rungs — never touched
    sell_near_pct=0.02, sell_far_pct=0.40,
    buy_gamma=1.0, sell_gamma=1.0, k_buy=0.5, k_sell=0.5,
)


def test_touch_constraint_prunes_deep_parked_rungs():
    """Deep rungs that never see a train touch — the endinv-gate-gaming
    pattern from the 2026-07-07 run — are pruned before any sim.

    Explicit 60/20/20d fold windows align every train_end to the oscillation
    midpoint (period 120 bars = 5d), so the NEAR ladder's rungs all live
    inside the ±12% price range while the DEEP 40% rungs never trade.
    """
    candles = _oscillating_candles(n=3000)
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0,
                        min_rung_touches_train=8, touch_lookback_days=270.0)
    windows = dict(train_days=60.0, test_days=20.0, step_days=20.0)
    deep = _run_one_trial(candles, DEEP_PARAMS, policy, **windows)
    assert deep.state == optuna.trial.TrialState.PRUNED
    assert "min rung touches" in deep.user_attrs["reject_reason"]
    # a pruned-by-touch trial never simulated: no fold_detail scores
    assert "fold_detail" not in deep.user_attrs or not any(
        "score_ann_pct" in d for d in deep.user_attrs.get("fold_detail", []))

    near = _run_one_trial(candles, NEAR_PARAMS, policy, **windows)
    assert near.state == optuna.trial.TrialState.COMPLETE
    assert near.user_attrs["min_rung_touches"] >= 8


def test_touch_constraint_disabled_by_default():
    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)  # touches off
    deep = _run_one_trial(candles, DEEP_PARAMS, policy)
    # not pruned by touches (may complete; gates depend on fills)
    if deep.state == optuna.trial.TrialState.PRUNED:
        assert "min rung touches" not in (deep.user_attrs.get("reject_reason") or "")


def test_fill_frequency_gate_prunes_on_majority():
    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0,
                        min_trades_per_month=10_000.0)  # impossible bar
    t = _run_one_trial(candles, NEAR_PARAMS, policy)
    assert t.state == optuna.trial.TrialState.PRUNED
    assert "majority" in str(t.user_attrs.get("reject_reason", ""))


# ----------------------------------------------------------------------
# Consistency-blended objective (§3c)
# ----------------------------------------------------------------------

def test_frac_positive_windows_monotone_up():
    n = 1440  # 60d of 1h bars
    eq = np.linspace(1000.0, 1200.0, n)
    assert frac_positive_windows(eq, BAR_SECONDS) == 1.0


def test_frac_positive_windows_sawtooth_down():
    n = 1440
    base = np.linspace(1000.0, 700.0, n)          # strong downtrend
    wiggle = 2.0 * np.sin(np.arange(n) / 3.0)     # small oscillation
    frac = frac_positive_windows(base + wiggle, BAR_SECONDS)
    assert frac <= 0.1


def test_frac_positive_windows_short_curve_single_window():
    eq_up = np.array([100.0, 101.0, 102.0])
    eq_dn = np.array([100.0, 99.0, 98.0])
    assert frac_positive_windows(eq_up, BAR_SECONDS) == 1.0
    assert frac_positive_windows(eq_dn, BAR_SECONDS) == 0.0


def test_frac_positive_windows_window_math():
    # 40 days of 1h bars: windows of 30d (720 bars) step 7d (168):
    # starts 0, 168 → 2 full windows
    n = 960
    eq = np.concatenate([np.linspace(100, 110, 720), np.linspace(110, 90, 240)])
    frac = frac_positive_windows(eq, BAR_SECONDS)
    # window 0 (0..719) is positive; window 1 (168..887) ends lower than start
    assert frac == pytest.approx(0.5)


def test_median_ann_mode_bit_identical():
    """OBJECTIVE_MODE='median_ann' must not change Phase A scoring at all."""
    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)
    a = _run_one_trial(candles, NEAR_PARAMS, policy, objective_mode="median_ann")
    b = _run_one_trial(candles, NEAR_PARAMS, policy)   # default
    assert a.state == b.state == optuna.trial.TrialState.COMPLETE
    assert a.value == b.value
    for da, db in zip(a.user_attrs["fold_detail"], b.user_attrs["fold_detail"]):
        assert da["score_ann_pct"] == db["score_ann_pct"]
        assert da["frac_positive_windows"] is None and db["frac_positive_windows"] is None


def test_consistency_mode_blends_fold_scores():
    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)
    t = _run_one_trial(candles, NEAR_PARAMS, policy, objective_mode="consistency")
    assert t.state == optuna.trial.TrialState.COMPLETE
    assert t.user_attrs["objective_mode"] == "consistency"
    for d in t.user_attrs["fold_detail"]:
        frac = d["frac_positive_windows"]
        assert frac is not None and 0.0 <= frac <= 1.0
        expected = d["ann_pnl_pct"] * (0.5 + 0.5 * frac) - d["soft_penalty"]
        assert d["score_ann_pct"] == pytest.approx(expected, rel=1e-9)
