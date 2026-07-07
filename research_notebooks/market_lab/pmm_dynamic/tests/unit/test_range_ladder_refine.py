"""refine_incumbent tests (Phase A.1 §3): overlay/nudge math, identity
bit-exactness, constraint pruning, and stage smoke tests (TPE + CMA-ES)."""

import numpy as np
import optuna
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper_range_ladder import (
    GatePolicy,
    create_range_ladder_refine_objective,
    evaluate_ladder_walkforward,
    plan_range_ladder_folds,
)
from pmm_lab.optuna.search_space_range_ladder import (
    IDENTITY_OVERLAY_PARAMS,
    identity_nudge_params,
)
from pmm_lab.objective.walkforward import TimeSeriesCV
from pmm_lab.strategies.range_ladder import RangeLadderConfig
from pmm_lab.strategies.range_ladder_gen import (
    RungSet,
    apply_ladder_overlay,
    apply_per_rung_nudge,
    quantize_price,
)
from tests.conftest import CANDLE_DTYPE

BAR_SECONDS = 3600

# The live DASH ladder — deliberately OFF the 0.01 tick grid (4-dp prices),
# so identity bit-exactness also proves untouched sides are not re-quantized.
DASH_RUNGS = RungSet(
    buys=np.array([32.851, 32.112, 31.3395, 30.6005, 29.8615]),
    sells=np.array([36.1764, 38.7965, 41.3829, 43.9693, 46.5893]),
    buy_weights=np.array([7.6, 11.4, 17.1, 25.6, 38.4]),
    sell_weights=np.array([39.9, 25.8, 16.6, 10.7, 6.9]),
)


# ----------------------------------------------------------------------
# Overlay math
# ----------------------------------------------------------------------

def test_identity_overlay_is_bit_exact():
    out = apply_ladder_overlay(DASH_RUNGS, price_tick=0.01, **IDENTITY_OVERLAY_PARAMS)
    assert np.array_equal(out.buys, DASH_RUNGS.buys)
    assert np.array_equal(out.sells, DASH_RUNGS.sells)
    assert np.array_equal(out.buy_weights, DASH_RUNGS.buy_weights)
    assert np.array_equal(out.sell_weights, DASH_RUNGS.sell_weights)


def test_overlay_shift_moves_whole_side():
    out = apply_ladder_overlay(
        DASH_RUNGS, price_tick=1e-9, buy_shift_pct=-0.02,
        sell_shift_pct=0.0, buy_stretch=1.0, sell_stretch=1.0,
        buy_tilt_delta=0.0, sell_tilt_delta=0.0,
    )
    # stretch=1 → p_i' = p_near*(1+shift) * (p_i/p_near) = p_i * 0.98
    expected = DASH_RUNGS.buys * 0.98
    np.testing.assert_allclose(out.buys, expected, rtol=1e-9)
    assert np.array_equal(out.sells, DASH_RUNGS.sells)   # untouched side


def test_overlay_stretch_hand_computed():
    rungs = RungSet(
        buys=np.array([98.0, 94.0, 88.0]),
        sells=np.array([102.0, 108.0]),
        buy_weights=np.array([1.0, 1.0, 1.0]),
        sell_weights=np.array([1.0, 1.0]),
    )
    out = apply_ladder_overlay(
        rungs, price_tick=1e-9, buy_shift_pct=0.0, sell_shift_pct=0.0,
        buy_stretch=1.2, sell_stretch=1.0, buy_tilt_delta=0.0, sell_tilt_delta=0.0,
    )
    p_near = 98.0
    expected = [p_near * (p / p_near) ** 1.2 for p in rungs.buys]
    np.testing.assert_allclose(out.buys, expected, rtol=1e-9)
    # nearest rung is invariant under pure stretch
    assert out.buys[0] == pytest.approx(98.0, rel=1e-12)
    # stretch > 1 pushes the far rung deeper
    assert out.buys[-1] < rungs.buys[-1]


def test_overlay_tilt_hand_computed():
    rungs = RungSet(
        buys=np.array([98.0, 94.0, 88.0]),
        sells=np.array([102.0, 108.0]),
        buy_weights=np.array([1.0, 1.0, 1.0]),
        sell_weights=np.array([2.0, 1.0]),
    )
    out = apply_ladder_overlay(
        rungs, price_tick=1e-9, buy_shift_pct=0.0, sell_shift_pct=0.0,
        buy_stretch=1.0, sell_stretch=1.0, buy_tilt_delta=1.5, sell_tilt_delta=0.0,
    )
    x = np.array([0.0, 0.5, 1.0])
    w = np.array([1.0, 1.0, 1.0]) * np.exp(1.5 * x)
    np.testing.assert_allclose(out.buy_weights, w / w.max(), rtol=1e-12)
    assert np.array_equal(out.sell_weights, rungs.sell_weights)
    # prices untouched by a pure tilt
    assert np.array_equal(out.buys, rungs.buys)


def test_overlay_moved_prices_are_quantized():
    out = apply_ladder_overlay(
        DASH_RUNGS, price_tick=0.01, buy_shift_pct=0.011,
        sell_shift_pct=-0.011, buy_stretch=1.0, sell_stretch=1.0,
        buy_tilt_delta=0.0, sell_tilt_delta=0.0,
    )
    for p in out.buys:
        assert abs(p / 0.01 - round(p / 0.01)) < 1e-6
    for p in out.sells:
        assert abs(p / 0.01 - round(p / 0.01)) < 1e-6


# ----------------------------------------------------------------------
# Per-rung nudge math
# ----------------------------------------------------------------------

def test_identity_nudge_is_bit_exact():
    ones_b = np.ones(5)
    out = apply_per_rung_nudge(
        DASH_RUNGS, ones_b, np.ones(5), ones_b, np.ones(5), price_tick=0.01,
    )
    assert np.array_equal(out.buys, DASH_RUNGS.buys)
    assert np.array_equal(out.sells, DASH_RUNGS.sells)
    assert np.array_equal(out.buy_weights, DASH_RUNGS.buy_weights)
    assert np.array_equal(out.sell_weights, DASH_RUNGS.sell_weights)


def test_nudge_moves_single_rung():
    mults = np.ones(5)
    mults[2] = 1.01
    out = apply_per_rung_nudge(
        DASH_RUNGS, mults, np.ones(5), np.ones(5), np.ones(5), price_tick=0.01,
    )
    assert out.buys[2] == quantize_price(DASH_RUNGS.buys[2] * 1.01, 0.01, "buy")
    for i in (0, 1, 3, 4):
        assert out.buys[i] == DASH_RUNGS.buys[i]


def test_nudge_rejects_length_mismatch():
    with pytest.raises(ValueError, match="multipliers"):
        apply_per_rung_nudge(
            DASH_RUNGS, np.ones(3), np.ones(5), np.ones(5), np.ones(5),
            price_tick=0.01,
        )


def test_identity_nudge_params_shape():
    p = identity_nudge_params(3, 4)
    assert len(p) == 2 * (3 + 4)
    assert all(v == 1.0 for v in p.values())


# ----------------------------------------------------------------------
# Refine objective (stage smoke tests)
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


INCUMBENT = {
    "buy_prices": [98.0, 95.0, 90.0],
    "buy_weights": [1.0, 1.0, 2.0],
    "sell_prices": [102.0, 105.0, 110.0],
    "sell_weights": [2.0, 1.0, 1.0],
}


def _pair_rules():
    return PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.002, taker_fee=0.002),
    )


def _refine_kwargs(candles, **overrides):
    kwargs = dict(
        candles=candles,
        pair_rules=_pair_rules(),
        bar_interval_seconds=BAR_SECONDS,
        dataset_hash="refine_test",
        deploy_anchor=100.0,
        base_rungs=INCUMBENT,
        stage="overlay",
        fund=1000.0, quote_frac=0.5, cooldown_bars=1,
        run_stress=True,
        gate_policy=GatePolicy(mode="accumulate_ok", max_dd_pct=100.0),
    )
    kwargs.update(overrides)
    return kwargs


def _incumbent_benchmark_objective(candles, policy):
    """Benchmark the literal incumbent via the shared evaluator."""
    train, test, step = plan_range_ladder_folds(len(candles), BAR_SECONDS)
    cv = TimeSeriesCV(
        n_bars=len(candles), bar_interval_seconds=BAR_SECONDS,
        train_days=train, test_days=test, step_days=step,
        embargo_bars=0, macd_slow=3, natr_length=3,
    )
    lit = RangeLadderConfig(
        fund_quote=1000.0, fee=0.002, cooldown_bars=1,
        literal_buy_prices=tuple(INCUMBENT["buy_prices"]),
        literal_buy_weights=tuple(INCUMBENT["buy_weights"]),
        literal_sell_prices=tuple(INCUMBENT["sell_prices"]),
        literal_sell_weights=tuple(INCUMBENT["sell_weights"]),
    )
    rungs = lit.resolve_rungs(100.0, 0.01)
    return evaluate_ladder_walkforward(
        candles, cv.get_folds(), BAR_SECONDS,
        rung_provider=lambda fd: (rungs, 100.0, None),
        fund=1000.0, quote_frac=0.5, fee=0.002, cooldown_bars=1,
        stress_config=lit, run_stress=True,
        gate_policy=policy, objective_mode="median_ann", trial=None,
    )["objective"]


def test_identity_overlay_trial_reproduces_incumbent_objective():
    """Trial 0 (identity overlay) must score EXACTLY the incumbent benchmark
    — the refinement study can never lose to its baseline."""
    candles = _oscillating_candles()
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)
    bench = _incumbent_benchmark_objective(candles, policy)

    objective = create_range_ladder_refine_objective(**_refine_kwargs(candles))
    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.NopPruner(),
        sampler=optuna.samplers.RandomSampler(seed=3),
    )
    study.enqueue_trial(dict(IDENTITY_OVERLAY_PARAMS))
    study.optimize(objective, n_trials=1, catch=())
    trial = study.trials[0]
    assert trial.state == optuna.trial.TrialState.COMPLETE
    assert trial.value == pytest.approx(bench, rel=1e-12)
    assert trial.user_attrs["search_mode"] == "refine_incumbent:overlay"
    rr = trial.user_attrs["refined_rungs"]
    assert rr["buys"] == INCUMBENT["buy_prices"]
    assert rr["sells"] == INCUMBENT["sell_prices"]


def test_constraint_violating_overlay_prunes():
    """Shifting buys up and sells down collapses the dead zone → pruned."""
    candles = _oscillating_candles()
    objective = create_range_ladder_refine_objective(**_refine_kwargs(candles))
    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.NopPruner(),
        sampler=optuna.samplers.RandomSampler(seed=3),
    )
    bad = dict(IDENTITY_OVERLAY_PARAMS)
    bad["buy_shift_pct"] = 0.02    # nearest buy 98 → ~99.96
    bad["sell_shift_pct"] = -0.02  # nearest sell 102 → ~99.96
    study.enqueue_trial(bad)
    study.optimize(objective, n_trials=1, catch=())
    trial = study.trials[0]
    assert trial.state == optuna.trial.TrialState.PRUNED
    assert trial.user_attrs["reject_reason"] is not None


def test_overlay_stage_tpe_smoke():
    candles = _oscillating_candles()
    objective = create_range_ladder_refine_objective(**_refine_kwargs(candles))
    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.NopPruner(),
        sampler=optuna.samplers.TPESampler(seed=7, n_startup_trials=3),
    )
    study.enqueue_trial(dict(IDENTITY_OVERLAY_PARAMS))
    study.optimize(objective, n_trials=5, catch=())
    completed = [t for t in study.trials
                 if t.state == optuna.trial.TrialState.COMPLETE]
    assert completed, "identity trial must complete at minimum"


def test_nudge_stage_cmaes_smoke():
    """Stage 2 with the real CmaEsSampler (requires the cmaes package)."""
    pytest.importorskip("cmaes")
    candles = _oscillating_candles()
    objective = create_range_ladder_refine_objective(
        **_refine_kwargs(candles, stage="nudge"))
    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.NopPruner(),
        sampler=optuna.samplers.CmaEsSampler(seed=7, n_startup_trials=1),
    )
    study.enqueue_trial(identity_nudge_params(3, 3))
    study.optimize(objective, n_trials=4, catch=())
    completed = [t for t in study.trials
                 if t.state == optuna.trial.TrialState.COMPLETE]
    assert completed
    # the enqueued identity nudge reproduces the incumbent exactly
    policy = GatePolicy(mode="accumulate_ok", max_dd_pct=100.0)
    bench = _incumbent_benchmark_objective(candles, policy)
    assert completed[0].value == pytest.approx(bench, rel=1e-12)
