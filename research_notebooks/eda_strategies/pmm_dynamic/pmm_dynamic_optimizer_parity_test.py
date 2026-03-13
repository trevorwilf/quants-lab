"""
pmm_dynamic_optimizer_parity_test.py — Standalone parity test.

Generates synthetic OHLCV candles and verifies CPU/GPU produce matching results.
Covers baseline, auto-spread-floor, and edge-case test scenarios.
Exits with code 0 if all pass, 1 if any fail.
"""
import sys
import numpy as np
import pandas as pd


def generate_synthetic_candles(n=2000, seed=42):
    """Generate synthetic OHLCV candles for testing (moderate volatility)."""
    rng = np.random.RandomState(seed)

    # Random walk price
    returns = rng.normal(0.0001, 0.005, n)
    prices = 100.0 * np.exp(np.cumsum(returns))

    # Build OHLCV
    highs = prices * (1 + rng.uniform(0.001, 0.01, n))
    lows = prices * (1 - rng.uniform(0.001, 0.01, n))
    opens = prices * (1 + rng.uniform(-0.003, 0.003, n))
    volumes = rng.uniform(1000, 50000, n)

    # Enforce OHLC sanity: high >= max(open, close), low <= min(open, close), all positive
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))
    eps = 1e-8
    prices = np.maximum(prices, eps)
    opens = np.maximum(opens, eps)
    highs = np.maximum(highs, eps)
    lows = np.maximum(lows, eps)

    # Timestamps: 5-minute candles
    start_ts = pd.Timestamp("2024-01-01")
    timestamps = pd.date_range(start=start_ts, periods=n, freq="5min")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
    })
    return df


def generate_low_vol_candles(n=2000, seed=42):
    """Generate BTC-like low-volatility synthetic candles (NATR ~0.002-0.004)."""
    rng = np.random.RandomState(seed)

    # Lower volatility returns for BTC-like price action
    returns = rng.normal(0.00005, 0.002, n)
    prices = 40000.0 * np.exp(np.cumsum(returns))

    # Tight OHLC range (low NATR)
    highs = prices * (1 + rng.uniform(0.0005, 0.003, n))
    lows = prices * (1 - rng.uniform(0.0005, 0.003, n))
    opens = prices * (1 + rng.uniform(-0.001, 0.001, n))
    volumes = rng.uniform(0.1, 5.0, n)  # BTC volume in base units

    # Enforce OHLC sanity: high >= max(open, close), low <= min(open, close), all positive
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))
    eps = 1e-8
    prices = np.maximum(prices, eps)
    opens = np.maximum(opens, eps)
    highs = np.maximum(highs, eps)
    lows = np.maximum(lows, eps)

    start_ts = pd.Timestamp("2024-01-01")
    timestamps = pd.date_range(start=start_ts, periods=n, freq="5min")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
    })
    return df


def generate_high_vol_candles(n=2000, seed=42):
    """Generate altcoin-like high-volatility synthetic candles (NATR ~0.02)."""
    rng = np.random.RandomState(seed)

    returns = rng.normal(0.0002, 0.015, n)
    prices = 0.50 * np.exp(np.cumsum(returns))

    highs = prices * (1 + rng.uniform(0.005, 0.025, n))
    lows = prices * (1 - rng.uniform(0.005, 0.025, n))
    opens = prices * (1 + rng.uniform(-0.008, 0.008, n))
    volumes = rng.uniform(50000, 500000, n)

    # Enforce OHLC sanity: high >= max(open, close), low <= min(open, close), all positive
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))
    eps = 1e-8
    prices = np.maximum(prices, eps)
    opens = np.maximum(opens, eps)
    highs = np.maximum(highs, eps)
    lows = np.maximum(lows, eps)

    start_ts = pd.Timestamp("2024-01-01")
    timestamps = pd.date_range(start=start_ts, periods=n, freq="5min")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
    })
    return df


# ---------------------------------------------------------------------------
# Baseline parameter sets (5 original tests)
# ---------------------------------------------------------------------------
TEST_PARAMS = [
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
    },
    {
        "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 20,
        "n_levels": 1,
        "spread_level_1": 1.5,
        "amount_pct_1": 100.0,
        "stop_loss": 0.05, "take_profit": 0.03,
        "time_limit_minutes": 120,
        "trailing_activation": 0.02, "trailing_delta": 0.01,
        "refresh_minutes": 10,
    },
    {
        "macd_fast": 8, "macd_slow": 30, "macd_signal": 7, "natr_length": 10,
        "n_levels": 3,
        "spread_level_1": 0.8, "spread_level_2": 1.6, "spread_level_3": 3.0,
        "amount_pct_1": 40.0, "amount_pct_2": 35.0, "amount_pct_3": 25.0,
        "stop_loss": 0.02, "take_profit": 0.015,
        "time_limit_minutes": 30,
        "trailing_activation": 0.008, "trailing_delta": 0.004,
        "refresh_minutes": 3,
    },
    {
        "macd_fast": 15, "macd_slow": 45, "macd_signal": 12, "natr_length": 25,
        "n_levels": 2,
        "spread_level_1": 2.0, "spread_level_2": 4.0,
        "amount_pct_1": 60.0, "amount_pct_2": 40.0,
        "stop_loss": 0.08, "take_profit": 0.05,
        "time_limit_minutes": 240,
        "trailing_activation": 0.03, "trailing_delta": 0.015,
        "refresh_minutes": 15,
    },
    {
        "macd_fast": 10, "macd_slow": 35, "macd_signal": 8, "natr_length": 12,
        "n_levels": 2,
        "spread_level_1": 0.6, "spread_level_2": 1.2,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.04, "take_profit": 0.025,
        "time_limit_minutes": 90,
        "trailing_activation": 0.015, "trailing_delta": 0.008,
        "refresh_minutes": 6,
    },
]

# ---------------------------------------------------------------------------
# Edge-case parameter sets (V3)
# ---------------------------------------------------------------------------
EDGE_CASE_PARAMS = [
    # max_open_positions=2 — exercises the cap logic
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"max_open_positions": 2},
    },
    # fill_rate_pct=0.05 — exercises volume gate
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"fill_rate_pct": 0.05},
    },
    # cooldown_seconds=60 — exercises cooldown logic
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"cooldown_seconds": 60},
    },
    # initial_inventory_mode="all_quote" — original behavior, regression test
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"initial_inventory_mode": "all_quote"},
    },
    # initial_inventory_mode="half_and_half" — current default, regression test
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"initial_inventory_mode": "half_and_half"},
    },
    # FIX-7: timestamp_shift=1 — exercises the shift cache logic (most common live mode)
    {
        "macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "natr_length": 14,
        "n_levels": 2,
        "spread_level_1": 1.0, "spread_level_2": 2.0,
        "amount_pct_1": 50.0, "amount_pct_2": 50.0,
        "stop_loss": 0.03, "take_profit": 0.02,
        "time_limit_minutes": 60,
        "trailing_activation": 0.01, "trailing_delta": 0.005,
        "refresh_minutes": 5,
        "_test_overrides": {"timestamp_shift": 1},
    },
    # FIX-7: timestamp_shift=1 with different MACD params
    {
        "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 20,
        "n_levels": 1,
        "spread_level_1": 1.5,
        "amount_pct_1": 100.0,
        "stop_loss": 0.05, "take_profit": 0.03,
        "time_limit_minutes": 120,
        "trailing_activation": 0.02, "trailing_delta": 0.01,
        "refresh_minutes": 10,
        "_test_overrides": {"timestamp_shift": 1},
    },
]


def _run_test(candles, params, test_label, overrides=None,
              auto_spread_floor=False, tolerance=0.02):
    """Run a single parity test and return (pass, cpu, gpu) or raise."""
    from pmm_dynamic_optimizer_gpu import assert_cpu_gpu_parity

    kwargs = {
        "total_capital": 1000.0,
        "maker_fee": 0.001,
        "taker_fee": 0.002,
        "slippage_max_pct": 0.001,
        "fill_rate_pct": 0.05,
        "max_open_positions": 4,
        "deploy_fraction": 0.4,
        "compounding": False,
        "cooldown_seconds": 15,
        "min_spread_floor": 0.0,
        "tolerance": tolerance,
        "auto_spread_floor": auto_spread_floor,
        "candles_df": candles if auto_spread_floor else None,
        "timestamp_shift": 0,  # FIX-7: default, overridable via _test_overrides
        "enforce_spread_floor": False,  # BUG-5: default off
        "enforce_nc_guard": False,      # BUG-5: default off
        "cooldown_sl_only": True,       # ADD-2: match Hummingbot
    }
    if overrides:
        kwargs.update(overrides)

    # Strip internal _test_overrides from params
    clean_params = {k: v for k, v in params.items() if not k.startswith("_")}

    result = assert_cpu_gpu_parity(candles, clean_params, **kwargs)
    return result


def main():
    from pmm_dynamic_optimizer_gpu import gpu_available

    if not gpu_available():
        print("GPU not available — cannot run parity test")
        sys.exit(1)

    candles = generate_synthetic_candles(n=2000, seed=42)
    low_vol_candles = generate_low_vol_candles(n=2000, seed=42)
    high_vol_candles = generate_high_vol_candles(n=2000, seed=42)

    print(f"Generated candles: standard={len(candles)}, low_vol={len(low_vol_candles)}, high_vol={len(high_vol_candles)}")
    print(f"{'Test':<40} {'Sharpe CPU':>12} {'Sharpe GPU':>12} {'PnL% CPU':>10} {'PnL% GPU':>10} "
          f"{'Trades CPU':>11} {'Trades GPU':>11} {'Status':>8}")
    print("-" * 120)

    n_pass = 0
    n_fail = 0

    def _print_result(label, result, status):
        nonlocal n_pass, n_fail
        cpu = result["cpu_result"]
        gpu = result["gpu_result"]
        print(f"{label:<40} {cpu['sharpe']:>12.4f} {gpu['sharpe']:>12.4f} "
              f"{cpu['pnl_pct']:>10.4f} {gpu['pnl_pct']:>10.4f} "
              f"{cpu['n_trades']:>11} {gpu['n_trades']:>11} {status:>8}")
        if status == "PASS":
            n_pass += 1
        else:
            n_fail += 1

    def _print_fail(label, error):
        nonlocal n_fail
        print(f"{label:<40} {'':>12} {'':>12} {'':>10} {'':>10} {'':>11} {'':>11} {'FAIL':>8}")
        print(f"  {error}")
        n_fail += 1

    # ── Section 1: Baseline tests (5 original param sets) ──
    print("\n=== Baseline Tests (auto_spread_floor=False) ===")
    for idx, params in enumerate(TEST_PARAMS):
        label = f"Baseline #{idx+1}"
        try:
            result = _run_test(candles, params, label, auto_spread_floor=False)
            _print_result(label, result, "PASS")
        except (AssertionError, Exception) as e:
            _print_fail(label, e)

    # ── Section 2: Auto spread floor tests ──
    print("\n=== Auto Spread Floor Tests ===")
    for vol_label, vol_candles in [("low_vol", low_vol_candles), ("high_vol", high_vol_candles)]:
        for idx, params in enumerate(TEST_PARAMS[:3]):
            label = f"ASF {vol_label} #{idx+1}"
            try:
                result = _run_test(vol_candles, params, label, auto_spread_floor=True)
                _print_result(label, result, "PASS")
            except (AssertionError, Exception) as e:
                _print_fail(label, e)

    # ── Section 3: Edge-case tests ──
    print("\n=== Edge-Case Tests ===")
    for idx, params in enumerate(EDGE_CASE_PARAMS):
        overrides = params.get("_test_overrides", {})
        override_desc = ", ".join(f"{k}={v}" for k, v in overrides.items())
        label = f"Edge #{idx+1} ({override_desc})"
        try:
            result = _run_test(candles, params, label, overrides=overrides)
            _print_result(label, result, "PASS")
        except (AssertionError, Exception) as e:
            _print_fail(label, e)

    # ── Summary ──
    total = n_pass + n_fail
    print("-" * 120)
    print(f"Results: {n_pass} passed, {n_fail} failed out of {total} tests")

    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()