"""End-of-backtest forced exits must be labeled as final_liquidation, not time_limit."""
import numpy as np
import pytest

from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy, PMMDynamicStrategyConfig
from pmm_lab.config.params import PairRules, FeeConfig
from tests.conftest import _make_sample_candles_500


def _make_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _make_strategy():
    return PMMDynamicStrategy(PMMDynamicStrategyConfig(
        buy_spreads=(1.0, 2.0),
        sell_spreads=(1.0, 2.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


def test_force_close_exit_type_is_final_liquidation():
    """Trades force-closed at end of backtest must have exit_type='final_liquidation'."""
    candles = _make_sample_candles_500()
    # Use a very long time_limit so no trades exit via normal time_limit
    config = EngineConfig(time_limit=999999999)
    engine = SimEngine(config, _make_pair_rules())
    result = engine.run(candles, _make_strategy())

    # Find trades that were force-closed (exit at the last bar)
    last_bar = len(candles) - 1
    force_closed = [t for t in result.trades if t.exit_bar == last_bar and t.exit_type is not None]

    for t in force_closed:
        assert t.exit_type == "final_liquidation", (
            f"Trade {t.trade_id} force-closed at bar {last_bar} should have "
            f"exit_type='final_liquidation', got '{t.exit_type}'"
        )


def test_normal_time_limit_still_works():
    """Trades that hit time_limit during simulation should still be labeled 'time_limit'."""
    candles = _make_sample_candles_500()
    # Use a short time_limit to trigger normal time exits
    config = EngineConfig(time_limit=600)  # 10 minutes
    engine = SimEngine(config, _make_pair_rules())
    result = engine.run(candles, _make_strategy())

    # Normal time-limit exits should not be at the last bar
    last_bar = len(candles) - 1
    time_exits = [t for t in result.trades if t.exit_type == "time_limit"]
    for t in time_exits:
        assert t.exit_bar < last_bar, (
            f"Normal time_limit exit at last bar — should be final_liquidation"
        )
