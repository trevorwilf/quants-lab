"""Tests for BollingerStrategy."""

import numpy as np
import math
import pytest

from pmm_lab.sim.strategy import Strategy, SignalOutput
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.config.params import PairRules, FeeConfig
from pmm_lab.strategies.bollinger import BollingerStrategy, BollingerStrategyConfig

from tests.conftest import CANDLE_DTYPE


@pytest.fixture
def bollinger_strategy():
    return BollingerStrategy(BollingerStrategyConfig(
        bb_window=20,
        bb_stdev=2.0,
        buy_spreads=(0.5, 1.0),
        sell_spreads=(0.5, 1.0),
        buy_amounts_pct=(0.5, 0.5),
        sell_amounts_pct=(0.5, 0.5),
    ))


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0)


# ── Signal computation tests ──────────────────────────────────────


class TestBollingerProtocol:
    def test_bollinger_implements_strategy(self, bollinger_strategy):
        assert isinstance(bollinger_strategy, Strategy)


class TestBollingerSignals:
    def test_compute_signals_returns_signal_output(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        assert isinstance(result, SignalOutput)

    def test_compute_signals_has_required_keys(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        for key in ("reference_price", "spread_multiplier", "upper_band", "lower_band", "sma"):
            assert key in result.data, f"Missing key: {key}"

    def test_compute_signals_warmup_end(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        # bb_window=20, open mode -> warmup_end = 20 + 1 = 21
        assert result.warmup_end == 21

    def test_signals_causal_no_lookahead(self, sample_candles_5m, bollinger_strategy):
        """Signals at bar 49 should be identical whether computed on 50 or 100 candles."""
        signals_short = bollinger_strategy.compute_signals(sample_candles_5m[:50])
        signals_full = bollinger_strategy.compute_signals(sample_candles_5m)

        bar = 49
        for key in ("reference_price", "spread_multiplier"):
            val_short = signals_short.get(key, bar)
            val_full = signals_full.get(key, bar)
            if not math.isnan(val_short):
                assert abs(val_short - val_full) < 1e-10, (
                    f"{key} at bar {bar}: short={val_short}, full={val_full}"
                )

    def test_spread_multiplier_is_band_width_fraction(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        bar = result.warmup_end + 5
        upper = result.get("upper_band", bar)
        lower = result.get("lower_band", bar)
        sma_val = result.get("sma", bar)
        sm = result.get("spread_multiplier", bar)

        if not math.isnan(sma_val) and sma_val > 0:
            expected = (upper - lower) / sma_val
            assert abs(sm - expected) < 1e-10

    def test_reference_price_is_sma(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        bar = result.warmup_end + 5
        ref = result.get("reference_price", bar)
        sma_val = result.get("sma", bar)
        if not math.isnan(sma_val):
            assert abs(ref - sma_val) < 1e-10

    def test_upper_above_lower(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        for bar in range(result.warmup_end, len(sample_candles_5m)):
            upper = result.get("upper_band", bar)
            lower = result.get("lower_band", bar)
            if not math.isnan(upper):
                assert upper > lower, f"Bar {bar}: upper={upper} <= lower={lower}"

    def test_nan_before_warmup(self, sample_candles_5m, bollinger_strategy):
        result = bollinger_strategy.compute_signals(sample_candles_5m)
        # Bars well before warmup should be NaN. The boundary bar (warmup_end - 1)
        # may or may not be NaN depending on exact computation, but early bars must be.
        for bar in range(min(result.warmup_end - 1, 10)):
            ref = result.get("reference_price", bar)
            sm = result.get("spread_multiplier", bar)
            assert math.isnan(ref) or math.isnan(sm), (
                f"Bar {bar} (well before warmup {result.warmup_end}) has valid signals"
            )


# ── Order building tests ──────────────────────────────────────────


class TestBollingerOrders:
    def test_build_orders_returns_tuple(
        self, sample_candles_5m, bollinger_strategy, engine_config, default_pair_rules
    ):
        signals = bollinger_strategy.compute_signals(sample_candles_5m)
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        result = bollinger_strategy.build_orders(
            signals.warmup_end, signals, engine_config, default_pair_rules, inventory
        )
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_build_orders_buy_and_sell(
        self, sample_candles_5m, bollinger_strategy, engine_config, default_pair_rules
    ):
        signals = bollinger_strategy.compute_signals(sample_candles_5m)
        inventory = Inventory(base_balance=0.001, quote_balance=100.0)
        orders, placed, rejected = bollinger_strategy.build_orders(
            signals.warmup_end, signals, engine_config, default_pair_rules, inventory
        )
        buy_orders = [o for o in orders if o.side == "buy"]
        sell_orders = [o for o in orders if o.side == "sell"]
        assert len(buy_orders) > 0

    def test_build_orders_spot_constraint_no_base(
        self, sample_candles_5m, bollinger_strategy, engine_config, default_pair_rules
    ):
        signals = bollinger_strategy.compute_signals(sample_candles_5m)
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = bollinger_strategy.build_orders(
            signals.warmup_end, signals, engine_config, default_pair_rules, inventory
        )
        sell_orders = [o for o in orders if o.side == "sell"]
        assert len(sell_orders) == 0

    def test_build_orders_nan_signals_empty(self, bollinger_strategy, engine_config, default_pair_rules):
        signals = SignalOutput(
            warmup_end=0,
            data={
                "reference_price": np.array([np.nan]),
                "spread_multiplier": np.array([np.nan]),
            },
        )
        inventory = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = bollinger_strategy.build_orders(
            0, signals, engine_config, default_pair_rules, inventory
        )
        assert orders == []
        assert placed == 0

    def test_build_orders_prices_bracket_sma(
        self, sample_candles_5m, bollinger_strategy, engine_config, default_pair_rules
    ):
        signals = bollinger_strategy.compute_signals(sample_candles_5m)
        bar = signals.warmup_end
        inventory = Inventory(base_balance=0.001, quote_balance=100.0)
        orders, placed, rejected = bollinger_strategy.build_orders(
            bar, signals, engine_config, default_pair_rules, inventory
        )
        ref = signals.get("reference_price", bar)
        buy_orders = [o for o in orders if o.side == "buy"]
        sell_orders = [o for o in orders if o.side == "sell"]
        for o in buy_orders:
            assert o.price < ref, f"Buy price {o.price} >= ref {ref}"
        for o in sell_orders:
            assert o.price > ref, f"Sell price {o.price} <= ref {ref}"
