"""Validation helpers must accept MR and EMA configs without type errors.

These are smoke tests — they verify the call path doesn't explode and
returns a plausibly-shaped result. Scientific correctness of metrics is
verified by phase-1 unit tests elsewhere.

Helpers exercised:
- pmm_lab/objective/holdout.py::evaluate_holdout
- pmm_lab/objective/recent_window.py::evaluate_recent_window
- pmm_lab/optuna/sensitivity.py::compute_sensitivity
- pmm_lab/objective/stress_selection.py::select_best_stressed_candidate
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.mean_reversion_bb_rsi import MeanReversionBBRSIStrategyConfig
from pmm_lab.strategies.ema_regime_hold import EMARegimeHoldStrategyConfig
from tests.conftest import CANDLE_DTYPE


def _make_candles(n: int = 800, interval: int = 300) -> np.ndarray:
    rng = np.random.default_rng(seed=42)
    start_ts = 1_700_000_000
    price = 100.0
    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        change = rng.normal(0, 0.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.5, 3.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_regime_candles(n: int = 200, interval: int = 28800) -> np.ndarray:
    rng = np.random.default_rng(seed=77)
    start_ts = 1_700_000_000
    price = 100.0
    rows = []
    for i in range(n):
        ts = start_ts + i * interval
        change = rng.normal(0, 1.0)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.5))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.5))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = rng.uniform(0.5, 3.0)
        rows.append((ts, open_p, high_p, low_p, close_p, vol, False))
        price = close_p
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def engine_cfg():
    return EngineConfig(
        total_amount_quote=100.0,
        stop_loss=0.02,
        take_profit=0.03,
        time_limit=3600,
        latency_bars=1,
        slippage_bps=5.0,
    )


@pytest.fixture
def mr_config():
    return MeanReversionBBRSIStrategyConfig(bb_length=20, rsi_length=14, trend_ema_length=50, atr_length=14, volume_filter_window=30, max_trades_per_day=6)


@pytest.fixture
def ema_config_with_regime():
    regime = _make_regime_candles()
    cfg = EMARegimeHoldStrategyConfig(
        regime_ema_fast=10, regime_ema_slow=20, regime_adx_length=14,
        volume_filter_window=30,
    )
    return replace(cfg, _regime_candles=regime), regime


# ----- evaluate_holdout ---------------------------------------------------

def test_evaluate_holdout_accepts_mr_config(pair_rules, engine_cfg, mr_config):
    from pmm_lab.objective.holdout import evaluate_holdout

    candles = _make_candles(n=800)
    holdout = candles[600:]
    report = evaluate_holdout(
        holdout_candles=holdout,
        candidate_configs=[(mr_config, 0.0)],
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        run_stress=False,
        objective_version=2,
        engine_config=engine_cfg,
    )
    assert report is not None
    assert len(report.candidates) == 1
    assert report.holdout_bars == len(holdout)


def test_evaluate_holdout_accepts_ema_config(pair_rules, engine_cfg, ema_config_with_regime):
    from pmm_lab.objective.holdout import evaluate_holdout

    ema_cfg, regime = ema_config_with_regime
    candles = _make_candles(n=800)
    holdout = candles[600:]
    report = evaluate_holdout(
        holdout_candles=holdout,
        candidate_configs=[(ema_cfg, 0.0)],
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        run_stress=False,
        objective_version=2,
        engine_config=engine_cfg,
        regime_candles=regime,
    )
    assert report is not None
    assert len(report.candidates) == 1


# ----- evaluate_recent_window --------------------------------------------

def test_evaluate_recent_window_accepts_mr_config(pair_rules, engine_cfg, mr_config):
    from pmm_lab.objective.recent_window import evaluate_recent_window

    candles = _make_candles(n=800)
    result = evaluate_recent_window(
        full_candles=candles,
        config=mr_config,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        recent_days=1,
        run_stress=False,
        objective_version=2,
        engine_config=engine_cfg,
    )
    assert result is not None
    assert result.recent_bars >= 0


def test_evaluate_recent_window_accepts_ema_config(pair_rules, engine_cfg, ema_config_with_regime):
    from pmm_lab.objective.recent_window import evaluate_recent_window

    ema_cfg, regime = ema_config_with_regime
    candles = _make_candles(n=800)
    result = evaluate_recent_window(
        full_candles=candles,
        config=ema_cfg,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        recent_days=1,
        run_stress=False,
        objective_version=2,
        engine_config=engine_cfg,
        regime_candles=regime,
    )
    assert result is not None


# ----- compute_sensitivity ----------------------------------------------

def test_compute_sensitivity_accepts_mr_canonicalizer(pair_rules, engine_cfg):
    """Pass a MR-style canonicalize_fn (returns a bundle) and verify sensitivity runs."""
    from pmm_lab.optuna.sensitivity import compute_sensitivity
    from pmm_lab.optuna.candidate import CandidateBundle

    # Hand-build a bundle returned by our fake canonicalizer
    def fake_canonicalize(params, pair_rules, reference_price, **kwargs):
        strategy_config = MeanReversionBBRSIStrategyConfig(
            bb_length=params.get("bb_length", 20),
            rsi_length=14,
            trend_ema_length=50,
            atr_length=14,
            volume_filter_window=30,
            max_trades_per_day=6,
        )
        return CandidateBundle(
            strategy_name="mean_reversion_bb_rsi",
            strategy_config=strategy_config,
            engine_config=engine_cfg,
        ), None

    params = {
        "bb_length": 20,
        "total_amount_quote": 100.0,
    }

    candles = _make_candles(n=500)
    report = compute_sensitivity(
        params=params,
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        reference_price=100.0,
        delta_pct=0.10,
        perturb_params=["total_amount_quote"],
        canonicalize_fn=fake_canonicalize,
    )
    assert report is not None
    assert report.baseline_score is not None


def test_compute_sensitivity_accepts_ema_canonicalizer(pair_rules, engine_cfg):
    from pmm_lab.optuna.sensitivity import compute_sensitivity
    from pmm_lab.optuna.candidate import CandidateBundle

    regime = _make_regime_candles()

    def fake_canonicalize(params, pair_rules, reference_price, **kwargs):
        strat = EMARegimeHoldStrategyConfig(
            regime_ema_fast=10, regime_ema_slow=20,
            regime_adx_length=14, volume_filter_window=30,
        )
        strat = replace(strat, _regime_candles=regime)
        return CandidateBundle(
            strategy_name="ema_regime_hold",
            strategy_config=strat,
            engine_config=engine_cfg,
        ), None

    params = {"regime_ema_fast": 10, "total_amount_quote": 100.0}
    candles = _make_candles(n=500)
    report = compute_sensitivity(
        params=params,
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        reference_price=100.0,
        delta_pct=0.10,
        perturb_params=["total_amount_quote"],
        canonicalize_fn=fake_canonicalize,
        regime_candles=regime,
    )
    assert report is not None


# ----- select_best_stressed_candidate ----------------------------------

def test_select_best_stressed_candidate_accepts_mr_config(pair_rules, engine_cfg, mr_config):
    """With apply_scenario_fn=None and non-SimConfig, scenarios are skipped per candidate
    but the candidate itself is still evaluated on baseline. The incumbent update still works."""
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate

    candles = _make_candles(n=500)
    top = [{"config": mr_config, "engine_config": engine_cfg,
            "trial_number": 0, "phase1_score": 0.0}]

    best, diag = select_best_stressed_candidate(
        top_candidates=top,
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        objective_version=2,
    )
    # Scenarios all skipped → scenario_results_pruning_order is empty → the
    # code still falls through to score the baseline. Either best is None
    # (if downstream rejects) or a dict with stress_report.
    assert diag["candidates_evaluated"] == 1


def test_select_best_stressed_candidate_accepts_ema_config(
    pair_rules, engine_cfg, ema_config_with_regime,
):
    from pmm_lab.objective.stress_selection import select_best_stressed_candidate

    ema_cfg, regime = ema_config_with_regime
    candles = _make_candles(n=500)
    top = [{"config": ema_cfg, "engine_config": engine_cfg,
            "trial_number": 0, "phase1_score": 0.0}]

    best, diag = select_best_stressed_candidate(
        top_candidates=top,
        candles=candles,
        pair_rules=pair_rules,
        bar_interval_seconds=300,
        objective_version=2,
        regime_candles=regime,
    )
    assert diag["candidates_evaluated"] == 1


# ----- runner_dispatch smoke --------------------------------------------

def test_run_simulation_dispatches_mr(pair_rules, engine_cfg, mr_config):
    from pmm_lab.sim.runner_dispatch import run_simulation_cold

    candles = _make_candles(n=300)
    result = run_simulation_cold(mr_config, pair_rules, candles,
                                  engine_config=engine_cfg)
    assert result is not None
    assert result.equity_curve.shape[0] == len(candles)


def test_run_simulation_dispatches_ema(pair_rules, engine_cfg, ema_config_with_regime):
    from pmm_lab.sim.runner_dispatch import run_simulation_cold

    ema_cfg, regime = ema_config_with_regime
    candles = _make_candles(n=300)
    result = run_simulation_cold(ema_cfg, pair_rules, candles,
                                  engine_config=engine_cfg,
                                  regime_candles=regime)
    assert result is not None
    assert result.equity_curve.shape[0] == len(candles)


def test_run_simulation_unknown_config_raises(pair_rules):
    from pmm_lab.sim.runner_dispatch import run_simulation

    class Unknown: pass

    with pytest.raises(TypeError, match="unsupported config type"):
        run_simulation(Unknown(), pair_rules, np.array([]), None)
