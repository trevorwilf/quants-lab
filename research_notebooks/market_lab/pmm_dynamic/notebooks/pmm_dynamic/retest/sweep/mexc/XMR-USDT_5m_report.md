# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_retest_20260403

Generated: 2026-04-04 05:08:22 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T05:08:22.002716+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 5904 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51869
- **dataset_hash**: 70b64b77fbcde69ce93c1c81743ac4156429c024795ec72fd2dc7903be9bcefb
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 540.2856168044839
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.499662564066943 |
| buy_n_levels | 3 |
| buy_side_weight | 0.38665089035276834 |
| buy_spread_base | 0.2630847488338121 |
| buy_spread_ratio | 1.2243177349255032 |
| cooldown_time | 168 |
| executor_refresh_time | 1095 |
| macd_fast | 28 |
| macd_signal | 13 |
| macd_slow | 30 |
| natr_length | 36 |
| sell_n_levels | 2 |
| sell_spread_base | 0.3569094011715635 |
| sell_spread_ratio | 1.5655962935775962 |
| stop_loss | 0.15610797119048705 |
| take_profit | 0.05752298443444811 |
| time_limit | 172165 |
| total_amount_quote | 540.2856168044839 |
| trailing_stop_activation | 0.024938468905514634 |
| trailing_stop_delta | 0.0010092704258353228 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 540.2856168044839 |
| Selected | 540.2856168044839 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4193.0950
- **Net PnL (quote)**: 22654.6891
- **Sharpe Ratio**: 11.4512
- **Max Drawdown %**: 35.8410
- **Profit Factor**: 1.4678099065005186
- **Trade Count**: 23349
- **Total Fees (quote)**: 888.7877
- **Maker Fees**: 447.8525
- **Taker Fees**: 440.9352
- **Fee Drag %**: 164.5033

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.4109
- **PnL Component**: 3.7596
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2688
- **Fee Drag Component**: -0.8225
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.9444**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 443.82 | 41.22 | 10.72 | 2585 | 1.2776 | n/a |
| 1 | 304.08 | 40.12 | 4.15 | 2474 | 1.0379 | n/a |
| 2 | 278.27 | 43.67 | 6.15 | 2357 | 0.9612 | n/a |
| 3 | 243.66 | 45.62 | 6.06 | 2395 | 0.8696 | n/a |
| 4 | 490.67 | 31.75 | 14.48 | 2410 | 1.3288 | n/a |
| 5 | 403.71 | 30.46 | 21.92 | 2483 | 1.1183 | n/a |
| 6 | 301.43 | 43.92 | 8.02 | 2552 | 1.0023 | n/a |
| 7 | 275.15 | 44.67 | 7.58 | 2491 | 0.9406 | n/a |
| 8 | 194.38 | 40.95 | 6.23 | 2555 | 0.7107 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: 1.5825)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4185.35 | 11.42 | 36.19 | 1.9917 |
| fees_2x | 4133.85 | 11.39 | 35.58 | 1.5825 |
| latency_plus1 | 3723.41 | 11.12 | 34.88 | 2.3885 |
| latency_plus2 | 3107.08 | 10.54 | 34.63 | 2.3210 |
| latency_plus3 | 2564.51 | 9.94 | 34.68 | 2.2563 |
| low_liquidity | 4123.45 | 11.36 | 36.02 | 2.4290 |
| very_low_liquidity | 3815.20 | 10.98 | 36.37 | 2.4140 |
| high_slippage | 4133.03 | 11.39 | 35.21 | 2.4092 |
| extreme_slippage | 3855.55 | 11.19 | 34.25 | 2.3561 |
| combined_adverse | 3408.92 | 10.73 | 35.06 | 1.9936 |
| spread_widen_10bps | 4117.82 | 11.39 | 35.03 | 2.4041 |
| spread_widen_25bps | 3888.25 | 11.07 | 34.22 | 2.3634 |
| thin_book | 2665.38 | 9.89 | 37.72 | 2.3042 |
| very_thin_book | 1129.85 | 7.70 | 37.92 | 1.7527 |
| entry_spread_stress | 4033.31 | 11.26 | 34.71 | 2.3895 |
| combined_market_deterioration | 3328.03 | 10.47 | 36.75 | 2.0655 |
| severe_adverse | 1197.96 | 7.61 | 36.41 | 1.5991 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0045)
- **Best holdout score**: 1.9956 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.9967 | 1.6952 | 823.16 | 13.85 | 5489 |
| 1 | 1.2658 | 1.9956 | 1191.80 | 9.40 | 5501 |
| 2 | 1.2441 | 1.8582 | 1005.18 | 7.78 | 2418 |
| 3 | 1.2096 | 1.9252 | 1099.62 | 9.58 | 6528 |
| 4 | 1.1654 | 1.7585 | 887.68 | 11.77 | 2793 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51869
- **Expected rows**: 51910
- **Missing rows**: 41
- **Forward-fill count**: 66
- **Forward-fill fraction**: 0.001272436329985155
- **Longest gap (seconds)**: 12600

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.0170028791412289
- **PnL %**: 333.45800559476015
- **Trade count**: 5151

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.9366029617030198
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.9436, 1.9296 |
| sell_spread_base | 1.9299, 1.9196 |
| stop_loss | 1.9401, 1.9225 |
| take_profit | 1.9366, 1.9366 |
| executor_refresh_time | 1.9585, 1.9366 |
| cooldown_time | 1.9366, 1.9366 |
| total_amount_quote | 1.9285, 1.9444 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33108747863092103
- **Max CV**: 0.7096265088588349
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4048 | 0.20283828116659147 | 0.5960009795342618 | 0.33870959175710325 |
| buy_spread_ratio | 0.2531 | 1.2744361865283955 | 2.683676742520726 | 1.6999193291977335 |
| sell_spread_base | 0.2872 | 0.21053340136045828 | 0.5369379811811492 | 0.3617154656928857 |
| sell_spread_ratio | 0.2020 | 1.2104751563948362 | 2.2809145937981405 | 1.7428263408513118 |
| buy_side_weight | 0.1870 | 0.30489715897054503 | 0.595451912425643 | 0.44650562353523676 |
| amount_skew | 0.1280 | 2.702140866554756 | 3.964527790205862 | 3.476445931689611 |
| stop_loss | 0.2985 | 0.06465600588058994 | 0.20053261184878626 | 0.14286094437298355 |
| take_profit | 0.5431 | 0.021970991940722884 | 0.1470460164076899 | 0.07154052241325229 |
| executor_refresh_time | 0.2970 | 335.0 | 824.0 | 494.4 |
| cooldown_time | 0.3316 | 88.0 | 274.0 | 165.8 |
| total_amount_quote | 0.7096 | 25.255922450985803 | 186.85814618498165 | 82.76579450266316 |

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
| recent_objective | > 0 | 1.0170028791412289 | PASS |
| recent_pnl | >= 0 | 333.45800559476015 | PASS |
| recent_trades | >= 5 | 5151 | PASS |
| worst_stress | > -10 | 1.5824601673269247 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.6952 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=1.5824601673269247 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.0170028791412289, pnl=333.45800559476015, trades=5151, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33108747863092103 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51869 |  |
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
- **Dev bars**: 35076
- **Holdout bars**: 8769
- **Recent 28d bars**: 8024

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-04T05:08:22.002716+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 5904
