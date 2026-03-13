# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_sweep_mexc_v2

Generated: 2026-03-09 06:54:03 UTC

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 53635
- **dataset_hash**: 12656bd238fb2572435bfb93400a2acdab43e77e498213f930c1c71c11202d5f
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0554811151355468 |
| buy_n_levels | 2 |
| buy_side_weight | 0.21215429024772645 |
| buy_spread_base | 0.31474466052928984 |
| buy_spread_ratio | 2.927774931264497 |
| cooldown_time | 1456.286106728841 |
| executor_refresh_time | 1132.9300688778308 |
| macd_fast | 12 |
| macd_signal | 9 |
| macd_slow | 20 |
| natr_length | 38 |
| sell_n_levels | 3 |
| sell_spread_base | 0.2869000240352802 |
| sell_spread_ratio | 1.4421107335084722 |
| stop_loss | 0.1749916775884484 |
| take_profit | 0.037834424382468354 |
| time_limit | 136280 |
| total_amount_quote | 199.85170089501645 |
| trailing_stop_activation | 0.03005401636935117 |
| trailing_stop_delta | 0.0010269725197449072 |

## Best Metrics

- **PnL %**: 407.5310
- **Net PnL (quote)**: 814.4576
- **Sharpe Ratio**: 8.3125
- **Max Drawdown %**: 13.1991
- **Profit Factor**: 1.1317526892631653
- **Trade Count**: 14445
- **Total Fees (quote)**: 149.7195
- **Maker Fees**: 79.9322
- **Taker Fees**: 69.7873
- **Fee Drag %**: 74.9153

## Objective Decomposition

- **Raw Score**: 388.9032
- **PnL Component**: 407.5310
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -3.9597
- **Fee Drag Component**: -14.9831
- **Inventory Component**: -2.1115
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **28.3444**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 40.06 | 21.62 | 5.89 | 1027 | 37.5650 |
| 1 | 45.75 | 16.29 | 6.79 | 998 | 43.1206 |
| 2 | 36.27 | 14.84 | 7.16 | 1043 | 33.6591 |
| 3 | 47.58 | 22.52 | 5.23 | 981 | 45.6737 |
| 4 | 33.28 | 11.84 | 4.55 | 1011 | 31.6559 |
| 5 | 11.15 | 13.56 | 2.85 | 1123 | 9.6016 |
| 6 | 1.06 | 1.41 | 5.99 | 1042 | -3.4083 |
| 7 | 32.90 | 11.74 | 8.46 | 1047 | 29.3476 |
| 8 | 28.21 | 12.22 | 5.78 | 1002 | 25.8681 |
| 9 | 73.32 | 30.74 | 4.66 | 1054 | 71.5908 |

## Stress Test Results

Worst Scenario: **combined_adverse** (score: 176.5723)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 376.97 | 8.18 | 12.14 | 351.5607 |
| fees_2x | 352.96 | 7.70 | 12.84 | 320.5044 |
| latency_plus1 | 281.10 | 6.90 | 13.68 | 264.1288 |
| latency_plus2 | 229.26 | 6.12 | 13.19 | 213.8997 |
| latency_plus3 | 212.34 | 5.74 | 15.32 | 197.1178 |
| low_liquidity | 407.53 | 8.31 | 13.20 | 388.9032 |
| very_low_liquidity | 407.53 | 8.31 | 13.20 | 388.9032 |
| high_slippage | 336.14 | 7.56 | 14.83 | 317.4098 |
| extreme_slippage | 200.56 | 5.21 | 23.56 | 179.9384 |
| combined_adverse | 199.51 | 5.61 | 14.16 | 176.5723 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
