"""Holdout validation must always describe the exported config — and each
candidate must be scored with its OWN engine_config for MR/EMA.

Stage 1 of the efficiency fixes adds `HoldoutCandidateSpec` so directional
strategies don't silently reuse the winner's execution params for every
holdout candidate.
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

import numpy as np
import pytest


# ────────────────────────────────────────────────────────────────────────────
# Structural guarantee (pre-existing; kept)
# ────────────────────────────────────────────────────────────────────────────

def test_holdout_evaluates_exported_config_first():
    """The first candidate in holdout evaluation must be the exported config.

    The PMM deploy pipeline still constructs this via 2-tuples, so the existing
    structural test substring stays. The directional notebooks use
    HoldoutCandidateSpec — verified in their own tests below.
    """
    import inspect
    from pmm_lab.deploy.runner import run_full_pipeline
    source = inspect.getsource(run_full_pipeline)
    assert "holdout_candidates = [(val_config," in source, (
        "PMM pipeline must construct holdout_candidates with val_config as first element"
    )
    assert "holdout_report.candidates[0]" in source, (
        "Pipeline must reference candidates[0] for package metadata"
    )


# ────────────────────────────────────────────────────────────────────────────
# Helpers for the per-candidate engine-config tests
# ────────────────────────────────────────────────────────────────────────────

def _pair_rules():
    from pmm_lab.config.params import FeeConfig, PairRules
    return PairRules(
        price_tick=0.01, amount_step=0.0001, min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _make_candles(n: int = 800, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    from tests.conftest import CANDLE_DTYPE
    rows = []
    ts = 1_700_000_000
    price = 100.0
    for i in range(n):
        ch = rng.normal(0, 0.5)
        op = price
        cl = op + ch
        hi = max(op, cl) + abs(rng.normal(0, 0.2))
        lo = min(op, cl) - abs(rng.normal(0, 0.2))
        hi = max(hi, max(op, cl))
        lo = max(lo, 0.01)
        lo = min(lo, min(op, cl))
        rows.append((ts + i * 300, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _make_regime(n: int = 200, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    from tests.conftest import CANDLE_DTYPE
    rows = []
    ts = 1_700_000_000
    price = 100.0
    for i in range(n):
        ch = rng.normal(0, 1.0)
        op = price
        cl = op + ch
        hi = max(op, cl) + abs(rng.normal(0, 0.5))
        lo = min(op, cl) - abs(rng.normal(0, 0.5))
        hi = max(hi, max(op, cl))
        lo = max(lo, 0.01)
        lo = min(lo, min(op, cl))
        rows.append((ts + i * 28800, op, hi, lo, cl, rng.uniform(0.5, 3.0), False))
        price = cl
    return np.array(rows, dtype=CANDLE_DTYPE)


def _pmm_config(total=100.0):
    from pmm_lab.sim.executor_model import SimConfig
    return SimConfig(
        buy_spreads=[0.002], sell_spreads=[0.002],
        buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        total_amount_quote=total,
        controller_compat=False,
    )


def _mr_bundle(total=100.0):
    from pmm_lab.optuna.canonicalizer_mean_reversion_bb_rsi import canonicalize_mr_bb_rsi_params
    raw = {
        "bb_length": 20, "bb_std": 2.0, "bbp_entry_threshold": 0.15,
        "rsi_length": 14, "rsi_entry_threshold": 35.0,
        "use_trend_filter": False, "trend_ema_length": 50,
        "atr_length": 14, "max_atr_pct_for_entry": 0.10,
        "volume_filter_window": 30, "min_volume_quantile": 0.0,
        "cooldown_time": 300, "stop_loss": 0.04, "take_profit": 0.02,
        "time_limit": 86400, "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
        "max_spread_pct": 0.006, "max_trades_per_day": 6,
        "max_executors_per_side": 1, "total_amount_quote": total,
        "min_trend_slope": 0.0,
    }
    bundle, reject = canonicalize_mr_bb_rsi_params(raw, _pair_rules(), 100.0, bar_interval_seconds=300)
    assert bundle is not None, f"canonicalize rejected: {reject}"
    return bundle


def _ema_bundle(total=100.0, regime=None):
    from pmm_lab.optuna.canonicalizer_ema_regime_hold import canonicalize_ema_regime_hold_params
    raw = {
        "regime_ema_fast": 10, "regime_ema_slow": 30,
        "regime_adx_length": 14, "regime_adx_threshold": 20.0,
        "volume_filter_window": 30, "min_volume_quantile": 0.0,
        "hold_mode": "reentry",
        "cooldown_time": 300, "stop_loss": 0.04, "take_profit": 0.02,
        "time_limit": 86400, "take_profit_order_type": "LIMIT",
        "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
        "max_executors_per_side": 1, "total_amount_quote": total,
    }
    bundle, reject = canonicalize_ema_regime_hold_params(
        raw, _pair_rules(), 100.0,
        signal_interval_seconds=300,
        regime_candles=regime,
    )
    assert bundle is not None, f"canonicalize rejected: {reject}"
    return bundle


# ────────────────────────────────────────────────────────────────────────────
# The five mandatory Stage 1 tests
# ────────────────────────────────────────────────────────────────────────────

def test_holdout_accepts_legacy_tuple_inputs_unchanged():
    """Two (cfg, score) tuples must still work; the function-level engine_config
    kwarg is used for every candidate (legacy PMM behavior)."""
    from pmm_lab.objective.holdout import evaluate_holdout

    pmm_a = _pmm_config(total=111.0)
    pmm_b = _pmm_config(total=222.0)
    candles = _make_candles(400)

    seen_engine_configs = []

    def _rec_sim(config, pair_rules, candles_, precomputed_signals, **kw):
        from pmm_lab.sim.executor_model import SimResult
        seen_engine_configs.append(kw.get("engine_config"))
        n = len(candles_)
        return SimResult(
            trades=[],
            equity_curve=np.full(n, 100.0),
            position_history=np.zeros(n),
            n_orders_placed=0, n_orders_filled=0,
            n_orders_rejected=0, n_market_exits=0,
            final_base_balance=0.0, final_quote_balance=100.0,
        )

    with patch("pmm_lab.objective.holdout.run_simulation", side_effect=_rec_sim), \
         patch("pmm_lab.objective.holdout.run_simulation_cold", side_effect=_rec_sim):
        evaluate_holdout(
            holdout_candles=candles[-100:],
            candidate_configs=[(pmm_a, 0.1), (pmm_b, 0.2)],
            pair_rules=_pair_rules(), bar_interval_seconds=300,
            run_stress=False, objective_version=2,
            full_candles=candles, holdout_start_idx=300,
            engine_config="fallback_ec",
        )

    assert len(seen_engine_configs) == 2
    # Legacy tuple path: both calls get the function-level engine_config
    assert seen_engine_configs[0] == "fallback_ec"
    assert seen_engine_configs[1] == "fallback_ec"


def test_holdout_accepts_holdout_candidate_spec_inputs():
    """HoldoutCandidateSpec with different engine_configs must produce different
    engine_config arguments on each run_simulation call."""
    from pmm_lab.objective.holdout import evaluate_holdout, HoldoutCandidateSpec

    cfg = _pmm_config()
    candles = _make_candles(400)

    seen = []

    def _rec_sim(config, pair_rules, candles_, precomputed_signals, **kw):
        from pmm_lab.sim.executor_model import SimResult
        seen.append(kw.get("engine_config"))
        n = len(candles_)
        return SimResult(
            trades=[], equity_curve=np.full(n, 100.0),
            position_history=np.zeros(n),
            n_orders_placed=0, n_orders_filled=0,
            n_orders_rejected=0, n_market_exits=0,
            final_base_balance=0.0, final_quote_balance=100.0,
        )

    specs = [
        HoldoutCandidateSpec(strategy_config=cfg, engine_config="ec_0",
                             development_score=0.1),
        HoldoutCandidateSpec(strategy_config=cfg, engine_config="ec_1",
                             development_score=0.2),
    ]
    with patch("pmm_lab.objective.holdout.run_simulation", side_effect=_rec_sim), \
         patch("pmm_lab.objective.holdout.run_simulation_cold", side_effect=_rec_sim):
        evaluate_holdout(
            holdout_candles=candles[-100:], candidate_configs=specs,
            pair_rules=_pair_rules(), bar_interval_seconds=300,
            run_stress=False, objective_version=2,
            full_candles=candles, holdout_start_idx=300,
            engine_config="fallback_ec",
        )

    assert seen == ["ec_0", "ec_1"], (
        f"Each spec's engine_config must be used; got {seen}"
    )


def test_holdout_spec_engine_config_none_falls_back_to_kwarg():
    """A spec with engine_config=None must fall back to the function-level
    engine_config kwarg (supports PMM SimConfig which has no separate
    engine_config)."""
    from pmm_lab.objective.holdout import evaluate_holdout, HoldoutCandidateSpec

    cfg = _pmm_config()
    candles = _make_candles(400)
    seen = []

    def _rec_sim(config, pair_rules, candles_, precomputed_signals, **kw):
        from pmm_lab.sim.executor_model import SimResult
        seen.append(kw.get("engine_config"))
        n = len(candles_)
        return SimResult(
            trades=[], equity_curve=np.full(n, 100.0),
            position_history=np.zeros(n),
            n_orders_placed=0, n_orders_filled=0,
            n_orders_rejected=0, n_market_exits=0,
            final_base_balance=0.0, final_quote_balance=100.0,
        )

    specs = [
        HoldoutCandidateSpec(strategy_config=cfg, engine_config=None,
                             development_score=0.5),
    ]
    with patch("pmm_lab.objective.holdout.run_simulation", side_effect=_rec_sim), \
         patch("pmm_lab.objective.holdout.run_simulation_cold", side_effect=_rec_sim):
        evaluate_holdout(
            holdout_candles=candles[-100:], candidate_configs=specs,
            pair_rules=_pair_rules(), bar_interval_seconds=300,
            run_stress=False, objective_version=2,
            full_candles=candles, holdout_start_idx=300,
            engine_config="fallback_ec",
        )

    assert seen == ["fallback_ec"]


def test_holdout_directional_mr_uses_per_candidate_engine_config():
    """With real MR configs and two specs whose engine_config.total_amount_quote
    differ, each run_simulation call receives the candidate's own engine_config."""
    from pmm_lab.objective.holdout import evaluate_holdout, HoldoutCandidateSpec

    b_a = _mr_bundle(total=100.0)
    b_b = _mr_bundle(total=500.0)
    assert b_a.engine_config.total_amount_quote != b_b.engine_config.total_amount_quote

    candles = _make_candles(800)
    seen_quote = []

    def _rec_sim(config, pair_rules, candles_, precomputed_signals, **kw):
        from pmm_lab.sim.executor_model import SimResult
        ec = kw.get("engine_config")
        seen_quote.append(ec.total_amount_quote if ec is not None else None)
        n = len(candles_)
        return SimResult(
            trades=[], equity_curve=np.full(n, 100.0),
            position_history=np.zeros(n),
            n_orders_placed=0, n_orders_filled=0,
            n_orders_rejected=0, n_market_exits=0,
            final_base_balance=0.0, final_quote_balance=100.0,
        )

    specs = [
        HoldoutCandidateSpec(
            strategy_config=b_a.strategy_config,
            engine_config=b_a.engine_config,
            development_score=0.1,
        ),
        HoldoutCandidateSpec(
            strategy_config=b_b.strategy_config,
            engine_config=b_b.engine_config,
            development_score=0.2,
        ),
    ]
    with patch("pmm_lab.objective.holdout.run_simulation", side_effect=_rec_sim), \
         patch("pmm_lab.objective.holdout.run_simulation_cold", side_effect=_rec_sim):
        evaluate_holdout(
            holdout_candles=candles[-100:], candidate_configs=specs,
            pair_rules=_pair_rules(), bar_interval_seconds=300,
            run_stress=False, objective_version=2,
            full_candles=candles, holdout_start_idx=600,
        )

    assert seen_quote == [100.0, 500.0], (
        f"Each MR candidate must use its own engine_config.total_amount_quote; got {seen_quote}"
    )


def test_holdout_directional_ema_uses_per_candidate_engine_config():
    """Same as MR but for EMA regime-hold with regime_candles threaded through."""
    from pmm_lab.objective.holdout import evaluate_holdout, HoldoutCandidateSpec

    regime = _make_regime(200)
    b_a = _ema_bundle(total=100.0, regime=regime)
    b_b = _ema_bundle(total=500.0, regime=regime)
    assert b_a.engine_config.total_amount_quote != b_b.engine_config.total_amount_quote

    candles = _make_candles(800)
    seen_quote = []

    def _rec_sim(config, pair_rules, candles_, precomputed_signals, **kw):
        from pmm_lab.sim.executor_model import SimResult
        ec = kw.get("engine_config")
        seen_quote.append(ec.total_amount_quote if ec is not None else None)
        n = len(candles_)
        return SimResult(
            trades=[], equity_curve=np.full(n, 100.0),
            position_history=np.zeros(n),
            n_orders_placed=0, n_orders_filled=0,
            n_orders_rejected=0, n_market_exits=0,
            final_base_balance=0.0, final_quote_balance=100.0,
        )

    specs = [
        HoldoutCandidateSpec(
            strategy_config=b_a.strategy_config,
            engine_config=b_a.engine_config,
            development_score=0.1,
        ),
        HoldoutCandidateSpec(
            strategy_config=b_b.strategy_config,
            engine_config=b_b.engine_config,
            development_score=0.2,
        ),
    ]
    with patch("pmm_lab.objective.holdout.run_simulation", side_effect=_rec_sim), \
         patch("pmm_lab.objective.holdout.run_simulation_cold", side_effect=_rec_sim):
        evaluate_holdout(
            holdout_candles=candles[-100:], candidate_configs=specs,
            pair_rules=_pair_rules(), bar_interval_seconds=300,
            run_stress=False, objective_version=2,
            full_candles=candles, holdout_start_idx=600,
            regime_candles=regime,
        )

    assert seen_quote == [100.0, 500.0]
