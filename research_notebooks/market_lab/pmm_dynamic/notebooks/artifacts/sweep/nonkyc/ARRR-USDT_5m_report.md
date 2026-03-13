# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_nonkyc_v1

Generated: 2026-03-09 14:55:10 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 52149
- **dataset_hash**: 90049ee0699af85e7b44f7d340e0ecb6e3684c75c2baeb15327d168c33511ef1
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.786515081741557 |
| buy_n_levels | 9 |
| buy_side_weight | 0.43313510573242653 |
| buy_spread_base | 0.4422409636473741 |
| buy_spread_ratio | 2.7795230624830056 |
| cooldown_time | 244.27591883332423 |
| executor_refresh_time | 973.5847645273673 |
| macd_fast | 31 |
| macd_signal | 22 |
| macd_slow | 57 |
| natr_length | 12 |
| sell_n_levels | 3 |
| sell_spread_base | 0.3349188837094918 |
| sell_spread_ratio | 1.2158693648232959 |
| stop_loss | 0.24357568021925105 |
| take_profit | 0.09140777759934406 |
| time_limit | 138190 |
| total_amount_quote | 42.06748937437969 |
| trailing_stop_activation | 0.05020507262030969 |
| trailing_stop_delta | 0.0010168897358866884 |

## Best Metrics

- **PnL %**: 3931.6168
- **Net PnL (quote)**: 1653.9325
- **Sharpe Ratio**: 5.8422
- **Max Drawdown %**: 45.2092
- **Profit Factor**: 1.1783218117943637
- **Trade Count**: 18117
- **Total Fees (quote)**: 707.2007
- **Maker Fees**: 247.8315
- **Taker Fees**: 459.3693
- **Fee Drag %**: 1681.1099

## Objective Decomposition

- **Raw Score**: 3579.7967
- **PnL Component**: 3931.6168
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -13.5628
- **Fee Drag Component**: -336.2220
- **Inventory Component**: -4.2534
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **383.9697**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective |
|------|-------|--------|----------|--------|-----------|
| 0 | 901.85 | 21.28 | 10.36 | 1237 | 879.6862 |
| 1 | 449.58 | 28.52 | 11.97 | 754 | 428.6764 |
| 2 | 472.91 | 20.01 | 13.99 | 882 | 446.7864 |
| 3 | 591.86 | 28.69 | 9.89 | 831 | 568.2793 |
| 4 | 227.11 | 26.57 | 10.82 | 861 | 204.0478 |
| 5 | 500.23 | 28.15 | 13.24 | 865 | 475.2675 |
| 6 | 367.91 | 16.97 | 27.52 | 829 | 339.2630 |
| 7 | 419.40 | 28.39 | 15.13 | 817 | 395.7066 |
| 8 | 195.92 | 26.29 | 7.49 | 809 | 174.7529 |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 1801.1192)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3241.59 | 5.58 | 44.86 | 2737.4615 |
| fees_2x | 2447.23 | 5.25 | 40.73 | 1801.1192 |
| latency_plus1 | 3306.07 | 5.61 | 43.97 | 2985.6979 |
| latency_plus2 | 2879.64 | 5.40 | 42.96 | 2590.8909 |
| latency_plus3 | 2196.39 | 4.96 | 42.09 | 1965.2020 |
| low_liquidity | 3412.33 | 5.63 | 43.00 | 3098.8385 |
| very_low_liquidity | 2887.93 | 5.24 | 41.80 | 2611.5618 |
| high_slippage | 3566.51 | 5.79 | 43.76 | 3219.1368 |
| extreme_slippage | 3282.28 | 5.60 | 44.95 | 2939.6491 |
| combined_adverse | 2251.55 | 5.04 | 41.55 | 1838.1030 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- determinism: PASS

> **WARNING**: One or more stop-ship checks FAILED.
