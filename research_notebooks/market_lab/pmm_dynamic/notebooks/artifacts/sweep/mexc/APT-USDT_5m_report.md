# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 03:38:40 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m
- **n_candles**: 52047
- **dataset_hash**: 62da5d7d6dd65d1bbc63ceb786439a89040d7f94a8f4fcdf3683bb8b033f5224
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.9713977809307748 |
| buy_n_levels | 9 |
| buy_side_weight | 0.5358027448164506 |
| buy_spread_base | 2.3524874230371418 |
| buy_spread_ratio | 2.703448879823084 |
| cooldown_time | 884.1585208463666 |
| executor_refresh_time | 2472.670640248718 |
| macd_fast | 23 |
| macd_signal | 10 |
| macd_slow | 37 |
| natr_length | 31 |
| sell_n_levels | 10 |
| sell_spread_base | 0.5075775711335472 |
| sell_spread_ratio | 1.3303478226367813 |
| stop_loss | 0.16109910215285206 |
| take_profit | 0.12856207007443915 |
| time_limit | 138255 |
| total_amount_quote | 60.7205312158917 |
| trailing_stop_activation | 0.03939568388972452 |
| trailing_stop_delta | 0.001053492222282848 |

## Best Metrics

- **PnL %**: 93.1374
- **Net PnL (quote)**: 56.5536
- **Sharpe Ratio**: 2.3290
- **Max Drawdown %**: 34.1925
- **Profit Factor**: 1.2771763351004095
- **Trade Count**: 3822
- **Total Fees (quote)**: 15.8016
- **Maker Fees**: 8.3414
- **Taker Fees**: 7.4602
- **Fee Drag %**: 26.0235

## Objective Decomposition

- **Raw Score**: 77.6031
- **PnL Component**: 93.1374
- **Sharpe Component**: 1.1645
- **Drawdown Component**: -10.2578
- **Fee Drag Component**: -5.2047
- **Inventory Component**: -1.1528
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **3.9577**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 8.24 | 5.65 | 7.44 | 284 | 6.7096 |
| 1 | 21.70 | 10.62 | 6.52 | 253 | 20.5939 |
| 2 | 19.52 | 10.91 | 4.87 | 256 | 19.2142 |
| 3 | 1.87 | 2.27 | 3.67 | 166 | 1.2057 |
| 4 | 9.76 | 12.04 | 1.96 | 145 | 11.2157 |
| 5 | 4.60 | 9.39 | 1.27 | 198 | 6.0804 |
| 6 | -3.30 | -2.44 | 9.85 | 195 | -8.2731 |
| 7 | 11.29 | 4.77 | 9.92 | 240 | 9.3202 |
| 8 | 0.62 | 0.66 | 6.13 | 254 | -2.1265 |

## Stress Test Results

Worst Scenario: **extreme_slippage** (score: 7.3408)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 91.98 | 2.25 | 33.93 | 73.7717 |
| fees_2x | 86.94 | 2.14 | 33.93 | 66.4186 |
| latency_plus1 | 105.63 | 2.24 | 35.80 | 89.5893 |
| latency_plus2 | 42.94 | 1.41 | 37.26 | 26.3541 |
| latency_plus3 | 41.92 | 1.41 | 39.22 | 25.2117 |
| low_liquidity | 97.61 | 2.40 | 34.19 | 82.0739 |
| very_low_liquidity | 103.43 | 2.48 | 34.19 | 87.8917 |
| high_slippage | 71.82 | 2.00 | 34.19 | 56.5995 |
| extreme_slippage | 23.83 | 1.01 | 37.70 | 7.3408 |
| combined_adverse | 56.51 | 1.47 | 34.45 | 38.2343 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
