"""Tests for MeanReversionBBRSIStrategy."""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.sim.engine_config import EngineConfig
from pmm_lab.sim.inventory import Inventory
from pmm_lab.sim.strategy import SignalOutput, Strategy
from pmm_lab.strategies.mean_reversion_bb_rsi import (
    MeanReversionBBRSIStrategy,
    MeanReversionBBRSIStrategyConfig,
)
from tests.conftest import CANDLE_DTYPE


def _make_candles(n: int = 1500, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed=seed)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.8)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.3))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.3))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.1, 3.0))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


@pytest.fixture
def candles():
    return _make_candles()


@pytest.fixture
def strategy():
    return MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
        bb_length=20,
        bb_std=2.0,
        bbp_entry_threshold=0.6,  # loose so we get entries
        rsi_length=14,
        rsi_entry_threshold=70.0,
        use_trend_filter=False,
        trend_ema_length=50,
        atr_length=14,
        max_atr_pct_for_entry=1.0,
        volume_filter_window=48,
        min_volume_quantile=0.0,
        max_trades_per_day=6,
    ))


@pytest.fixture
def pair_rules():
    return PairRules(
        price_tick=0.01,
        amount_step=0.001,
        min_notional_quote=1.0,
        fees=FeeConfig(maker_fee=0.001, taker_fee=0.002),
    )


@pytest.fixture
def engine_config():
    return EngineConfig(total_amount_quote=100.0)


class TestProtocol:
    def test_implements_strategy(self, strategy):
        assert isinstance(strategy, Strategy)


class TestInvariants:
    def test_max_executors_must_be_1(self):
        with pytest.raises(ValueError):
            MeanReversionBBRSIStrategyConfig(max_executors_per_side=2)


class TestComputeSignals:
    def test_returns_signal_output(self, strategy, candles):
        out = strategy.compute_signals(candles)
        assert isinstance(out, SignalOutput)
        for key in ("signal", "bbp", "rsi", "atr_pct", "ema_slope", "volume_ok", "close_price", "timestamp"):
            assert key in out.data


class TestBuildOrders:
    def test_buy_on_entry_signal(self, strategy, candles, engine_config, pair_rules):
        signals = strategy.compute_signals(candles)
        sig = signals.data["signal"]
        entry_bars = np.where(sig == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals in synthetic data")
        bar_idx = int(entry_bars[0])
        inv = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inv
        )
        assert placed == 1
        assert len(orders) == 1
        assert orders[0].side == "buy"

    def test_no_order_on_zero_signal(self, strategy, candles, engine_config, pair_rules):
        signals = strategy.compute_signals(candles)
        sig = signals.data["signal"]
        # Find a bar past warmup with signal 0
        zero_bars = np.where(sig == 0.0)[0]
        zero_past_warmup = zero_bars[zero_bars >= signals.warmup_end]
        if len(zero_past_warmup) == 0:
            pytest.skip("No zero-signal bars past warmup")
        bar_idx = int(zero_past_warmup[0])
        inv = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = strategy.build_orders(
            bar_idx, signals, engine_config, pair_rules, inv
        )
        assert placed == 0
        assert len(orders) == 0

    def test_no_order_on_nan_signal(self, strategy, candles, engine_config, pair_rules):
        signals = strategy.compute_signals(candles)
        # Bar 0 has NaN after timestamp shift
        inv = Inventory(base_balance=0.0, quote_balance=100.0)
        orders, placed, rejected = strategy.build_orders(
            0, signals, engine_config, pair_rules, inv
        )
        assert placed == 0

    def test_insufficient_quote_rejects_via_d13(self, strategy, candles, engine_config, pair_rules):
        signals = strategy.compute_signals(candles)
        entry_bars = np.where(signals.data["signal"] == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals")
        inv = Inventory(base_balance=0.0, quote_balance=1.0)  # way below 99 needed
        orders, placed, rejected = strategy.build_orders(
            int(entry_bars[0]), signals, engine_config, pair_rules, inv
        )
        assert placed == 0
        assert rejected == 1

    def test_min_notional_rejection(self, strategy, candles):
        signals = strategy.compute_signals(candles)
        entry_bars = np.where(signals.data["signal"] == 1.0)[0]
        if len(entry_bars) == 0:
            pytest.skip("No entry signals")
        high_rules = PairRules(
            price_tick=0.01, amount_step=0.001,
            min_notional_quote=10_000.0,
            fees=FeeConfig(0.001, 0.002),
        )
        small_ec = EngineConfig(total_amount_quote=5.0)
        inv = Inventory(base_balance=0.0, quote_balance=5.0)
        orders, placed, rejected = strategy.build_orders(
            int(entry_bars[0]), signals, small_ec, high_rules, inv
        )
        assert placed == 0
        assert rejected == 1

    def test_never_places_sell(self, strategy, candles, engine_config, pair_rules):
        """Adversarial: inject a -1 signal and verify strategy rejects it."""
        signals = strategy.compute_signals(candles)
        # Mutate one bar to -1
        bar_idx = signals.warmup_end + 50
        signals.data["signal"][bar_idx] = -1.0
        # close_price, timestamp must be present for bar_idx
        if bar_idx < len(signals.data["close_price"]):
            inv = Inventory(base_balance=10.0, quote_balance=100.0)
            orders, placed, rejected = strategy.build_orders(
                bar_idx, signals, engine_config, pair_rules, inv
            )
            assert placed == 0
            assert len(orders) == 0


class TestMaxTradesPerDay:
    def _make_fixed_signal_array(self, n=300):
        """Build a synthetic signals object where every bar past warmup fires."""
        start_ts = 1_700_000_000
        interval = 300
        signal = np.ones(n, dtype="float64")
        close_price = np.full(n, 100.0, dtype="float64")
        timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64").astype("float64")
        # Zero warmup for tests — we control `signal` directly
        return SignalOutput(
            warmup_end=0,
            data={
                "signal": signal,
                "close_price": close_price,
                "timestamp": timestamps,
                # Other keys not required by build_orders
                "bbp": np.zeros(n),
                "rsi": np.zeros(n),
                "atr_pct": np.zeros(n),
                "ema_slope": np.zeros(n),
                "volume_ok": np.ones(n),
            },
        )

    def test_cap_binds_within_24h(self, pair_rules):
        strat = MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
            bb_length=20, bbp_entry_threshold=0.5,
            use_trend_filter=False, max_trades_per_day=6,
        ))
        signals = self._make_fixed_signal_array(n=100)
        # 100 bars × 300s = 30000s < 86400s — all within 24h of bar 0.
        inv = Inventory(base_balance=0.0, quote_balance=1_000_000.0)
        ec = EngineConfig(total_amount_quote=100.0)

        placed_total = 0
        rejected_total = 0
        for bar_idx in range(10):
            orders, placed, rejected = strat.build_orders(
                bar_idx, signals, ec, pair_rules, inv
            )
            placed_total += placed
            rejected_total += rejected
            # Simulate the engine spending quote for each fill (simplified)
            if placed:
                inv.quote_balance -= ec.total_amount_quote
                inv.base_balance += orders[0].quantity
                # Refill for next iteration
                inv.quote_balance = 1_000_000.0

        assert placed_total == 6, f"Expected 6 placed, got {placed_total}"
        assert rejected_total == 4, f"Expected 4 rejected, got {rejected_total}"

    def test_window_slides_past_24h(self, pair_rules):
        strat = MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
            bb_length=20, bbp_entry_threshold=0.5,
            use_trend_filter=False, max_trades_per_day=6,
        ))
        n = 500
        start_ts = 1_700_000_000
        interval = 300
        signal = np.ones(n, dtype="float64")
        # Space first 6 entries across 24h so they bind when we try bar_idx=6
        close_price = np.full(n, 100.0, dtype="float64")
        timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64").astype("float64")
        signals = SignalOutput(
            warmup_end=0,
            data={
                "signal": signal, "close_price": close_price, "timestamp": timestamps,
                "bbp": np.zeros(n), "rsi": np.zeros(n), "atr_pct": np.zeros(n),
                "ema_slope": np.zeros(n), "volume_ok": np.ones(n),
            },
        )
        inv = Inventory(base_balance=0.0, quote_balance=1_000_000.0)
        ec = EngineConfig(total_amount_quote=100.0)

        # Fire 6 at bars 0-5 — all accepted
        for bar_idx in range(6):
            orders, placed, _ = strat.build_orders(bar_idx, signals, ec, pair_rules, inv)
            assert placed == 1
            inv.quote_balance = 1_000_000.0

        # 7th attempt at bar 6 — rejected by cap
        _, placed7, rejected7 = strat.build_orders(6, signals, ec, pair_rules, inv)
        assert placed7 == 0
        assert rejected7 == 1

        # Advance to a bar whose timestamp is > 86400s past bar 0 — cap window slides.
        # bar 0 ts = start_ts; we need bar ts > start_ts + 86400 = bar index > 288
        inv.quote_balance = 1_000_000.0
        _, placed_next, rejected_next = strat.build_orders(289, signals, ec, pair_rules, inv)
        assert placed_next == 1
        assert rejected_next == 0

    def test_reset_state_clears_cap(self, pair_rules):
        strat = MeanReversionBBRSIStrategy(MeanReversionBBRSIStrategyConfig(
            bb_length=20, bbp_entry_threshold=0.5,
            use_trend_filter=False, max_trades_per_day=3,
        ))
        n = 50
        start_ts = 1_700_000_000
        interval = 300
        signal = np.ones(n, dtype="float64")
        close_price = np.full(n, 100.0, dtype="float64")
        timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64").astype("float64")
        signals = SignalOutput(
            warmup_end=0,
            data={
                "signal": signal, "close_price": close_price, "timestamp": timestamps,
                "bbp": np.zeros(n), "rsi": np.zeros(n), "atr_pct": np.zeros(n),
                "ema_slope": np.zeros(n), "volume_ok": np.ones(n),
            },
        )
        inv = Inventory(base_balance=0.0, quote_balance=1_000_000.0)
        ec = EngineConfig(total_amount_quote=100.0)

        for bar_idx in range(3):
            strat.build_orders(bar_idx, signals, ec, pair_rules, inv)
            inv.quote_balance = 1_000_000.0
        _, p4, r4 = strat.build_orders(3, signals, ec, pair_rules, inv)
        assert p4 == 0
        assert r4 == 1

        strat.reset_state()
        inv.quote_balance = 1_000_000.0
        _, p_after, _ = strat.build_orders(4, signals, ec, pair_rules, inv)
        assert p_after == 1
