"""Factory registration: ema_regime_hold."""

from pmm_lab.strategies.factory import available_strategies, create_strategy
from pmm_lab.strategies.ema_regime_hold import (
    EMARegimeHoldStrategy,
    EMARegimeHoldStrategyConfig,
)


def test_registered_name_present():
    assert "ema_regime_hold" in available_strategies()


def test_create_returns_instance():
    strat = create_strategy("ema_regime_hold", EMARegimeHoldStrategyConfig())
    assert isinstance(strat, EMARegimeHoldStrategy)
