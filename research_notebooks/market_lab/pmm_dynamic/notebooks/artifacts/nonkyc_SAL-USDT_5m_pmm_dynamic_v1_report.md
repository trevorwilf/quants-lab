# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_pmm_dynamic_v1

Generated: 2026-03-06 23:02:39 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 53143
- **dataset_hash**: c3f47aaeb70a0c77701fe169f11f46a44df040ab96cbd4741646bf7b6d5c3bcf

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.9231975763052906 |
| buy_n_levels | 2 |
| buy_side_weight | 0.7953200971336091 |
| buy_spread_base | 0.2666436702529785 |
| buy_spread_ratio | 1.2728064292621248 |
| cooldown_time | 205.1292671147308 |
| executor_refresh_time | 377.0066781008875 |
| macd_fast | 8 |
| macd_signal | 15 |
| macd_slow | 84 |
| natr_length | 41 |
| sell_n_levels | 1 |
| sell_spread_base | 2.1523807174134966 |
| sell_spread_ratio | 1.703535807803702 |
| stop_loss | 0.17417519112110125 |
| take_profit | 0.0690823002970069 |
| time_limit | 64781 |
| total_amount_quote | 25.28366790695684 |
| trailing_stop_activation | 0.047020753475201744 |
| trailing_stop_delta | 0.0011237435057616953 |

## Best Metrics

- **PnL %**: -787.2653
- **Net PnL (quote)**: -787.2653
- **Sharpe Ratio**: 0.6645
- **Max Drawdown %**: 789.7404
- **Profit Factor**: 0.4014812022991047
- **Trade Count**: 12796
- **Total Fees (quote)**: 203.0815
- **Maker Fees**: 81.2103
- **Taker Fees**: 121.8712
- **Fee Drag %**: 203.0815

## Objective Decomposition

- **Raw Score**: -1067.6878
- **PnL Component**: -787.2653
- **Sharpe Component**: 0.3323
- **Drawdown Component**: -236.9221
- **Fee Drag Component**: -40.6163
- **Inventory Component**: -3.2164
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-85.5976**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | -105.23 | 4.91 | 106.85 | 685 | -149.9707 |
| 1 | -71.86 | -18.28 | 72.17 | 697 | -101.9468 |
| 2 | -53.35 | -14.56 | 54.73 | 769 | -78.5387 |
| 3 | -52.01 | -17.09 | 52.55 | 560 | -76.2794 |
| 4 | -40.08 | -13.68 | 41.38 | 484 | -59.7342 |
| 5 | -44.31 | -12.16 | 45.62 | 701 | -66.3648 |
| 6 | -63.67 | -18.17 | 65.33 | 575 | -92.2444 |
| 7 | -20.89 | -6.91 | 23.45 | 623 | -35.1919 |
| 8 | -52.20 | -12.80 | 52.59 | 653 | -76.4015 |
| 9 | -76.06 | -20.71 | 76.09 | 676 | -108.1844 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -1373.2462)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -888.81 | 1.48 | 890.96 | -1221.1078 |
| fees_2x | -990.35 | -0.51 | 992.17 | -1373.2462 |
| latency_plus1 | -796.81 | -1.39 | 799.28 | -1080.5759 |
| latency_plus2 | -806.56 | 1.97 | 809.37 | -1090.7624 |
| latency_plus3 | -778.66 | 3.84 | 781.33 | -1054.8309 |
| low_liquidity | -743.97 | 1.82 | 747.66 | -1008.0005 |
| very_low_liquidity | -712.04 | -1.11 | 715.09 | -961.6971 |
| high_slippage | -807.60 | 1.43 | 810.05 | -1093.4797 |
| extreme_slippage | -848.28 | 0.11 | 850.66 | -1149.8558 |
| combined_adverse | -854.21 | -1.37 | 856.56 | -1169.1779 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: PASS
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
