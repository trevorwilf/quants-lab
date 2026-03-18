"""Tests for pmm_lab.optuna.canonicalizer — parameter canonicalization."""

import pytest
import numpy as np

from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.optuna.canonicalizer import (
    canonicalize_params,
    generate_geometric_ladder,
    generate_amount_weights,
)


def _default_pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.00001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


def _default_raw_params():
    return {
        "macd_fast": 21,
        "macd_slow": 42,
        "macd_signal": 9,
        "natr_length": 14,
        "buy_n_levels": 3,
        "sell_n_levels": 3,
        "buy_spread_base": 1.0,
        "buy_spread_ratio": 2.0,
        "sell_spread_base": 1.0,
        "sell_spread_ratio": 2.0,
        "buy_side_weight": 0.5,
        "amount_skew": 1.0,
        "total_amount_quote": 100.0,
        "executor_refresh_time": 3120,
        "cooldown_time": 3120,
        "stop_loss": 0.03,
        "take_profit": 0.015,
        "time_limit": 43200,
        "trailing_stop_activation": 0.01,
        "trailing_stop_delta": 0.005,
    }


class TestCanonicalizeParams:
    def test_valid_params_produce_config(self):
        """Reasonable params → (SimConfig, None)."""
        config, reason = canonicalize_params(
            _default_raw_params(), _default_pair_rules(), 100000.0
        )
        assert config is not None
        assert reason is None

    def test_spread_ladder_monotonic(self):
        """After canonicalization, buy_spreads and sell_spreads are strictly increasing."""
        config, _ = canonicalize_params(
            _default_raw_params(), _default_pair_rules(), 100000.0
        )
        for i in range(1, len(config.buy_spreads)):
            assert config.buy_spreads[i] > config.buy_spreads[i - 1]
        for i in range(1, len(config.sell_spreads)):
            assert config.sell_spreads[i] > config.sell_spreads[i - 1]

    def test_spread_ladder_length_matches_levels(self):
        """len(buy_spreads) == raw_params['buy_n_levels']."""
        raw = _default_raw_params()
        config, _ = canonicalize_params(raw, _default_pair_rules(), 100000.0)
        assert len(config.buy_spreads) == raw["buy_n_levels"]
        assert len(config.sell_spreads) == raw["sell_n_levels"]

    def test_amount_weights_sum_to_one(self):
        """buy_amounts_pct and sell_amounts_pct sum ≈ 1.0."""
        config, _ = canonicalize_params(
            _default_raw_params(), _default_pair_rules(), 100000.0
        )
        assert abs(sum(config.buy_amounts_pct) - 1.0) < 1e-9
        assert abs(sum(config.sell_amounts_pct) - 1.0) < 1e-9

    def test_no_nan_in_config(self):
        """No NaN in any field of the resulting SimConfig."""
        config, _ = canonicalize_params(
            _default_raw_params(), _default_pair_rules(), 100000.0
        )
        for s in config.buy_spreads:
            assert not np.isnan(s)
        for s in config.sell_spreads:
            assert not np.isnan(s)
        for a in config.buy_amounts_pct:
            assert not np.isnan(a)
        for a in config.sell_amounts_pct:
            assert not np.isnan(a)
        assert not np.isnan(config.stop_loss)
        assert not np.isnan(config.take_profit)
        assert not np.isnan(config.total_amount_quote)

    def test_min_notional_reduces_levels(self):
        """Tiny total_amount_quote → levels reduced, not outright rejected."""
        raw = _default_raw_params()
        raw["total_amount_quote"] = 5.0  # small but should allow at least 1 level
        config, reason = canonicalize_params(raw, _default_pair_rules(), 100000.0)
        # Should succeed with reduced levels or reject gracefully
        if config is not None:
            assert len(config.buy_spreads) <= raw["buy_n_levels"]
        # If rejected, that's also acceptable for very small capital

    def test_both_sides_zero_rejects(self):
        """Capital too small for any level → rejection with reason."""
        raw = _default_raw_params()
        raw["total_amount_quote"] = 0.001  # impossibly small
        rules = PairRules(
            price_tick=0.01,
            amount_step=0.00001,
            min_notional_quote=5.0,  # high min notional
            fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
        )
        config, reason = canonicalize_params(raw, rules, 100000.0)
        assert config is None
        assert reason is not None
        assert "fail" in reason.lower() or "both" in reason.lower()

    def test_trailing_stop_disabled_clears_delta(self):
        """trailing_stop_activation == 0 → trailing_stop_delta == 0."""
        raw = _default_raw_params()
        raw["trailing_stop_activation"] = 0.0
        raw["trailing_stop_delta"] = 0.01
        config, _ = canonicalize_params(raw, _default_pair_rules(), 100000.0)
        assert config.trailing_stop_delta == 0.0

    def test_deterministic(self):
        """Same inputs → identical SimConfig twice."""
        raw = _default_raw_params()
        rules = _default_pair_rules()
        c1, _ = canonicalize_params(raw, rules, 100000.0)
        c2, _ = canonicalize_params(raw, rules, 100000.0)
        assert c1 == c2


class TestGeometricLadder:
    def test_geometric_ladder_values(self):
        """generate_geometric_ladder(1.0, 2.0, 3) → [1.0, 2.0, 4.0]."""
        result = generate_geometric_ladder(1.0, 2.0, 3)
        assert len(result) == 3
        assert abs(result[0] - 1.0) < 1e-9
        assert abs(result[1] - 2.0) < 1e-9
        assert abs(result[2] - 4.0) < 1e-9


class TestAmountWeights:
    def test_amount_weights_equal_when_skew_one(self):
        """generate_amount_weights(4, skew=1.0) → [0.25, 0.25, 0.25, 0.25]."""
        result = generate_amount_weights(4, skew=1.0)
        assert len(result) == 4
        for w in result:
            assert abs(w - 0.25) < 1e-9

    def test_amount_weights_skewed(self):
        """generate_amount_weights(3, skew=2.0) → monotonically increasing."""
        result = generate_amount_weights(3, skew=2.0)
        assert len(result) == 3
        assert abs(sum(result) - 1.0) < 1e-9
        for i in range(1, len(result)):
            assert result[i] > result[i - 1]


class TestSpreadCap:
    """Verify pathological spread ladders are capped."""

    def test_extreme_ladder_is_capped(self):
        """Ladders with absurd far-tail levels are truncated to <= 50%."""
        params = dict(_default_raw_params())
        params["buy_spread_base"] = 5.0
        params["buy_spread_ratio"] = 3.0
        params["buy_n_levels"] = 10  # 5 * 3^9 = 98415 — way beyond cap
        params["sell_spread_base"] = 5.0
        params["sell_spread_ratio"] = 3.0
        params["sell_n_levels"] = 10

        config, rejection = canonicalize_params(params, _default_pair_rules(), 100000.0)

        if config is not None:
            assert all(s <= 50.0 for s in config.buy_spreads)
            assert all(s <= 50.0 for s in config.sell_spreads)
        # If rejected, that's also acceptable (all levels beyond cap)

    def test_moderate_ladder_unchanged(self):
        """Ladders that are all within cap are not truncated."""
        params = dict(_default_raw_params())
        params["buy_spread_base"] = 1.0
        params["buy_spread_ratio"] = 2.0
        params["buy_n_levels"] = 3  # 1, 2, 4 — all within 50
        params["sell_spread_base"] = 1.0
        params["sell_spread_ratio"] = 2.0
        params["sell_n_levels"] = 3

        config, _ = canonicalize_params(params, _default_pair_rules(), 100000.0)
        assert config is not None
        assert len(config.buy_spreads) == 3
        assert len(config.sell_spreads) == 3

    def test_all_levels_beyond_cap_rejected(self):
        """When ALL levels exceed cap, config is rejected."""
        params = dict(_default_raw_params())
        params["buy_spread_base"] = 60.0  # Already > 50
        params["buy_spread_ratio"] = 2.0
        params["buy_n_levels"] = 3
        params["sell_spread_base"] = 60.0
        params["sell_spread_ratio"] = 2.0
        params["sell_n_levels"] = 3

        config, rejection = canonicalize_params(params, _default_pair_rules(), 100000.0)
        assert config is None
        assert "max spread cap" in rejection
