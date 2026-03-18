# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_v1

Generated: 2026-03-18 17:50:40 UTC

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 55189
- **dataset_hash**: 306d51bff085b8dc26f9799beb11ca98199d3a9d6371a645d35d5d8cd53dfa0f
- **n_trials_phase1**: 3000
- **n_candidates_stressed**: 50
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 33.86935372835636
- **search_controller_compat**: False
- **stress_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.503027103683293 |
| buy_n_levels | 2 |
| buy_side_weight | 0.21036729511007715 |
| buy_spread_base | 0.5246018106371712 |
| buy_spread_ratio | 1.8559869652557075 |
| cooldown_time | 175 |
| executor_refresh_time | 1056 |
| macd_fast | 29 |
| macd_signal | 27 |
| macd_slow | 84 |
| natr_length | 10 |
| sell_n_levels | 6 |
| sell_spread_base | 0.29956342474354 |
| sell_spread_ratio | 1.6692074247698259 |
| stop_loss | 0.1673752686462858 |
| take_profit | 0.06790358109189269 |
| time_limit | 156613 |
| total_amount_quote | 33.86935372835636 |
| trailing_stop_activation | 0.0493640583868715 |
| trailing_stop_delta | 0.0020676280720837007 |

## Best Metrics

- **PnL %**: 4455.4316
- **Net PnL (quote)**: 1509.0259
- **Sharpe Ratio**: 5.7207
- **Max Drawdown %**: 50.6537
- **Profit Factor**: 1.2928094267369383
- **Trade Count**: 21321
- **Total Fees (quote)**: 506.9902
- **Maker Fees**: 174.8495
- **Taker Fees**: 332.1407
- **Fee Drag %**: 1496.8996

## Objective Decomposition

- **Raw Score**: 4140.1682
- **PnL Component**: 4455.4316
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -15.1961
- **Fee Drag Component**: -299.3799
- **Inventory Component**: -2.9259
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **197.6583**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 454.93 | 20.42 | 8.14 | 1111 | 440.8328 | n/a |
| 1 | 268.43 | 27.30 | 12.24 | 871 | 254.3961 | n/a |
| 2 | 297.30 | 17.65 | 7.87 | 962 | 282.6501 | n/a |
| 3 | 408.39 | 26.02 | 7.92 | 843 | 395.4312 | n/a |
| 4 | 157.46 | 28.42 | 5.40 | 896 | 145.3889 | n/a |
| 5 | 414.01 | 32.99 | 8.66 | 959 | 398.7506 | n/a |
| 6 | 217.82 | 16.99 | 16.65 | 960 | 200.1945 | n/a |
| 7 | 220.50 | 27.12 | 5.39 | 952 | 207.4300 | n/a |
| 8 | 161.86 | 30.89 | 4.28 | 921 | 149.6309 | n/a |
| 9 | 201.59 | 35.46 | 3.40 | 945 | 189.6077 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus3** (score: 2039.0858)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3836.96 | 5.50 | 49.97 | 3387.9358 |
| fees_2x | 3205.97 | 5.33 | 49.33 | 2638.3975 |
| latency_plus1 | 4104.28 | 5.59 | 49.71 | 3814.2988 |
| latency_plus2 | 3466.92 | 5.25 | 51.89 | 3203.9016 |
| latency_plus3 | 2244.82 | 4.80 | 48.52 | 2039.0858 |
| low_liquidity | 4182.86 | 5.56 | 49.03 | 3893.8198 |
| very_low_liquidity | 3864.50 | 5.47 | 48.38 | 3601.4693 |
| high_slippage | 4374.70 | 5.65 | 51.03 | 4059.3225 |
| extreme_slippage | 3839.33 | 5.55 | 49.91 | 3534.7165 |
| combined_adverse | 2776.00 | 5.09 | 46.99 | 2410.9352 |

## Stop-Ship Checks

- dataset_audit: **FAIL**
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
