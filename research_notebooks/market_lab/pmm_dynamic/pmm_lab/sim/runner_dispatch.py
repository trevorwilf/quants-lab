"""Runner dispatch — run a simulation for any supported strategy config type.

The validation helpers (holdout, recent_window, sensitivity, stress_selection)
are agnostic to the specific strategy; they receive a strategy config and a
set of signals, and call `run_simulation` to produce a `SimResult`. The
dispatch picks the right engine + strategy pair based on the config type.

Supported config types:
- `SimConfig` (PMM Dynamic / MACD-BB): uses `CandleSimRunner`. `engine_config`
  is ignored; all engine fields are embedded in the SimConfig.
- `MeanReversionBBRSIStrategyConfig`: requires `engine_config` (from the
  MR canonicalizer bundle); constructs `SimEngine` + `MeanReversionBBRSIStrategy`.
- `EMARegimeHoldStrategyConfig`: requires `engine_config`; regime_candles
  must already be attached on the config (the MR/EMA canonicalizers do this
  via `dataclasses.replace`). `SimEngine` + `EMARegimeHoldStrategy`.

Add new strategies by extending the dispatch in this file.
"""

from __future__ import annotations

import importlib.util
import logging
from typing import Any, Optional

import numpy as np

from pmm_lab.config.params import PairRules
from pmm_lab.sim.executor_model import SimConfig, SimResult

_logger = logging.getLogger(__name__)


def _module_is_installable(module_name: str) -> bool:
    """Return True if the module's top-level package is findable.

    Returns False ONLY when the module itself is missing — NOT when the module
    is present but raises ImportError due to a transitive dependency. This lets
    us distinguish "feature absent" (legitimate skip) from "feature broken"
    (must raise so the operator sees the real problem) in dispatch code.
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ImportError, ValueError):
        return False


def run_simulation(
    config: Any,
    pair_rules: PairRules,
    candles: np.ndarray,
    precomputed_signals,
    engine_config=None,
    sim_start_idx: Optional[int] = None,
    bar_index_offset: int = 0,
    regime_candles: Optional[np.ndarray] = None,
) -> SimResult:
    """Run a backtest with precomputed signals for any supported config type.

    Parameters
    ----------
    config : SimConfig | MeanReversionBBRSIStrategyConfig | EMARegimeHoldStrategyConfig
        Strategy configuration.
    pair_rules : PairRules
        Exchange rules.
    candles : np.ndarray
        Candle array to simulate on.
    precomputed_signals : SignalOutput
        Pre-computed signals (must cover `candles`).
    engine_config : EngineConfig, optional
        Required for MR/EMA configs (they separate strategy params from
        engine params). Ignored for SimConfig.
    sim_start_idx : int, optional
        Bar index where simulation starts.
    bar_index_offset : int
        Offset passed to run_with_signals (MR/EMA only; SimConfig path uses
        CandleSimRunner which does not expose this kwarg — pass 0).
    regime_candles : np.ndarray, optional
        For EMA only — if the caller wants to validate that the config's
        _regime_candles field is set. Not used to override.
    """
    if isinstance(config, SimConfig):
        from pmm_lab.sim.runner import CandleSimRunner
        runner = CandleSimRunner(config, pair_rules)
        return runner.run_with_signals(candles, precomputed_signals, sim_start_idx=sim_start_idx)

    if _module_is_installable("pmm_lab.strategies.mean_reversion_bb_rsi"):
        try:
            from pmm_lab.strategies.mean_reversion_bb_rsi import (
                MeanReversionBBRSIStrategy,
                MeanReversionBBRSIStrategyConfig,
            )
        except ImportError as e:
            raise ImportError(
                f"Directional MR module failed to import transitively: {e}. "
                f"Check pandas_ta / feature-engine dependencies."
            ) from e
        if isinstance(config, MeanReversionBBRSIStrategyConfig):
            if engine_config is None:
                raise ValueError(
                    "MR config requires engine_config to be passed to run_simulation "
                    "(MR separates strategy params from engine params — "
                    "the canonicalizer bundle has both; pass bundle.engine_config)."
                )
            from pmm_lab.sim.engine import SimEngine
            engine = SimEngine(engine_config, pair_rules)
            strategy = MeanReversionBBRSIStrategy(config)
            return engine.run_with_signals(
                candles, strategy, precomputed_signals,
                sim_start_idx=sim_start_idx, bar_index_offset=bar_index_offset,
            )

    if _module_is_installable("pmm_lab.strategies.range_ladder"):
        try:
            from pmm_lab.strategies.range_ladder import (
                RangeLadderConfig,
                run_range_ladder_window,
            )
        except ImportError as e:
            raise ImportError(
                f"range_ladder module failed to import transitively: {e}"
            ) from e
        if isinstance(config, RangeLadderConfig):
            if engine_config is None:
                raise ValueError(
                    "range_ladder config requires engine_config to be passed to "
                    "run_simulation (the canonicalizer bundle has both; pass "
                    "bundle.engine_config)."
                )
            # The ladder kernel ignores precomputed_signals (no indicator
            # signals); the anchor is derived from bars before sim_start_idx.
            return run_range_ladder_window(
                config, pair_rules, candles,
                sim_start_idx=sim_start_idx or 0,
            )

    if _module_is_installable("pmm_lab.strategies.ema_regime_hold"):
        try:
            from pmm_lab.strategies.ema_regime_hold import (
                EMARegimeHoldStrategy,
                EMARegimeHoldStrategyConfig,
            )
        except ImportError as e:
            raise ImportError(
                f"Directional EMA module failed to import transitively: {e}. "
                f"Check pandas_ta / feature-engine dependencies."
            ) from e
        if isinstance(config, EMARegimeHoldStrategyConfig):
            if engine_config is None:
                raise ValueError(
                    "EMA config requires engine_config to be passed to run_simulation."
                )
            if config._regime_candles is None:
                raise ValueError(
                    "EMA config._regime_candles is None. The canonicalizer must attach "
                    "regime_candles before calling run_simulation."
                )
            from pmm_lab.sim.engine import SimEngine
            engine = SimEngine(engine_config, pair_rules)
            strategy = EMARegimeHoldStrategy(config)
            return engine.run_with_signals(
                candles, strategy, precomputed_signals,
                sim_start_idx=sim_start_idx, bar_index_offset=bar_index_offset,
            )

    raise TypeError(
        f"run_simulation: unsupported config type {type(config).__name__}. "
        f"Add a branch in runner_dispatch.py."
    )


def run_simulation_cold(
    config: Any,
    pair_rules: PairRules,
    candles: np.ndarray,
    engine_config=None,
    regime_candles: Optional[np.ndarray] = None,
) -> SimResult:
    """Cold-start simulation (compute signals internally). Delegates to run_simulation."""
    if isinstance(config, SimConfig):
        from pmm_lab.sim.runner import CandleSimRunner
        return CandleSimRunner(config, pair_rules).run(candles)

    # For MR/EMA we need to compute signals ourselves then call run_simulation.
    if _module_is_installable("pmm_lab.strategies.mean_reversion_bb_rsi"):
        try:
            from pmm_lab.strategies.mean_reversion_bb_rsi import (
                MeanReversionBBRSIStrategy, MeanReversionBBRSIStrategyConfig,
            )
        except ImportError as e:
            raise ImportError(
                f"Directional MR module failed to import transitively: {e}"
            ) from e
        if isinstance(config, MeanReversionBBRSIStrategyConfig):
            strategy = MeanReversionBBRSIStrategy(config)
            signals = strategy.compute_signals(candles)
            return run_simulation(config, pair_rules, candles, signals,
                                  engine_config=engine_config)

    if _module_is_installable("pmm_lab.strategies.ema_regime_hold"):
        try:
            from pmm_lab.strategies.ema_regime_hold import (
                EMARegimeHoldStrategy, EMARegimeHoldStrategyConfig,
            )
        except ImportError as e:
            raise ImportError(
                f"Directional EMA module failed to import transitively: {e}"
            ) from e
        if isinstance(config, EMARegimeHoldStrategyConfig):
            strategy = EMARegimeHoldStrategy(config)
            signals = strategy.compute_signals(candles)
            return run_simulation(config, pair_rules, candles, signals,
                                  engine_config=engine_config,
                                  regime_candles=regime_candles)

    raise TypeError(
        f"run_simulation_cold: unsupported config type {type(config).__name__}"
    )
