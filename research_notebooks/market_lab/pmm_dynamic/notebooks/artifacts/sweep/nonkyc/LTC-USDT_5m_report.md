# PMM Dynamic Optimization Report: nonkyc_LTC-USDT_5m_sweep_nonkyc_v1

Generated: 2026-03-09 20:03:54 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 52559
- **dataset_hash**: 5ff70d356d291e6dd2ee2e112cf16b89eb2ebf0a871a9aa803b4a24f68c4da74
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.565451256350591 |
| buy_n_levels | 8 |
| buy_side_weight | 0.7383251845327828 |
| buy_spread_base | 5.328166422931712 |
| buy_spread_ratio | 2.497996614758753 |
| cooldown_time | 2826.083775864875 |
| executor_refresh_time | 1746.3629403787127 |
| macd_fast | 17 |
| macd_signal | 7 |
| macd_slow | 41 |
| natr_length | 16 |
| sell_n_levels | 9 |
| sell_spread_base | 4.106693655631374 |
| sell_spread_ratio | 1.7797442411746989 |
| stop_loss | 0.19394304068086232 |
| take_profit | 0.009614591123261466 |
| time_limit | 131507 |
| total_amount_quote | 899.7271997743595 |
| trailing_stop_activation | 0.01710165981397141 |
| trailing_stop_delta | 0.008734613693271795 |

## Best Metrics

- **PnL %**: 24.5609
- **Net PnL (quote)**: 220.9812
- **Sharpe Ratio**: 1.4264
- **Max Drawdown %**: 6.8726
- **Profit Factor**: 3.1780426935178543
- **Trade Count**: 563
- **Total Fees (quote)**: 23.5264
- **Maker Fees**: 16.7438
- **Taker Fees**: 6.7826
- **Fee Drag %**: 2.6148

## Objective Decomposition

- **Raw Score**: 22.4335
- **PnL Component**: 24.5609
- **Sharpe Component**: 0.7132
- **Drawdown Component**: -2.0618
- **Fee Drag Component**: -0.5230
- **Inventory Component**: -0.2476
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.2182**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 0.25 | 6.48 | 0.13 | 19 | 2.0133 |
| 1 | 0.14 | 3.51 | 0.15 | 24 | 1.2792 |
| 2 | -0.02 | -0.73 | 0.11 | 10 | -1.2389 |
| 3 | -0.05 | -0.84 | 0.38 | 29 | -1.1669 |
| 4 | 0.31 | 4.16 | 0.26 | 42 | 1.9116 |
| 5 | 0.11 | 5.45 | 0.07 | 24 | 2.0141 |
| 6 | 1.15 | 3.92 | 0.54 | 41 | 2.5872 |
| 7 | -0.55 | -4.39 | 1.03 | 40 | -2.2285 |
| 8 | 0.21 | 10.75 | 0.04 | 23 | 2.1127 |
| 9 | -0.81 | -3.87 | 1.43 | 51 | -2.5936 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 19.1888)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 23.25 | 1.37 | 6.95 | 20.8112 |
| fees_2x | 21.95 | 1.31 | 7.02 | 19.1888 |
| latency_plus1 | 24.75 | 1.44 | 6.87 | 22.6545 |
| latency_plus2 | 24.41 | 1.46 | 5.35 | 22.8732 |
| latency_plus3 | 24.76 | 1.44 | 5.75 | 23.0639 |
| low_liquidity | 24.39 | 1.42 | 6.02 | 22.5152 |
| very_low_liquidity | 24.22 | 1.41 | 5.63 | 22.4592 |
| high_slippage | 24.37 | 1.42 | 6.88 | 22.2393 |
| extreme_slippage | 24.00 | 1.40 | 6.89 | 21.8510 |
| combined_adverse | 23.21 | 1.37 | 6.09 | 21.0612 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
