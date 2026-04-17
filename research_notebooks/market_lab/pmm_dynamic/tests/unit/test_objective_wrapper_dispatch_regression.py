"""Regression: existing `macd_bb` and `pmm_dynamic` dispatch still works after
the new directional wrappers were added.
"""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.optuna.objective_wrapper import create_objective
from tests.conftest import CANDLE_DTYPE


def _make_candles(n=500):
    rng = np.random.default_rng(seed=41)
    start_ts = 1_700_000_000
    interval = 300
    timestamps = np.arange(start_ts, start_ts + n * interval, interval, dtype="int64")
    price = 100.0
    rows = []
    for i in range(n):
        change = rng.normal(0, 0.5)
        open_p = price
        close_p = open_p + change
        high_p = max(open_p, close_p) + abs(rng.normal(0, 0.2))
        low_p = min(open_p, close_p) - abs(rng.normal(0, 0.2))
        high_p = max(high_p, max(open_p, close_p))
        low_p = max(low_p, 0.01)
        low_p = min(low_p, min(open_p, close_p))
        vol = max(0.01, rng.uniform(0.2, 2.5))
        rows.append((int(timestamps[i]), open_p, high_p, low_p, close_p, vol, False))
        price = max(close_p, 1.0)
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_macd_bb_dispatch_still_creates_objective():
    candles = _make_candles()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
        fees=FeeConfig(0.0002, 0.0002),
    )
    obj = create_objective(
        candles=candles, pair_rules=pair_rules, bar_interval_seconds=300,
        dataset_hash="test", reference_price=100.0,
        strategy_name="macd_bb", fixed_quote=100.0,
    )
    assert callable(obj)


def test_pmm_dynamic_dispatch_still_creates_objective():
    candles = _make_candles()
    pair_rules = PairRules(
        price_tick=0.01, amount_step=0.00001, min_notional_quote=1.0,
        fees=FeeConfig(0.0002, 0.0002),
    )
    obj = create_objective(
        candles=candles, pair_rules=pair_rules, bar_interval_seconds=300,
        dataset_hash="test", reference_price=100.0,
        strategy_name="pmm_dynamic", fixed_quote=100.0,
    )
    assert callable(obj)
