"""
GenericSimRunner — run any Strategy through SimEngine.

This is the strategy-generic equivalent of CandleSimRunner.
Use it when you want to run a non-PMM-Dynamic strategy through
the full pipeline (stress, walkforward, metrics).
"""

import numpy as np
from typing import Optional

from pmm_lab.config.params import PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.engine import SimEngine
from pmm_lab.sim.strategy import Strategy
from pmm_lab.sim.executor_model import SimResult


class GenericSimRunner:
    """Run any Strategy through SimEngine.

    Usage:
        runner = GenericSimRunner(engine_config, strategy, pair_rules)
        result = runner.run(candles)

    The runner exposes `.config` as an EngineConfig, which stress.py and
    walkforward.py can read for `total_amount_quote`, barrier params, etc.
    """

    def __init__(self, config: EngineConfig, strategy: Strategy, pair_rules: PairRules):
        self.config = config
        self.strategy = strategy
        self.pair_rules = pair_rules
        self._engine = SimEngine(config, pair_rules)

    def run(self, candles: np.ndarray, sim_start_idx: Optional[int] = None) -> SimResult:
        """Run a full backtest."""
        return self._engine.run(candles, self.strategy, sim_start_idx)
