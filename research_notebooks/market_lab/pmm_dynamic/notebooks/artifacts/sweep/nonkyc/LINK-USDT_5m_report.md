# PMM Dynamic Optimization Report: nonkyc_LINK-USDT_5m_sweep_nonkyc_v2

Generated: 2026-03-17 08:08:40 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LINK-USDT
- **interval**: 5m
- **n_candles**: 52423
- **dataset_hash**: e8d7be15126821501af974dad8f420923ac46ab868b83d921dbd1683d6398c7f
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.7817631378485075 |
| buy_n_levels | 10 |
| buy_side_weight | 0.42055162198833684 |
| buy_spread_base | 4.221151574367895 |
| buy_spread_ratio | 2.994161615626676 |
| cooldown_time | 3041.2662446955583 |
| executor_refresh_time | 12423.694952837603 |
| macd_fast | 34 |
| macd_signal | 18 |
| macd_slow | 77 |
| natr_length | 34 |
| sell_n_levels | 7 |
| sell_spread_base | 2.5563958560186464 |
| sell_spread_ratio | 1.289692334052227 |
| stop_loss | 0.1540456913808346 |
| take_profit | 0.00984152016669388 |
| time_limit | 162155 |
| total_amount_quote | 989.9404438281426 |
| trailing_stop_activation | 0.02041232374773757 |
| trailing_stop_delta | 0.001592642420129594 |

## Best Metrics

- **PnL %**: 6.3500
- **Net PnL (quote)**: 62.8617
- **Sharpe Ratio**: 0.6797
- **Max Drawdown %**: 6.9625
- **Profit Factor**: 1.7068128488593108
- **Trade Count**: 1299
- **Total Fees (quote)**: 45.2492
- **Maker Fees**: 36.9835
- **Taker Fees**: 8.2657
- **Fee Drag %**: 4.5709

## Objective Decomposition

- **Raw Score**: 3.3373
- **PnL Component**: 6.3500
- **Sharpe Component**: 0.3398
- **Drawdown Component**: -2.0887
- **Fee Drag Component**: -0.9142
- **Inventory Component**: -0.3373
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7970**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.07 | -1.09 | 0.42 | 72 | -0.8894 | n/a |
| 1 | -0.07 | -0.88 | 0.36 | 95 | -0.7605 | n/a |
| 2 | 0.13 | 3.39 | 0.13 | 73 | 1.7147 | n/a |
| 3 | 0.17 | 2.87 | 0.24 | 74 | 1.3990 | n/a |
| 4 | 0.13 | 3.89 | 0.14 | 57 | 1.9495 | n/a |
| 5 | 0.16 | 5.68 | 0.10 | 55 | 2.5459 | n/a |
| 6 | -0.70 | -6.03 | 0.86 | 65 | -2.1608 | n/a |
| 7 | -1.51 | -6.77 | 2.21 | 85 | -3.5145 | n/a |
| 8 | 0.27 | 5.54 | 0.15 | 107 | 2.6030 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -3.3287)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.06 | 0.47 | 8.48 | 0.0319 |
| fees_2x | 1.78 | 0.27 | 10.18 | -3.3287 |
| latency_plus1 | 6.41 | 0.69 | 6.73 | 3.4778 |
| latency_plus2 | 6.31 | 0.68 | 6.79 | 3.3603 |
| latency_plus3 | 6.28 | 0.67 | 6.81 | 3.3191 |
| low_liquidity | 5.60 | 0.61 | 7.56 | 2.3431 |
| very_low_liquidity | 6.09 | 0.66 | 7.08 | 3.0490 |
| high_slippage | 6.14 | 0.66 | 7.05 | 3.0939 |
| extreme_slippage | 5.72 | 0.62 | 7.27 | 2.5901 |
| combined_adverse | 3.13 | 0.39 | 9.23 | -1.1834 |

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
