"""
Strategy factory — create strategy instances by name.

Usage:
    strategy = create_strategy("pmm_dynamic", PMMDynamicStrategyConfig(...))
    strategy = create_strategy("bollinger", BollingerStrategyConfig(...))
"""

from typing import Any, Dict, Set

from pmm_lab.sim.strategy import Strategy


# Registry of known strategies
_STRATEGY_REGISTRY: Dict[str, type] = {}


def register_strategy(name: str, cls: type) -> None:
    """Register a strategy class under a name."""
    _STRATEGY_REGISTRY[name] = cls


def available_strategies() -> Set[str]:
    """Return names of all registered strategies."""
    return set(_STRATEGY_REGISTRY.keys())


def create_strategy(name: str, config: Any) -> Strategy:
    """Create a strategy instance by name.

    Parameters
    ----------
    name : str
        Registered strategy name (e.g., "pmm_dynamic", "bollinger").
    config : Any
        Strategy-specific configuration object.

    Returns
    -------
    Strategy

    Raises
    ------
    KeyError
        If strategy name is not registered.
    """
    if name not in _STRATEGY_REGISTRY:
        raise KeyError(
            f"Unknown strategy '{name}'. Available: {sorted(_STRATEGY_REGISTRY.keys())}"
        )
    cls = _STRATEGY_REGISTRY[name]
    return cls(config)


# Auto-register built-in strategies
def _register_builtins():
    from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy
    from pmm_lab.strategies.bollinger import BollingerStrategy
    from pmm_lab.strategies.macd_bb import MACDBBStrategy

    register_strategy("pmm_dynamic", PMMDynamicStrategy)
    register_strategy("bollinger", BollingerStrategy)
    register_strategy("macd_bb", MACDBBStrategy)


_register_builtins()
