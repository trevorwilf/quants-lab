# PMM Dynamic Optimization Report: nonkyc_ARRR-USDT_5m_sweep_v1

Generated: 2026-03-29 06:14:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T06:14:05.775605+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 13612 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: d740757a1c8c93ad6c6ccb0adcd5f1a1fd4dcb8d72fbaf57730747b8639653ad
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 164.01481551910734
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.8098835928964505 |
| buy_n_levels | 4 |
| buy_side_weight | 0.4088981198075514 |
| buy_spread_base | 0.21722981652066783 |
| buy_spread_ratio | 1.2422450229226094 |
| cooldown_time | 449 |
| executor_refresh_time | 1114 |
| macd_fast | 49 |
| macd_signal | 25 |
| macd_slow | 82 |
| natr_length | 14 |
| sell_n_levels | 3 |
| sell_spread_base | 0.2311280865715924 |
| sell_spread_ratio | 1.6571886972870227 |
| stop_loss | 0.16027988594821432 |
| take_profit | 0.031534844825905205 |
| time_limit | 166816 |
| total_amount_quote | 164.01481551910734 |
| trailing_stop_activation | 0.03781742205324969 |
| trailing_stop_delta | 0.003361303929512857 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 164.01481551910734 |
| Selected | 164.01481551910734 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3947.9127
- **Net PnL (quote)**: 6475.1617
- **Sharpe Ratio**: 6.0081
- **Max Drawdown %**: 42.3388
- **Profit Factor**: 1.4326646597106552
- **Trade Count**: 28294
- **Total Fees (quote)**: 1241.4192
- **Maker Fees**: 561.9677
- **Taker Fees**: 679.4515
- **Fee Drag %**: 756.8945

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.6663
- **PnL Component**: 3.7008
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.3175
- **Fee Drag Component**: -3.7845
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7451**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 333.85 | 18.16 | 26.84 | 2625 | 0.5876 | n/a |
| 1 | 416.86 | 17.08 | 22.37 | 2700 | 0.7839 | n/a |
| 2 | 483.77 | 25.16 | 11.68 | 2627 | 1.0163 | n/a |
| 3 | 555.99 | 17.22 | 9.69 | 2777 | 1.1472 | n/a |
| 4 | 734.10 | 17.04 | 31.11 | 2828 | 1.1385 | n/a |
| 5 | 385.42 | 22.68 | 11.59 | 2569 | 0.8355 | n/a |
| 6 | 370.77 | 24.85 | 8.80 | 2501 | 0.8541 | n/a |
| 7 | 291.80 | 25.87 | 5.54 | 2408 | 0.6970 | n/a |
| 8 | 192.85 | 22.03 | 8.91 | 2390 | 0.4013 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -4.4009)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3727.26 | 5.91 | 42.72 | -2.5690 |
| fees_2x | 3598.95 | 5.79 | 45.09 | -4.4009 |
| latency_plus1 | 3401.56 | 5.82 | 46.56 | -0.4271 |
| latency_plus2 | 2932.82 | 5.63 | 47.90 | -0.1158 |
| latency_plus3 | 2328.79 | 5.30 | 48.06 | 0.0762 |
| low_liquidity | 3246.64 | 5.73 | 41.03 | -0.1625 |
| very_low_liquidity | 2384.29 | 5.34 | 41.37 | 0.3464 |
| high_slippage | 3889.91 | 5.99 | 43.40 | -0.6702 |
| extreme_slippage | 3817.65 | 5.92 | 42.85 | -0.6501 |
| combined_adverse | 2632.98 | 5.40 | 42.08 | -1.2876 |
| spread_widen_10bps | 3836.43 | 5.96 | 42.21 | -0.6676 |
| spread_widen_25bps | 3842.63 | 5.92 | 43.03 | -0.6795 |
| thin_book | 2394.03 | 5.23 | 46.06 | 0.3648 |
| very_thin_book | 1244.27 | 4.51 | 45.24 | 0.8915 |
| entry_spread_stress | 3812.50 | 5.95 | 41.87 | -0.6710 |
| combined_market_deterioration | 2795.37 | 5.43 | 49.43 | -1.5222 |
| severe_adverse | 1309.77 | 4.49 | 53.53 | -0.4704 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0084)
- **Trend**: ranging (efficiency: 0.0148)
- **Best holdout score**: 1.0235 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -2.5336 | 0.9663 | 823.85 | 12.04 | 5824 |
| 1 | 1.2005 | 0.8311 | 1767.14 | 10.70 | 5658 |
| 2 | 1.1969 | 1.0235 | 1539.21 | 13.84 | 2303 |
| 3 | 1.1922 | 0.9045 | 1717.69 | 13.94 | 3740 |
| 4 | 1.1902 | 0.9616 | 1456.21 | 14.10 | 4045 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 517
- **Forward-fill fraction**: 0.009972801450589302
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.8642651482329025
- **PnL %**: 682.6612327087907
- **Trade count**: 5057

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -3.118477069625753
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -3.0553, -3.2083 |
| sell_spread_base | -2.9555, -3.3022 |
| stop_loss | -3.0217, -3.1878 |
| take_profit | -3.3613, -2.9578 |
| executor_refresh_time | -2.6940, -3.1185 |
| cooldown_time | -3.1185, -3.1185 |
| total_amount_quote | -3.0457, -3.2440 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.27293706809440565
- **Max CV**: 0.5784699967963469
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2128 | 0.21314524011526176 | 0.44620810223061724 | 0.32594292704286076 |
| buy_spread_ratio | 0.1109 | 1.2019507057879626 | 1.7555064401234055 | 1.431017604536588 |
| sell_spread_base | 0.1325 | 0.21148580596689173 | 0.29566967397757304 | 0.2591968446882523 |
| sell_spread_ratio | 0.1622 | 1.2167172686004437 | 1.983786158674543 | 1.5112471869608743 |
| buy_side_weight | 0.1079 | 0.3211227045452902 | 0.42360642951841265 | 0.3830276914154388 |
| amount_skew | 0.2065 | 1.614664115060915 | 3.4978031717123703 | 2.7813870140727337 |
| stop_loss | 0.1526 | 0.1434447795120319 | 0.2401130548771886 | 0.1999637248851328 |
| take_profit | 0.4859 | 0.02842324932173935 | 0.13177122053042692 | 0.07019532634727639 |
| executor_refresh_time | 0.3828 | 315.0 | 1129.0 | 646.8 |
| cooldown_time | 0.5785 | 69.0 | 523.0 | 279.3 |
| total_amount_quote | 0.4698 | 29.940956181088204 | 106.18767056191172 | 56.05227100557247 |

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
| recent_objective | > 0 | 0.8642651482329025 | PASS |
| recent_pnl | >= 0 | 682.6612327087907 | PASS |
| recent_trades | >= 5 | 5057 | PASS |
| worst_stress | > -10 | -4.400934382724081 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.9663 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-4.400934382724081 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.8642651482329025, pnl=682.6612327087907, trades=5057, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.27293706809440565 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
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
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T06:14:05.775605+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 13612
