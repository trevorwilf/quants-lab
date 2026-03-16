# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_nonkyc_v2

Generated: 2026-03-15 23:31:53 UTC

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
| amount_skew | 1.9064158125738626 |
| buy_n_levels | 6 |
| buy_side_weight | 0.5041922400516616 |
| buy_spread_base | 0.29108863775520694 |
| buy_spread_ratio | 1.4226999633525188 |
| cooldown_time | 253.29338935936653 |
| executor_refresh_time | 1115.000515225536 |
| macd_fast | 44 |
| macd_signal | 21 |
| macd_slow | 61 |
| natr_length | 42 |
| sell_n_levels | 2 |
| sell_spread_base | 0.2036059123919964 |
| sell_spread_ratio | 1.264384911774311 |
| stop_loss | 0.1876808611684624 |
| take_profit | 0.09750939809239499 |
| time_limit | 151130 |
| total_amount_quote | 170.29948144066157 |
| trailing_stop_activation | 0.04140165921989172 |
| trailing_stop_delta | 0.003197167498462713 |

## Best Metrics

- **PnL %**: 3379.0898
- **Net PnL (quote)**: 5754.5725
- **Sharpe Ratio**: 5.5361
- **Max Drawdown %**: 50.4494
- **Profit Factor**: 1.2576725681209082
- **Trade Count**: 43292
- **Total Fees (quote)**: 2183.1171
- **Maker Fees**: 760.8422
- **Taker Fees**: 1422.2749
- **Fee Drag %**: 1281.9282

## Objective Decomposition

- **Raw Score**: 3105.6205
- **PnL Component**: 3379.0898
- **Sharpe Component**: 2.5000
- **Drawdown Component**: -15.1348
- **Fee Drag Component**: -256.3856
- **Inventory Component**: -4.1605
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **294.3823**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 543.93 | 22.59 | 13.02 | 3105 | 526.0184 | n/a |
| 1 | 344.21 | 24.17 | 11.26 | 2526 | 323.2328 | n/a |
| 2 | 393.51 | 18.68 | 15.05 | 2704 | 369.9112 | n/a |
| 3 | 504.66 | 25.41 | 7.30 | 2451 | 485.3947 | n/a |
| 4 | 287.45 | 28.09 | 11.34 | 2643 | 265.5319 | n/a |
| 5 | 617.06 | 29.20 | 7.96 | 2731 | 595.0579 | n/a |
| 6 | 323.59 | 17.11 | 18.13 | 2552 | 299.1912 | n/a |
| 7 | 297.55 | 24.55 | 18.62 | 2694 | 273.7927 | n/a |
| 8 | 179.84 | 26.01 | 6.96 | 2428 | 161.6401 | n/a |

## Stress Test Results

Worst Scenario: **combined_adverse** (score: 1409.9449)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2990.47 | 5.28 | 52.26 | 2595.4406 |
| fees_2x | 2576.51 | 5.04 | 53.60 | 2067.2759 |
| latency_plus1 | 3057.25 | 5.32 | 52.33 | 2808.4565 |
| latency_plus2 | 2437.72 | 5.02 | 50.94 | 2220.0976 |
| latency_plus3 | 1734.78 | 4.67 | 51.90 | 1552.4014 |
| low_liquidity | 2611.83 | 5.15 | 50.86 | 2386.8211 |
| very_low_liquidity | 1624.41 | 4.48 | 52.86 | 1458.7669 |
| high_slippage | 3277.10 | 5.43 | 51.66 | 3004.7130 |
| extreme_slippage | 2990.20 | 5.29 | 52.30 | 2721.2750 |
| combined_adverse | 1694.81 | 4.52 | 52.35 | 1409.9449 |

## Stop-Ship Checks

- dataset_audit: PASS
- feature_parity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: **FAIL**
- walkforward_robust: PASS
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: **FAIL**

> **WARNING**: One or more stop-ship checks FAILED.
