"""Factory registration: mean_reversion_bb_rsi."""

from pmm_lab.strategies.factory import available_strategies, create_strategy
from pmm_lab.strategies.mean_reversion_bb_rsi import (
    MeanReversionBBRSIStrategy,
    MeanReversionBBRSIStrategyConfig,
)


def test_registered_name_present():
    assert "mean_reversion_bb_rsi" in available_strategies()


def test_create_returns_instance():
    strat = create_strategy("mean_reversion_bb_rsi", MeanReversionBBRSIStrategyConfig())
    assert isinstance(strat, MeanReversionBBRSIStrategy)
