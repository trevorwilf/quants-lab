"""Gate-policy tests (Phase A.1 §2): strict / accumulate_ok / soft modes,
fill-frequency gates, defaults preserving Phase A, and incumbent-vs-trial
policy parity via the shared evaluator."""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from pmm_lab.optuna.objective_wrapper_range_ladder import (
    GatePolicy,
    evaluate_fold_gates,
    evaluate_ladder_walkforward,
    plan_range_ladder_folds,
)
from pmm_lab.objective.walkforward import TimeSeriesCV
from tests.conftest import CANDLE_DTYPE

BAR_SECONDS = 3600


def _fold(**overrides):
    base = dict(
        buy_fills=5, sell_fills=5, endinv_pct=50.0, maxdd=20.0,
        trades_per_month=10.0, cons_ann_pct=5.0,
    )
    base.update(overrides)
    return base


# ----------------------------------------------------------------------
# evaluate_fold_gates — per-mode math on synthetic fold results
# ----------------------------------------------------------------------

def test_defaults_preserve_phase_a():
    """GatePolicy() is exactly the Phase A gate set: strict endinv 75,
    plain two-sidedness, no fill-frequency or touch constraints."""
    p = GatePolicy()
    assert p.mode == "strict"
    assert p.endinv_gate_pct == 75.0
    assert p.min_trades_per_month == 0.0
    assert p.min_side_fills_per_fold == 1
    assert p.min_rung_touches_train == 0

    ok_fold = _fold(endinv_pct=74.9, trades_per_month=0.1, buy_fills=1, sell_fills=1)
    violated, reasons, penalty = evaluate_fold_gates(ok_fold, p)
    assert not violated and penalty == 0.0

    bad = _fold(endinv_pct=75.1)
    violated, reasons, _ = evaluate_fold_gates(bad, p)
    assert violated and any("endinv" in r for r in reasons)

    one_sided = _fold(sell_fills=0)
    violated, reasons, _ = evaluate_fold_gates(one_sided, p)
    assert violated and any("two-sided" in r for r in reasons)


def test_invalid_mode_rejected():
    with pytest.raises(ValueError, match="mode"):
        GatePolicy(mode="lenient")


def test_accumulate_ok_waives_endinv_adds_risk_gates():
    p = GatePolicy(mode="accumulate_ok")
    # endinv 99.7 (the live XMR case) no longer violates
    violated, reasons, _ = evaluate_fold_gates(_fold(endinv_pct=99.7), p)
    assert not violated, reasons
    # conservative floor replaces it
    violated, reasons, _ = evaluate_fold_gates(
        _fold(endinv_pct=99.7, cons_ann_pct=-0.1), p)
    assert violated and any("conservative" in r for r in reasons)
    # max drawdown gate
    violated, reasons, _ = evaluate_fold_gates(
        _fold(endinv_pct=99.7, maxdd=60.1), p)
    assert violated and any("drawdown" in r for r in reasons)
    # missing conservative score (stress off) → cons gate skipped
    violated, reasons, _ = evaluate_fold_gates(
        _fold(endinv_pct=99.7, cons_ann_pct=None), p)
    assert not violated


def test_soft_mode_penalty_math():
    p = GatePolicy(mode="soft", endinv_penalty=20.0, endinv_gate_pct=75.0)
    violated, reasons, penalty = evaluate_fold_gates(_fold(endinv_pct=90.0), p)
    assert not violated                       # endinv never prunes in soft
    assert penalty == pytest.approx(20.0 * (90.0 - 75.0) / 100.0)  # = 3.0
    _, _, penalty0 = evaluate_fold_gates(_fold(endinv_pct=60.0), p)
    assert penalty0 == 0.0
    # two-sidedness still gates in soft mode
    violated, reasons, _ = evaluate_fold_gates(
        _fold(endinv_pct=60.0, buy_fills=0), p)
    assert violated


def test_fill_frequency_gates_all_modes():
    for mode in ("strict", "accumulate_ok", "soft"):
        p = GatePolicy(mode=mode, min_trades_per_month=6.0, min_side_fills_per_fold=3)
        violated, reasons, _ = evaluate_fold_gates(
            _fold(trades_per_month=5.9), p)
        assert violated and any("trades/month" in r for r in reasons), mode
        violated, reasons, _ = evaluate_fold_gates(
            _fold(buy_fills=2, sell_fills=9), p)
        assert violated and any("per-side fills" in r for r in reasons), mode
        violated, _, _ = evaluate_fold_gates(
            _fold(trades_per_month=6.0, buy_fills=3, sell_fills=3), p)
        assert not violated, mode


def test_endinv_gate_pct_is_parametric():
    p = GatePolicy(mode="strict", endinv_gate_pct=90.0)
    violated, _, _ = evaluate_fold_gates(_fold(endinv_pct=85.0), p)
    assert not violated
    violated, _, _ = evaluate_fold_gates(_fold(endinv_pct=90.1), p)
    assert violated


# ----------------------------------------------------------------------
# Objective-level integration
# ----------------------------------------------------------------------

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


VALID_PARAMS = dict(
    n_buy=4, n_sell=4,
    buy_near_pct=0.02, buy_far_pct=0.15,
    sell_near_pct=0.02, sell_far_pct=0.15,
    buy_gamma=1.0, sell_gamma=1.0,
    k_buy=0.5, k_sell=0.5,
)


def _pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.002, taker_fee=0.002),
    )


def _run_one_trial(candles, gate_policy=None, objective_mode="median_ann",
                   params=VALID_PARAMS, train=60.0, test=20.0):
    objective = create_objective(
        candles=candles,
        pair_rules=_pair_rules(),
        bar_interval_seconds=BAR_SECONDS,
        dataset_hash="gate_test",
        reference_price=100.0,
        strategy_name="range_ladder",
        train_days=train, test_days=test, step_days=test,
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


def test_accumulate_ok_completes_where_strict_prunes():
    """The 20d-window inventory ratchet (endinv 93-95%) prunes under strict
    but completes under accumulate_ok (Phase A.1's motivating case)."""
    candles = _oscillating_candles(n=3000)
    strict = _run_one_trial(candles, GatePolicy(mode="strict"))
    assert strict.state == optuna.trial.TrialState.PRUNED
    acc = _run_one_trial(candles, GatePolicy(mode="accumulate_ok", max_dd_pct=100.0))
    assert acc.state == optuna.trial.TrialState.COMPLETE
    assert acc.user_attrs["gate_policy"]["mode"] == "accumulate_ok"


def test_soft_mode_completes_and_penalizes():
    candles = _oscillating_candles(n=3000)
    soft = _run_one_trial(candles, GatePolicy(mode="soft"))
    assert soft.state == optuna.trial.TrialState.COMPLETE
    detail = soft.user_attrs["fold_detail"]
    # the ratcheting folds carry a positive soft penalty and score < raw ann
    penalized = [d for d in detail if d.get("soft_penalty", 0) > 0]
    assert penalized, "expected at least one endinv-penalized fold"
    for d in penalized:
        assert d["score_ann_pct"] == pytest.approx(
            d["ann_pnl_pct"] - d["soft_penalty"], rel=1e-9)


def test_default_policy_matches_phase_a_objective():
    """gate_policy=None must reproduce the Phase A objective exactly."""
    candles = _oscillating_candles()
    t_default = _run_one_trial(candles, None, train=None, test=None)
    t_explicit = _run_one_trial(candles, GatePolicy(), train=None, test=None)
    assert t_default.state == t_explicit.state == optuna.trial.TrialState.COMPLETE
    assert t_default.value == pytest.approx(t_explicit.value, rel=1e-12)


def test_incumbent_and_trial_judged_identically():
    """The benchmark path (trial=None) and the trial path share the evaluator:
    same rungs + same policy → same fold scores and objective."""
    from pmm_lab.strategies.range_ladder import RangeLadderConfig

    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)
    train, test, step = plan_range_ladder_folds(len(candles), BAR_SECONDS)
    cv = TimeSeriesCV(
        n_bars=len(candles), bar_interval_seconds=BAR_SECONDS,
        train_days=train, test_days=test, step_days=step,
        embargo_bars=0, macd_slow=3, natr_length=3,
    )
    fold_defs = cv.get_folds()
    lit = RangeLadderConfig(
        fund_quote=1000.0, fee=0.002, cooldown_bars=1,
        literal_buy_prices=(98.0, 95.0, 90.0),
        literal_buy_weights=(1.0, 1.0, 2.0),
        literal_sell_prices=(102.0, 105.0, 110.0),
        literal_sell_weights=(2.0, 1.0, 1.0),
    )
    rungs = lit.resolve_rungs(100.0, 0.01)
    kwargs = dict(
        rung_provider=lambda fd: (rungs, 100.0, None),
        fund=1000.0, quote_frac=0.5, fee=0.002, cooldown_bars=1,
        stress_config=lit, run_stress=True,
        gate_policy=policy, objective_mode="median_ann",
    )
    bench = evaluate_ladder_walkforward(
        candles, fold_defs, BAR_SECONDS, trial=None, **kwargs)
    study = optuna.create_study(direction="maximize",
                                pruner=optuna.pruners.NopPruner())
    trial_results = {}

    def objective(trial):
        res = evaluate_ladder_walkforward(
            candles, fold_defs, BAR_SECONDS, trial=trial, **kwargs)
        trial_results.update(res)
        return res["objective"]

    study.optimize(objective, n_trials=1, catch=())
    assert study.trials[0].state == optuna.trial.TrialState.COMPLETE
    assert trial_results["objective"] == pytest.approx(bench["objective"], rel=1e-12)
    assert trial_results["fold_scores"] == pytest.approx(bench["fold_scores"], rel=1e-12)
    assert trial_results["violations"] == bench["violations"]
