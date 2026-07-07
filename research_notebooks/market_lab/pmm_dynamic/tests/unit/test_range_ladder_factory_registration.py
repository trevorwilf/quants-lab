"""Factory registration for range_ladder."""

from pmm_lab.strategies.factory import available_strategies, create_strategy
from pmm_lab.strategies.range_ladder import RangeLadderConfig, RangeLadderStrategy


def test_registered_name_present():
    assert "range_ladder" in available_strategies()


def test_create_returns_instance():
    strat = create_strategy("range_ladder", RangeLadderConfig())
    assert isinstance(strat, RangeLadderStrategy)


def test_lazy_package_exports():
    import pmm_lab.strategies as strategies
    assert strategies.RangeLadderStrategy is RangeLadderStrategy
    assert strategies.RangeLadderConfig is RangeLadderConfig
