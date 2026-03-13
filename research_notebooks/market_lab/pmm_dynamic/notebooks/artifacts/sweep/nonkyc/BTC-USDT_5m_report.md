# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_sweep_nonkyc_v1

Generated: 2026-03-09 16:16:44 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 54126
- **dataset_hash**: 55737a62a121a1956ad9c481212d15a94c5c3345ad29300a67ed9e8712c8903e
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.0116833137702033 |
| buy_n_levels | 9 |
| buy_side_weight | 0.4939775709846089 |
| buy_spread_base | 5.419141248662261 |
| buy_spread_ratio | 2.969701904571366 |
| cooldown_time | 3405.5726021576884 |
| executor_refresh_time | 8790.020861919618 |
| macd_fast | 13 |
| macd_signal | 28 |
| macd_slow | 25 |
| natr_length | 23 |
| sell_n_levels | 2 |
| sell_spread_base | 4.110112857270836 |
| sell_spread_ratio | 2.2654991151488493 |
| stop_loss | 0.2014930763208193 |
| take_profit | 0.13431335398997735 |
| time_limit | 110799 |
| total_amount_quote | 635.255914623056 |
| trailing_stop_activation | 0.023655117182311104 |
| trailing_stop_delta | 0.001196500386283847 |

## Best Metrics

- **PnL %**: 82.2978
- **Net PnL (quote)**: 522.8016
- **Sharpe Ratio**: 1.2906
- **Max Drawdown %**: 8.2551
- **Profit Factor**: 3.9346716939926174
- **Trade Count**: 460
- **Total Fees (quote)**: 57.6034
- **Maker Fees**: 19.0397
- **Taker Fees**: 38.5637
- **Fee Drag %**: 9.0677

## Objective Decomposition

- **Raw Score**: 78.0956
- **PnL Component**: 82.2978
- **Sharpe Component**: 0.6453
- **Drawdown Component**: -2.4765
- **Fee Drag Component**: -1.8135
- **Inventory Component**: -0.5444
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.8134**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.08 | 1.99 | 0.29 | 21 | 0.3254 |
| 1 | 95.18 | 5.12 | 0.33 | 28 | 96.8698 |
| 2 | -0.68 | -5.98 | 1.06 | 32 | -2.6041 |
| 3 | -0.05 | -0.75 | 0.27 | 28 | -1.1612 |
| 4 | 0.06 | 0.95 | 0.25 | 28 | -0.1883 |
| 5 | 0.08 | 4.00 | 0.05 | 22 | 1.4016 |
| 6 | -0.45 | -5.74 | 0.52 | 26 | -2.4267 |
| 7 | 0.10 | 0.77 | 0.64 | 41 | -0.1923 |
| 8 | 0.38 | 3.02 | 0.80 | 38 | 1.0807 |
| 9 | -0.10 | -1.23 | 0.57 | 36 | -1.4117 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 66.3140)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 77.76 | 1.25 | 9.66 | 72.2064 |
| fees_2x | 73.23 | 1.21 | 11.07 | 66.3140 |
| latency_plus1 | 85.13 | 1.30 | 8.27 | 80.7919 |
| latency_plus2 | 86.20 | 1.31 | 7.76 | 82.0158 |
| latency_plus3 | 87.05 | 1.31 | 7.25 | 83.0496 |
| low_liquidity | 82.30 | 1.29 | 8.26 | 78.0956 |
| very_low_liquidity | 82.30 | 1.29 | 8.25 | 78.1005 |
| high_slippage | 80.78 | 1.28 | 8.72 | 76.4273 |
| extreme_slippage | 77.74 | 1.25 | 9.65 | 73.0898 |
| combined_adverse | 78.80 | 1.25 | 10.22 | 72.8901 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
