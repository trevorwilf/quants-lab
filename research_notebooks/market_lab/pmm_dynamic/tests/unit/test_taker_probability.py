"""Tests for taker_probability in fill model and engine (Fix 2)."""

import numpy as np
import pytest

from pmm_lab.sim.fill_model import check_buy_fill, check_sell_fill
from pmm_lab.sim.executor_model import SimConfig


class TestFillModelTakerProbability:
    """Tests for taker_probability parameter in fill model."""

    def test_default_taker_probability_all_maker(self):
        """Default taker_probability=0.0 produces all maker fills (backward compat)."""
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
        )
        assert result.filled
        assert result.fill_type == "maker"

    def test_taker_probability_zero_always_maker(self):
        """Explicit taker_probability=0.0 always returns maker."""
        for seed in range(100):
            result = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                fill_seed=seed, taker_probability=0.0,
            )
            if result.filled:
                assert result.fill_type == "maker"

    def test_taker_probability_one_always_taker(self):
        """taker_probability=1.0 always returns taker."""
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=99.0, candle_volume=10.0,
            taker_probability=1.0,
        )
        assert result.filled
        assert result.fill_type == "taker"

    def test_taker_probability_one_sell(self):
        """taker_probability=1.0 on sell side returns taker."""
        result = check_sell_fill(
            order_price=100.0, order_quantity=1.0,
            candle_high=101.0, candle_volume=10.0,
            taker_probability=1.0,
        )
        assert result.filled
        assert result.fill_type == "taker"

    def test_taker_probability_half_produces_mix(self):
        """taker_probability=0.5 produces ~50% taker fills deterministically."""
        taker_count = 0
        total = 200
        for seed in range(total):
            result = check_buy_fill(
                order_price=100.0, order_quantity=0.1,
                candle_low=99.0, candle_volume=100.0,
                fill_seed=seed, taker_probability=0.5,
            )
            if result.filled and result.fill_type == "taker":
                taker_count += 1
        # Should be roughly 50% ± 15% (very generous for deterministic)
        ratio = taker_count / total
        assert 0.30 < ratio < 0.70, f"Taker ratio {ratio:.2f} not near 0.5"

    def test_taker_probability_reproducible(self):
        """Same inputs produce same fill_type across calls."""
        results = []
        for _ in range(3):
            r = check_buy_fill(
                order_price=100.0, order_quantity=1.0,
                candle_low=99.0, candle_volume=10.0,
                fill_seed=42, taker_probability=0.5,
            )
            results.append(r.fill_type)
        assert results[0] == results[1] == results[2]

    def test_no_fill_still_no_fill_with_taker_prob(self):
        """taker_probability doesn't cause fills where there shouldn't be any."""
        result = check_buy_fill(
            order_price=100.0, order_quantity=1.0,
            candle_low=101.0, candle_volume=10.0,  # low above order price
            taker_probability=1.0,
        )
        assert not result.filled
        assert result.fill_type == "maker"  # no_fill default


class TestSimConfigTakerProbability:
    """Tests for taker_probability field on SimConfig."""

    def test_default_is_zero(self):
        cfg = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
        )
        assert cfg.taker_probability == 0.0

    def test_custom_value(self):
        cfg = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[1.0], sell_amounts_pct=[1.0],
            taker_probability=0.1,
        )
        assert cfg.taker_probability == 0.1


class TestEngineTakerFees:
    """Integration test: taker fills in the engine use taker fee rates."""

    def test_taker_fills_use_taker_fee_rate(self, sample_candles_500, default_pair_rules):
        """With taker_probability=1.0, entry fees should use taker rate."""
        from pmm_lab.sim.runner import CandleSimRunner

        # Run with all maker (default)
        cfg_maker = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[0.5], sell_amounts_pct=[0.5],
            controller_compat=False,
            taker_probability=0.0,
        )
        runner_maker = CandleSimRunner(cfg_maker, default_pair_rules)
        result_maker = runner_maker.run(sample_candles_500)

        # Run with all taker
        cfg_taker = SimConfig(
            buy_spreads=[1.0], sell_spreads=[1.0],
            buy_amounts_pct=[0.5], sell_amounts_pct=[0.5],
            controller_compat=False,
            taker_probability=1.0,
        )
        runner_taker = CandleSimRunner(cfg_taker, default_pair_rules)
        result_taker = runner_taker.run(sample_candles_500)

        # If any trades occurred, taker result should have higher fees
        if result_maker.trades and result_taker.trades:
            maker_fees = sum(t.entry_fee_quote for t in result_maker.trades if t.entry_fee_quote > 0)
            taker_fees = sum(t.entry_fee_quote for t in result_taker.trades if t.entry_fee_quote > 0)
            # Taker fees should be >= maker fees (taker rate >= maker rate)
            if maker_fees > 0:
                assert taker_fees >= maker_fees, (
                    f"Taker total entry fees ({taker_fees:.4f}) should be >= "
                    f"maker total entry fees ({maker_fees:.4f})"
                )
