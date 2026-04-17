"""Regression: pre-existing strategies still registered and instantiable after Phase 1C."""

import pytest

from pmm_lab.strategies.factory import available_strategies, create_strategy


def test_pmm_dynamic_still_registered():
    assert "pmm_dynamic" in available_strategies()


def test_bollinger_still_registered():
    assert "bollinger" in available_strategies()


def test_macd_bb_still_registered():
    assert "macd_bb" in available_strategies()


def test_macd_bb_still_instantiable():
    from pmm_lab.strategies.macd_bb import MACDBBStrategy, MACDBBStrategyConfig
    strat = create_strategy("macd_bb", MACDBBStrategyConfig())
    assert isinstance(strat, MACDBBStrategy)


def test_bollinger_still_instantiable():
    from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig
    strat = create_strategy("bollinger", BollingerStrategyConfig())
    assert isinstance(strat, BollingerStrategy)
