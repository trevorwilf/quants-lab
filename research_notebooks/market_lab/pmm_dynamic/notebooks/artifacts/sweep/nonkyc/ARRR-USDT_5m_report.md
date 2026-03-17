# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_nonkyc_v2

Generated: 2026-03-17 05:40:19 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 54757
- **dataset_hash**: d7e9dca8fd28b4a761c660b8ae489d1ad2c068a197813aed626bf315bde7137b
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.0347608800577812 |
| buy_n_levels | 7 |
| buy_side_weight | 0.5128308195335152 |
| buy_spread_base | 0.2866745887990004 |
| buy_spread_ratio | 1.2892481022629942 |
| cooldown_time | 147.04398061495817 |
| executor_refresh_time | 1157.3245398095141 |
| macd_fast | 27 |
| macd_signal | 5 |
| macd_slow | 100 |
| natr_length | 21 |
| sell_n_levels | 2 |
| sell_spread_base | 0.39102043511131684 |
| sell_spread_ratio | 1.4318019769130872 |
| stop_loss | 0.20411035059725707 |
| take_profit | 0.13976137897028074 |
| time_limit | 148895 |
| total_amount_quote | 53.111438176801016 |
| trailing_stop_activation | 0.029500860181069972 |
| trailing_stop_delta | 0.001275995410957176 |

## Best Metrics

- **PnL %**: 3806.8927
- **Net PnL (quote)**: 2021.8954
- **Sharpe Ratio**: 6.0490
- **Max Drawdown %**: 41.2066
- **Profit Factor**: 1.3055987567567566
- **Trade Count**: 44140
- **Total Fees (quote)**: 801.9061
- **Maker Fees**: 275.4419
- **Taker Fees**: 526.4641
- **Fee Drag %**: 1509.8557

## Objective Decomposition

- **Raw Score**: 3490.7855
- **PnL Component**: 3806.8927
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -12.3620
- **Fee Drag Component**: -301.9711
- **Inventory Component**: -4.0124
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **361.3865**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 727.12 | 24.67 | 14.71 | 2719 | 704.7379 | n/a |
| 1 | 382.49 | 27.20 | 16.96 | 2260 | 360.6471 | n/a |
| 2 | 415.71 | 18.68 | 20.26 | 2444 | 390.0749 | n/a |
| 3 | 580.54 | 30.26 | 10.34 | 2363 | 559.2376 | n/a |
| 4 | 447.46 | 33.52 | 6.12 | 2393 | 426.9549 | n/a |
| 5 | 721.89 | 25.74 | 7.79 | 2441 | 699.7704 | n/a |
| 6 | 324.90 | 18.42 | 18.93 | 2334 | 300.4059 | n/a |
| 7 | 370.83 | 26.62 | 23.60 | 2492 | 344.8118 | n/a |
| 8 | 323.36 | 32.98 | 5.03 | 2279 | 304.5092 | n/a |
| 9 | 426.06 | 26.17 | 5.04 | 2458 | 406.1500 | n/a |

## Stress Test Results

Worst Scenario: **combined_adverse** (score: 2211.9133)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3340.80 | 5.85 | 39.89 | 2886.7486 |
| fees_2x | 2827.25 | 5.66 | 42.06 | 2237.5780 |
| latency_plus1 | 3450.53 | 5.92 | 39.57 | 3158.9349 |
| latency_plus2 | 3172.18 | 5.81 | 40.84 | 2905.5502 |
| latency_plus3 | 2556.44 | 5.36 | 43.40 | 2335.4077 |
| low_liquidity | 3878.11 | 5.87 | 39.46 | 3581.8129 |
| very_low_liquidity | 3248.06 | 5.64 | 34.86 | 2991.4024 |
| high_slippage | 3635.48 | 5.99 | 40.53 | 3322.4065 |
| extreme_slippage | 3368.61 | 5.87 | 41.35 | 3058.5917 |
| combined_adverse | 2592.30 | 5.35 | 41.39 | 2211.9133 |

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
