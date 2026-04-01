"""Tests for MACD-BB factory registration."""

import pytest

from pmm_lab.sim.strategy import Strategy
from pmm_lab.strategies.factory import create_strategy, available_strategies
from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig


class TestRegistration:
    def test_macd_bb_in_available(self):
        assert "macd_bb" in available_strategies()

    def test_create_macd_bb(self):
        strat = create_strategy("macd_bb", MACDBBStrategyConfig(
            bb_length=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9,
        ))
        assert isinstance(strat, MACDBBStrategy)

    def test_created_implements_protocol(self):
        strat = create_strategy("macd_bb", MACDBBStrategyConfig())
        assert isinstance(strat, Strategy)

    def test_unknown_strategy_raises(self):
        with pytest.raises(KeyError, match="nonexistent"):
            create_strategy("nonexistent", {})

    def test_existing_strategies_still_work(self):
        """PMM Dynamic and Bollinger must still be available."""
        avail = available_strategies()
        assert "pmm_dynamic" in avail
        assert "bollinger" in avail
