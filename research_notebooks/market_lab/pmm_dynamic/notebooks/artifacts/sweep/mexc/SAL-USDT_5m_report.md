# PMM Dynamic Optimization Report: mexc_SAL-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 08:57:44 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 53638
- **dataset_hash**: 47ae9e45b5250e96afa43140a7bd73630f2eff0016fdb8516c4cdfd4ea2e1d79
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.1317647060514227 |
| buy_n_levels | 7 |
| buy_side_weight | 0.24877639490038095 |
| buy_spread_base | 5.126904986220576 |
| buy_spread_ratio | 2.615393101980169 |
| cooldown_time | 346.18924892593964 |
| executor_refresh_time | 7826.5842471526885 |
| macd_fast | 29 |
| macd_signal | 23 |
| macd_slow | 73 |
| natr_length | 46 |
| sell_n_levels | 5 |
| sell_spread_base | 5.948105293733019 |
| sell_spread_ratio | 1.6795101749992654 |
| stop_loss | 0.23340128741805705 |
| take_profit | 0.12323926102658198 |
| time_limit | 101836 |
| total_amount_quote | 163.33310471881157 |
| trailing_stop_activation | 0.010087672262032879 |
| trailing_stop_delta | 0.0012185088219279997 |

## Best Metrics

- **PnL %**: 78.5446
- **Net PnL (quote)**: 128.2893
- **Sharpe Ratio**: 1.7706
- **Max Drawdown %**: 24.3302
- **Profit Factor**: 1.6387564586355594
- **Trade Count**: 3097
- **Total Fees (quote)**: 11.6891
- **Maker Fees**: 5.8748
- **Taker Fees**: 5.8143
- **Fee Drag %**: 7.1566

## Objective Decomposition

- **Raw Score**: 68.0125
- **PnL Component**: 78.5446
- **Sharpe Component**: 0.8853
- **Drawdown Component**: -7.2991
- **Fee Drag Component**: -1.4313
- **Inventory Component**: -2.5136
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **1.1749**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 12.71 | 5.65 | 6.85 | 193 | 11.7082 |
| 1 | 2.79 | 1.20 | 16.71 | 227 | -6.7528 |
| 2 | 37.95 | 7.65 | 14.51 | 262 | 32.7691 |
| 3 | 14.14 | 5.78 | 4.29 | 310 | 12.9493 |
| 4 | 1.75 | 0.97 | 10.82 | 281 | -2.6116 |
| 5 | 11.04 | 5.67 | 5.31 | 248 | 10.6218 |
| 6 | -3.06 | -0.97 | 10.40 | 113 | -8.4938 |
| 7 | -11.59 | -2.78 | 20.16 | 366 | -22.7008 |
| 8 | 2.71 | 3.90 | 2.06 | 97 | 3.3594 |
| 9 | 5.76 | 4.26 | 2.02 | 41 | 6.7709 |

## Stress Test Results

Worst Scenario: **very_low_liquidity** (score: 26.1436)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 74.97 | 1.71 | 24.83 | 63.5181 |
| fees_2x | 71.34 | 1.66 | 25.46 | 58.9185 |
| latency_plus1 | 84.06 | 1.82 | 23.20 | 73.7731 |
| latency_plus2 | 66.60 | 1.57 | 25.08 | 55.5277 |
| latency_plus3 | 104.84 | 2.46 | 19.63 | 96.6445 |
| low_liquidity | 71.05 | 1.79 | 23.45 | 61.2764 |
| very_low_liquidity | 36.35 | 1.21 | 25.06 | 26.1436 |
| high_slippage | 69.57 | 1.63 | 25.79 | 58.4530 |
| extreme_slippage | 51.49 | 1.35 | 29.44 | 38.9591 |
| combined_adverse | 53.12 | 1.46 | 24.66 | 42.0187 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
