"""
CandleSimRunner — backward-compatible wrapper over SimEngine + PMMDynamicStrategy.

v1 code that uses CandleSimRunner(config, pair_rules).run(candles) continues
to work unchanged. Internally, it delegates to the generic SimEngine.
"""

import numpy as np
from typing import Optional

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy


def _sim_config_to_engine_config(sc: SimConfig) -> EngineConfig:
    """Extract generic EngineConfig from a PMM Dynamic SimConfig."""
    return EngineConfig(
        total_amount_quote=sc.total_amount_quote,
        buy_side_weight=sc.buy_side_weight,
        executor_refresh_time=sc.executor_refresh_time,
        cooldown_time=sc.cooldown_time,
        stop_loss=sc.stop_loss,
        take_profit=sc.take_profit,
        time_limit=sc.time_limit,
        take_profit_order_type=sc.take_profit_order_type,
        trailing_stop_activation=sc.trailing_stop_activation,
        trailing_stop_delta=sc.trailing_stop_delta,
        fill_participation_rate=sc.fill_participation_rate,
        latency_bars=sc.latency_bars,
        slippage_bps=sc.slippage_bps,
        initial_base_pct=getattr(sc, 'initial_base_pct', 0.0),
        position_rebalance_threshold_pct=getattr(sc, 'position_rebalance_threshold_pct', 0.0),
        skip_rebalance=getattr(sc, 'skip_rebalance', True),
        touch_through=getattr(sc, 'touch_through', False),
        entry_spread_bps=getattr(sc, 'entry_spread_bps', 0.0),
        maker_fill_probability=getattr(sc, 'maker_fill_probability', 1.0),
        split_volume_by_side=getattr(sc, 'split_volume_by_side', False),
        buy_volume_fraction=getattr(sc, 'buy_volume_fraction', 0.5),
        volume_is_base=getattr(sc, 'volume_is_base', True),
    )


class CandleSimRunner:
    """Backward-compatible PMM Dynamic simulator.

    Delegates to SimEngine + PMMDynamicStrategy. Existing code that uses
    CandleSimRunner(config, pair_rules).run(candles) works unchanged.

    Usage:
        runner = CandleSimRunner(sim_config, pair_rules)
        result = runner.run(candles)
    """

    def __init__(self, config: SimConfig, pair_rules: PairRules):
        self.config = config
        self.pair_rules = pair_rules
        self._engine_config = _sim_config_to_engine_config(config)
        self._strategy = PMMDynamicStrategy.from_sim_config(config)
        self._engine = SimEngine(self._engine_config, pair_rules)

    def run(self, candles: np.ndarray, sim_start_idx: Optional[int] = None) -> SimResult:
        """Run a full backtest. Delegates to SimEngine."""
        return self._engine.run(candles, self._strategy, sim_start_idx)
