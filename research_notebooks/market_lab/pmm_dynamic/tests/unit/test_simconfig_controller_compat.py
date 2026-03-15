"""Tests for controller_compat field in SimConfig."""

import pytest
from dataclasses import replace

from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.strategies.pmm_dynamic import PMMDynamicStrategy


class TestSimConfigControllerCompat:
    def test_simconfig_has_controller_compat(self):
        """SimConfig must have controller_compat field."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
        )
        assert hasattr(config, 'controller_compat')

    def test_simconfig_controller_compat_default_true(self):
        """Default is True for backward compatibility."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
        )
        assert config.controller_compat is True

    def test_simconfig_controller_compat_settable(self):
        """Can set controller_compat=False."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
            controller_compat=False,
        )
        assert config.controller_compat is False

    def test_simconfig_replace_controller_compat(self):
        """dataclasses.replace works for controller_compat."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
            controller_compat=True,
        )
        config2 = replace(config, controller_compat=False)
        assert config.controller_compat is True
        assert config2.controller_compat is False


class TestStrategyFromSimConfig:
    def test_from_sim_config_reads_controller_compat_true(self):
        """Strategy picks up controller_compat=True from SimConfig."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
            controller_compat=True,
        )
        strategy = PMMDynamicStrategy.from_sim_config(config)
        assert strategy.config.controller_compat is True

    def test_from_sim_config_reads_controller_compat_false(self):
        """Strategy picks up controller_compat=False from SimConfig."""
        config = SimConfig(
            buy_spreads=[1.0],
            sell_spreads=[1.0],
            buy_amounts_pct=[1.0],
            sell_amounts_pct=[1.0],
            controller_compat=False,
        )
        strategy = PMMDynamicStrategy.from_sim_config(config)
        assert strategy.config.controller_compat is False
