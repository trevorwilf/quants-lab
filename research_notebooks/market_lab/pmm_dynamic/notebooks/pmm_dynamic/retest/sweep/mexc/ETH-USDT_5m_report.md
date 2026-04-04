# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_retest_20260403

Generated: 2026-04-04 01:07:20 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T01:07:20.213475+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11538 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51858
- **dataset_hash**: dc62b023fc0f2e547b9b6a4e9abef1f948829abf14d840cf2c8ff3b9b2bf2cf3
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 124.58711670070733
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.362493338797819 |
| buy_n_levels | 4 |
| buy_side_weight | 0.37015237441459353 |
| buy_spread_base | 0.45005383204805804 |
| buy_spread_ratio | 1.5384042589849396 |
| cooldown_time | 263 |
| executor_refresh_time | 1113 |
| macd_fast | 10 |
| macd_signal | 25 |
| macd_slow | 44 |
| natr_length | 9 |
| sell_n_levels | 5 |
| sell_spread_base | 0.20509956620475822 |
| sell_spread_ratio | 1.2721929006896782 |
| stop_loss | 0.19233367955050198 |
| take_profit | 0.07232893528483389 |
| time_limit | 171896 |
| total_amount_quote | 124.58711670070733 |
| trailing_stop_activation | 0.012429874239817661 |
| trailing_stop_delta | 0.0011622089165612866 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 124.58711670070733 |
| Selected | 124.58711670070733 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2233.6535
- **Net PnL (quote)**: 2782.8445
- **Sharpe Ratio**: 14.3043
- **Max Drawdown %**: 18.9657
- **Profit Factor**: 2.130271886738809
- **Trade Count**: 21581
- **Total Fees (quote)**: 187.7936
- **Maker Fees**: 95.1802
- **Taker Fees**: 92.6134
- **Fee Drag %**: 150.7328

## Selected Candidate Single-Run Objective

- **Raw Score**: 1.9998
- **PnL Component**: 3.1500
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1422
- **Fee Drag Component**: -0.7537
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7120**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 201.44 | 38.20 | 5.70 | 2022 | 0.7479 | n/a |
| 1 | 271.17 | 24.76 | 5.19 | 1930 | 0.9617 | n/a |
| 2 | 220.78 | 27.63 | 4.29 | 2201 | 0.8198 | n/a |
| 3 | 144.53 | 43.59 | 3.02 | 2038 | 0.5623 | n/a |
| 4 | 181.70 | 43.10 | 4.21 | 1975 | 0.6905 | n/a |
| 5 | 340.68 | 34.44 | 12.42 | 2115 | 1.0674 | n/a |
| 6 | 190.90 | 44.71 | 5.12 | 2137 | 0.7124 | n/a |
| 7 | 229.99 | 47.82 | 4.35 | 2140 | 0.8412 | n/a |
| 8 | 193.73 | 52.28 | 5.26 | 1987 | 0.7269 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0143)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2215.46 | 14.22 | 18.83 | 1.6176 |
| fees_2x | 2179.41 | 14.04 | 18.66 | 1.2290 |
| latency_plus1 | 1985.46 | 13.73 | 19.10 | 1.9576 |
| latency_plus2 | 1636.25 | 13.09 | 18.80 | 1.8884 |
| latency_plus3 | 1330.96 | 12.13 | 19.00 | 1.7971 |
| low_liquidity | 2233.65 | 14.30 | 18.97 | 1.9998 |
| very_low_liquidity | 2233.65 | 14.30 | 18.97 | 1.9998 |
| high_slippage | 2134.58 | 14.06 | 18.53 | 1.9653 |
| extreme_slippage | 2020.54 | 13.70 | 18.62 | 1.9131 |
| combined_adverse | 1897.68 | 13.38 | 18.57 | 1.5881 |
| spread_widen_10bps | 2189.86 | 14.06 | 18.63 | 1.9865 |
| spread_widen_25bps | 2091.31 | 13.85 | 18.50 | 1.9489 |
| thin_book | 1419.40 | 12.45 | 19.27 | 1.8658 |
| very_thin_book | 596.67 | 9.30 | 20.44 | 1.3337 |
| entry_spread_stress | 2175.12 | 14.09 | 18.48 | 1.9780 |
| combined_market_deterioration | 1729.22 | 13.15 | 18.95 | 1.6231 |
| severe_adverse | 542.11 | 8.53 | 19.54 | 1.0143 |

## Holdout Validation

- **Holdout bars**: 8758
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0034)
- **Trend**: ranging (efficiency: 0.0075)
- **Best holdout score**: 1.9413 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.5070 | 1.5553 | 655.85 | 6.42 | 5004 |
| 1 | 1.0073 | 1.9262 | 1095.42 | 6.68 | 4187 |
| 2 | 0.9906 | 1.8279 | 950.52 | 7.34 | 3839 |
| 3 | 0.9862 | 1.7589 | 927.08 | 6.65 | 2711 |
| 4 | 0.9831 | 1.9413 | 1129.25 | 7.64 | 4399 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51858
- **Expected rows**: 51858
- **Missing rows**: 0
- **Forward-fill count**: 190
- **Forward-fill fraction**: 0.0036638512862046356
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.4843804600091093
- **PnL %**: 582.7022693470186
- **Trade count**: 4482

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.8899735633517942
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.9186, 1.8877 |
| sell_spread_base | 1.8945, 1.8805 |
| stop_loss | 1.8926, 1.8673 |
| take_profit | 1.8900, 1.8900 |
| executor_refresh_time | 1.9189, 1.8900 |
| cooldown_time | 1.8900, 1.8900 |
| total_amount_quote | 1.8830, 1.8539 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.32696484626357947
- **Max CV**: 0.8460249239900253
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2017 | 0.209803530916934 | 0.38387284680146017 | 0.2740856053278097 |
| buy_spread_ratio | 0.2568 | 1.2141616048195212 | 2.8653056222676243 | 1.689729354712797 |
| sell_spread_base | 0.3511 | 0.2018489530343248 | 0.5516209508032781 | 0.325438113201147 |
| sell_spread_ratio | 0.1160 | 1.2790152807179007 | 1.856946870684364 | 1.5210447591360456 |
| buy_side_weight | 0.1368 | 0.3435388599444915 | 0.4942133687662079 | 0.4173597847593994 |
| amount_skew | 0.1557 | 2.28441813306155 | 3.9816346672418317 | 3.346828419645747 |
| stop_loss | 0.2464 | 0.1042708605209258 | 0.24930504997273104 | 0.17681986869390276 |
| take_profit | 0.6771 | 0.01217951102080776 | 0.07602863901015078 | 0.02936935806874037 |
| executor_refresh_time | 0.2448 | 319.0 | 626.0 | 472.4 |
| cooldown_time | 0.3641 | 109.0 | 285.0 | 184.8 |
| total_amount_quote | 0.8460 | 28.88859590875303 | 207.74428579462216 | 67.65570872572584 |

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
- walkforward_positive_majority: PASS
- holdout_passed: PASS
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: PASS
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | 1.4843804600091093 | PASS |
| recent_pnl | >= 0 | 582.7022693470186 | PASS |
| recent_trades | >= 5 | 4482 | PASS |
| worst_stress | > -10 | 1.0142502963414608 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.5553 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0142502963414608 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.4843804600091093, pnl=582.7022693470186, trades=4482, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.32696484626357947 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51858 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | PASS | recent_28d | — | — |  |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35035
- **Holdout bars**: 8758
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T01:07:20.213475+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11538
