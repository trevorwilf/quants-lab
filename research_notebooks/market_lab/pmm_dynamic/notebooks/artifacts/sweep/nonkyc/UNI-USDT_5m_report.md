# PMM Dynamic Optimization Report: nonkyc_UNI-USDT_5m_sweep_nonkyc_v2

Generated: 2026-03-17 09:35:34 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: UNI-USDT
- **interval**: 5m
- **n_candles**: 52424
- **dataset_hash**: 2ebe829c5a0b7e2198d76ad4a30fe2a1f74f7f0672d37fa01ed872a17c597794
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.810874423111224 |
| buy_n_levels | 7 |
| buy_side_weight | 0.5303517255340984 |
| buy_spread_base | 4.7520377246275425 |
| buy_spread_ratio | 1.9168132002553337 |
| cooldown_time | 421.5456504464728 |
| executor_refresh_time | 7826.164335463367 |
| macd_fast | 17 |
| macd_signal | 6 |
| macd_slow | 41 |
| natr_length | 38 |
| sell_n_levels | 10 |
| sell_spread_base | 5.351394107058694 |
| sell_spread_ratio | 2.361752019035613 |
| stop_loss | 0.010334254103639268 |
| take_profit | 0.006431161117072493 |
| time_limit | 157992 |
| total_amount_quote | 867.0870968610116 |
| trailing_stop_activation | 0.025331633760433885 |
| trailing_stop_delta | 0.0010533891752120556 |

## Best Metrics

- **PnL %**: 3.9545
- **Net PnL (quote)**: 34.2887
- **Sharpe Ratio**: 0.7908
- **Max Drawdown %**: 3.7678
- **Profit Factor**: 2.23821372401492
- **Trade Count**: 720
- **Total Fees (quote)**: 12.4860
- **Maker Fees**: 7.5860
- **Taker Fees**: 4.9000
- **Fee Drag %**: 1.4400

## Objective Decomposition

- **Raw Score**: 2.8819
- **PnL Component**: 3.9545
- **Sharpe Component**: 0.3954
- **Drawdown Component**: -1.1303
- **Fee Drag Component**: -0.2880
- **Inventory Component**: -0.0478
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1.3078**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.10 | -11.38 | 0.13 | 54 | -1.1741 | n/a |
| 1 | -0.14 | -9.36 | 0.15 | 74 | -1.2069 | n/a |
| 2 | -0.10 | -5.08 | 0.12 | 45 | -1.2632 | n/a |
| 3 | -0.29 | -17.22 | 0.29 | 37 | -1.6603 | n/a |
| 4 | -0.11 | -11.68 | 0.12 | 36 | -1.4449 | n/a |
| 5 | -0.08 | -6.74 | 0.10 | 41 | -1.3109 | n/a |
| 6 | 0.03 | 0.99 | 0.10 | 51 | 0.4436 | n/a |
| 7 | -0.16 | -11.27 | 0.17 | 59 | -1.2501 | n/a |
| 8 | -0.07 | -7.49 | 0.08 | 37 | -1.3683 | n/a |

## Stress Test Results

Worst Scenario: **very_low_liquidity** (score: 0.7935)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.23 | 0.66 | 3.91 | 1.9085 |
| fees_2x | 2.51 | 0.53 | 4.06 | 0.9339 |
| latency_plus1 | 3.95 | 0.79 | 3.77 | 2.8818 |
| latency_plus2 | 3.93 | 0.79 | 3.78 | 2.8497 |
| latency_plus3 | 3.92 | 0.79 | 3.78 | 2.8427 |
| low_liquidity | 4.76 | 0.84 | 3.71 | 3.7201 |
| very_low_liquidity | 1.63 | 0.54 | 2.70 | 0.7935 |
| high_slippage | 3.81 | 0.77 | 3.79 | 2.7202 |
| extreme_slippage | 3.53 | 0.71 | 3.85 | 2.3966 |
| combined_adverse | 3.87 | 0.70 | 3.86 | 2.5637 |

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
