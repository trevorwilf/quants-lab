# PMM Dynamic Optimization Report: nonkyc_ENA-USDT_5m_sweep_v1

Generated: 2026-03-29 08:53:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T08:53:16.258877+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11329 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ENA-USDT
- **interval**: 5m
- **n_candles**: 49401
- **dataset_hash**: a9780325ab52b871e3823aa2ca1a6d4df38f0d750f65f245468713d98e106e59
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 971.8537399288446
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.9613675831176702 |
| buy_n_levels | 7 |
| buy_side_weight | 0.23913805047796804 |
| buy_spread_base | 3.7226093376704767 |
| buy_spread_ratio | 1.8392216178485563 |
| cooldown_time | 6694 |
| executor_refresh_time | 8477 |
| macd_fast | 6 |
| macd_signal | 27 |
| macd_slow | 23 |
| natr_length | 23 |
| sell_n_levels | 5 |
| sell_spread_base | 4.84218742170049 |
| sell_spread_ratio | 1.8166225513585683 |
| stop_loss | 0.018201785892185705 |
| take_profit | 0.005050297148457252 |
| time_limit | 98531 |
| total_amount_quote | 971.8537399288446 |
| trailing_stop_activation | 0.0780019574506971 |
| trailing_stop_delta | 0.0018240772036807304 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 971.8537399288446 |
| Selected | 971.8537399288446 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.8559
- **Net PnL (quote)**: -27.7549
- **Sharpe Ratio**: -3.2829
- **Max Drawdown %**: 2.8625
- **Profit Factor**: 0.36973333731761976
- **Trade Count**: 634
- **Total Fees (quote)**: 16.8184
- **Maker Fees**: 12.7783
- **Taker Fees**: 4.0401
- **Fee Drag %**: 1.7305

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0623
- **PnL Component**: -0.0290
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0215
- **Fee Drag Component**: -0.0087
- **Inventory Component**: -0.0032
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0150**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.49 | -11.13 | 0.61 | 130 | -0.0120 | n/a |
| 1 | -0.02 | -0.57 | 0.19 | 77 | -0.0043 | n/a |
| 2 | -0.02 | -0.80 | 0.10 | 59 | -0.0058 | n/a |
| 3 | -0.13 | -7.56 | 0.14 | 60 | -0.0044 | n/a |
| 4 | -0.37 | -8.99 | 0.43 | 76 | -0.0128 | n/a |
| 5 | -0.58 | -11.78 | 0.68 | 76 | -0.0172 | n/a |
| 6 | -0.48 | -10.97 | 0.53 | 391 | -0.0165 | n/a |
| 7 | -0.51 | -9.06 | 0.59 | 82 | -0.0153 | n/a |
| 8 | -1.73 | -17.60 | 1.78 | 111 | -0.0388 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1774)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.72 | -4.27 | 3.72 | -0.0821 |
| fees_2x | -4.59 | -5.24 | 4.59 | -0.1019 |
| latency_plus1 | -2.86 | -3.29 | 2.86 | -0.0623 |
| latency_plus2 | -2.87 | -3.29 | 2.87 | -0.0625 |
| latency_plus3 | -2.86 | -3.29 | 2.87 | -0.0624 |
| low_liquidity | -3.95 | -3.65 | 3.96 | -0.0840 |
| very_low_liquidity | -4.42 | -3.71 | 4.48 | -0.0924 |
| high_slippage | -2.96 | -3.40 | 2.96 | -0.0642 |
| extreme_slippage | -3.17 | -3.64 | 3.17 | -0.0679 |
| combined_adverse | -5.04 | -4.63 | 5.04 | -0.1083 |
| spread_widen_10bps | -3.54 | -4.09 | 3.55 | -0.0759 |
| spread_widen_25bps | -5.85 | -4.24 | 6.00 | -0.1216 |
| thin_book | -4.94 | -5.89 | 4.94 | -0.0980 |
| very_thin_book | -5.18 | -3.04 | 5.23 | -0.1005 |
| entry_spread_stress | -4.08 | -4.66 | 4.09 | -0.0857 |
| combined_market_deterioration | -5.71 | -0.56 | 10.62 | -0.1550 |
| severe_adverse | -8.67 | -8.73 | 8.67 | -0.1774 |

## Holdout Validation

- **Holdout bars**: 8267
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0183)
- **Best holdout score**: -0.0128 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1199 | -0.0205 | -0.69 | 0.73 | 1353 |
| 1 | -0.0051 | -0.0129 | -0.50 | 0.52 | 150 |
| 2 | -0.0052 | -0.0138 | -0.47 | 0.56 | 179 |
| 3 | -0.0054 | -0.0128 | -0.41 | 0.42 | 172 |
| 4 | -0.0056 | -0.0349 | -1.37 | 1.49 | 333 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 49401
- **Expected rows**: 49401
- **Missing rows**: 0
- **Forward-fill count**: 129
- **Forward-fill fraction**: 0.002611283172405417
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0406 <= 0; recent PnL -1.8617% < 0
- **Objective score**: -0.04059150397516208
- **PnL %**: -1.861677711791716
- **Trade count**: 181

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.1263164304746954
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1203, -0.1451 |
| sell_spread_base | -0.1029, -0.1477 |
| stop_loss | -0.1415, -0.1326 |
| take_profit | -0.1527, -0.1081 |
| executor_refresh_time | -0.1262, -0.1395 |
| cooldown_time | -0.1393, -0.1889 |
| total_amount_quote | -0.1259, -0.0968 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2973362268098139
- **Max CV**: 0.9002223668268643
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1041 | 3.2366105424270577 | 4.5679978529407625 | 3.5993407302192644 |
| buy_spread_ratio | 0.0705 | 1.8633668130092524 | 2.3326430830967486 | 2.097950489677486 |
| sell_spread_base | 0.2994 | 1.9482366876694612 | 5.300585581474222 | 3.926925769821577 |
| sell_spread_ratio | 0.1884 | 1.65864839655982 | 2.9326428994386724 | 2.2162138823373594 |
| buy_side_weight | 0.4120 | 0.21233825990011918 | 0.6378051642118462 | 0.39242519045363883 |
| amount_skew | 0.1769 | 2.1740520491913853 | 3.903237991125022 | 3.266577123998105 |
| stop_loss | 0.3173 | 0.010411844629037052 | 0.0237480982041801 | 0.014838707367540982 |
| take_profit | 0.1524 | 0.005117224529464627 | 0.007628790959819789 | 0.006276533638551292 |
| executor_refresh_time | 0.5497 | 655.0 | 10998.0 | 6536.8 |
| cooldown_time | 0.9002 | 60.0 | 3941.0 | 1406.3 |
| total_amount_quote | 0.0997 | 720.5367610120719 | 978.1227862974537 | 867.1755398242188 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- walkforward_robust: PASS
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.04059150397516208 | FAIL |
| recent_pnl | >= 0 | -1.861677711791716 | FAIL |
| recent_trades | >= 5 | 181 | PASS |
| worst_stress | > -10 | -0.1774241070695179 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.020523033162686777 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.1774241070695179 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.04059150397516208, pnl=-1.861677711791716, trades=181, reason=recent objective score -0.0406 <= 0; recent PnL -1.8617% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2973362268098139 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 49401 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0406 <= 0; recent PnL -1.8617% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 33069
- **Holdout bars**: 8267
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T08:53:16.258877+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11329
