# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_sweep_nonkyc_v1

Generated: 2026-03-09 20:59:09 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 53981
- **dataset_hash**: b80f9dba1256abfe27d121cbaad2c0e29f1c821c7dae056a837a92434814804c
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.19961010512189 |
| buy_n_levels | 3 |
| buy_side_weight | 0.5935294305735271 |
| buy_spread_base | 0.3948671472951837 |
| buy_spread_ratio | 1.9716564389017464 |
| cooldown_time | 81.97336731170662 |
| executor_refresh_time | 541.9721720219766 |
| macd_fast | 7 |
| macd_signal | 9 |
| macd_slow | 77 |
| natr_length | 30 |
| sell_n_levels | 8 |
| sell_spread_base | 0.7003853477291294 |
| sell_spread_ratio | 2.8618038668040744 |
| stop_loss | 0.2060752183232005 |
| take_profit | 0.12034915956507898 |
| time_limit | 129881 |
| total_amount_quote | 48.179459719152675 |
| trailing_stop_activation | 0.05828702318081648 |
| trailing_stop_delta | 0.005791335600899029 |

## Best Metrics

- **PnL %**: 6700.1355
- **Net PnL (quote)**: 3228.0891
- **Sharpe Ratio**: 4.6825
- **Max Drawdown %**: 51.9571
- **Profit Factor**: 1.5020608356445715
- **Trade Count**: 29959
- **Total Fees (quote)**: 644.6195
- **Maker Fees**: 218.6135
- **Taker Fees**: 426.0060
- **Fee Drag %**: 1337.9549

## Objective Decomposition

- **Raw Score**: 6414.0474
- **PnL Component**: 6700.1355
- **Sharpe Component**: 2.3413
- **Drawdown Component**: -15.5871
- **Fee Drag Component**: -267.5910
- **Inventory Component**: -4.9077
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **242.6001**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 470.07 | 11.55 | 50.01 | 1435 | 436.3150 |
| 1 | 361.79 | 14.63 | 15.46 | 1577 | 337.9669 |
| 2 | 174.79 | 14.09 | 13.91 | 1599 | 153.5068 |
| 3 | 231.02 | 16.04 | 26.97 | 1491 | 206.6528 |
| 4 | 450.72 | 23.06 | 27.34 | 1588 | 424.0325 |
| 5 | 276.73 | 18.32 | 13.33 | 1433 | 255.9231 |
| 6 | 257.91 | 18.41 | 16.31 | 1480 | 235.8782 |
| 7 | 596.70 | 11.61 | 12.07 | 1747 | 573.4337 |
| 8 | 631.40 | 21.60 | 10.47 | 1628 | 609.1167 |
| 9 | 273.35 | 15.99 | 28.13 | 1503 | 247.8071 |

## Stress Test Results

Worst Scenario: **latency_plus2** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5367.65 | 4.35 | 79.28 | 4973.0326 |
| fees_2x | 4820.83 | 4.15 | 84.96 | 4311.9622 |
| latency_plus1 | 4478.53 | 4.30 | 63.75 | 4252.6472 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 3751.76 | 4.08 | 78.40 | 3550.0327 |
| very_low_liquidity | 1523.01 | 3.41 | 85.25 | 1393.2594 |
| high_slippage | 6163.16 | 4.53 | 62.67 | 5882.7722 |
| extreme_slippage | 5667.90 | 4.44 | 64.64 | 5390.6776 |
| combined_adverse | -86.47 | -1.91 | 86.80 | -125.1869 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
