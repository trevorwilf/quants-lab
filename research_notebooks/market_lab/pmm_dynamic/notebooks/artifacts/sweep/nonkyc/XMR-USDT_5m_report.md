# PMM Dynamic Optimization Report: nonkyc_XMR-USDT_5m_sweep_nonkyc_v1

Generated: 2026-03-09 23:37:00 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 53920
- **dataset_hash**: 4334fce9321e6fffb53b9f58a707441303e2e467634c3af07e37c3cabfc520ce
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.2827108239128875 |
| buy_n_levels | 7 |
| buy_side_weight | 0.6037876460065899 |
| buy_spread_base | 0.4710797313639645 |
| buy_spread_ratio | 1.7786377343105126 |
| cooldown_time | 507.92664624376914 |
| executor_refresh_time | 1133.7246310782964 |
| macd_fast | 19 |
| macd_signal | 23 |
| macd_slow | 22 |
| natr_length | 26 |
| sell_n_levels | 3 |
| sell_spread_base | 0.3146008973702613 |
| sell_spread_ratio | 1.3813933793162037 |
| stop_loss | 0.20915047979012333 |
| take_profit | 0.11405038098235279 |
| time_limit | 171525 |
| total_amount_quote | 499.77029155051775 |
| trailing_stop_activation | 0.025220306335924154 |
| trailing_stop_delta | 0.0015820044635608036 |

## Best Metrics

- **PnL %**: 1258.5606
- **Net PnL (quote)**: 6289.9121
- **Sharpe Ratio**: 2.2026
- **Max Drawdown %**: 42.3193
- **Profit Factor**: 1.0957835706847479
- **Trade Count**: 32642
- **Total Fees (quote)**: 3714.4320
- **Maker Fees**: 1316.4085
- **Taker Fees**: 2398.0234
- **Fee Drag %**: 743.2278

## Objective Decomposition

- **Raw Score**: 1094.3103
- **PnL Component**: 1258.5606
- **Sharpe Component**: 1.1013
- **Drawdown Component**: -12.6958
- **Fee Drag Component**: -148.6456
- **Inventory Component**: -3.8524
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **41.9844**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 741.83 | 6.25 | 3.80 | 2049 | 733.3783 |
| 1 | 75.73 | 16.52 | 10.67 | 2021 | 63.8280 |
| 2 | 93.32 | 20.53 | 11.36 | 1860 | 82.7449 |
| 3 | 55.97 | 21.21 | 4.11 | 1863 | 48.1921 |
| 4 | 21.07 | 9.20 | 6.11 | 1875 | 12.5485 |
| 5 | 11.97 | 7.30 | 6.33 | 2077 | 2.8873 |
| 6 | 103.57 | 16.26 | 15.20 | 1843 | 89.9632 |
| 7 | 91.16 | 22.08 | 9.27 | 1820 | 80.9302 |
| 8 | 38.00 | 13.16 | 12.68 | 1936 | 26.8539 |
| 9 | 37.59 | 18.67 | 5.79 | 1930 | 29.0633 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 358.3063)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 945.03 | 1.98 | 42.64 | 713.9986 |
| fees_2x | 646.52 | 1.67 | 46.96 | 358.3063 |
| latency_plus1 | 978.77 | 2.16 | 43.70 | 831.8368 |
| latency_plus2 | 974.76 | 2.02 | 45.39 | 837.5856 |
| latency_plus3 | 730.27 | 2.03 | 45.77 | 610.1178 |
| low_liquidity | 1033.50 | 2.10 | 41.13 | 885.9772 |
| very_low_liquidity | 852.49 | 1.96 | 41.32 | 722.2790 |
| high_slippage | 1099.02 | 2.07 | 42.29 | 937.6456 |
| extreme_slippage | 905.48 | 1.93 | 42.54 | 748.0893 |
| combined_adverse | 588.52 | 1.69 | 44.99 | 402.5227 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
