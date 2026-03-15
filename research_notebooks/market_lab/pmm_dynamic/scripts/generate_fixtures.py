"""Generate frozen parity fixtures for regression testing.

Run after any intentional feature computation change.
Outputs go to fixtures/ and should be committed to the repo.
"""
import sys
sys.path.insert(0, ".")

from tests.conftest import _make_sample_candles_5m, _make_sample_candles_500
from pmm_lab.features.pmm_dynamic_features import PMMDynamicConfig
from pmm_lab.parity.fixtures import generate_frozen_fixture

PARAMS = {
    "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
    "buy_n_levels": 2, "sell_n_levels": 2,
    "buy_spread_base": 1.0, "buy_spread_ratio": 2.0,
    "sell_spread_base": 1.0, "sell_spread_ratio": 2.0,
    "buy_side_weight": 0.5, "amount_skew": 1.0,
    "total_amount_quote": 100.0,
    "executor_refresh_time": 3120.0, "cooldown_time": 3120.0,
    "stop_loss": 0.03, "take_profit": 0.015, "time_limit": 43200,
    "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.001,
}

print("Generating fixtures with controller_compat=True (default)...")
print()

# Short fixture (100 bars — below max_records)
candles_100 = _make_sample_candles_5m()
path1 = generate_frozen_fixture(
    candles_100, PARAMS,
    name="short_100bar_compat",
    output_dir="fixtures",
    check_bars=[55, 60, 70, 80, 90, 99],
)
print(f"  Short fixture: {path1}")

# Long fixture (500 bars — exceeds max_records=142)
candles_500 = _make_sample_candles_500()
path2 = generate_frozen_fixture(
    candles_500, PARAMS,
    name="long_500bar_compat",
    output_dir="fixtures",
    check_bars=[60, 100, 141, 142, 200, 300, 400, 499],
)
print(f"  Long fixture: {path2}")

print()
print("Done. Commit fixtures/ to the repo.")
