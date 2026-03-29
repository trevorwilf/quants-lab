# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_sweep_v1

Generated: 2026-03-28 08:47:35 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T08:47:35.368767+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11368 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: ce6e1c17960585bb1f411669557e1f872bf0e296736f7f45211ee9cc64bf3d23
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 36.32181348258378
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6146642142631134 |
| buy_n_levels | 10 |
| buy_side_weight | 0.47005590875853953 |
| buy_spread_base | 0.4533929341390052 |
| buy_spread_ratio | 1.5942482174911181 |
| cooldown_time | 434 |
| executor_refresh_time | 1021 |
| macd_fast | 34 |
| macd_signal | 5 |
| macd_slow | 36 |
| natr_length | 39 |
| sell_n_levels | 6 |
| sell_spread_base | 0.43222988131297807 |
| sell_spread_ratio | 1.3199222727512703 |
| stop_loss | 0.12432176382680878 |
| take_profit | 0.04829645212920719 |
| time_limit | 158613 |
| total_amount_quote | 36.32181348258378 |
| trailing_stop_activation | 0.015148105590758385 |
| trailing_stop_delta | 0.0021867241045018583 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 36.32181348258378 |
| Selected | 36.32181348258378 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2382.0207
- **Net PnL (quote)**: 865.1931
- **Sharpe Ratio**: 10.8708
- **Max Drawdown %**: 26.9878
- **Profit Factor**: 1.7266497920901471
- **Trade Count**: 7858
- **Total Fees (quote)**: 55.4438
- **Maker Fees**: 28.0243
- **Taker Fees**: 27.4195
- **Fee Drag %**: 152.6461

## Selected Candidate Single-Run Objective

- **Raw Score**: 1.9918
- **PnL Component**: 3.2117
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.2024
- **Fee Drag Component**: -0.7632
- **Inventory Component**: -0.2500
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.4674**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 326.55 | 45.74 | 7.76 | 809 | 1.0631 | n/a |
| 1 | 251.09 | 36.51 | 4.34 | 743 | 0.9007 | n/a |
| 2 | 190.73 | 45.77 | 4.48 | 797 | 0.7066 | n/a |
| 3 | 54.15 | 31.11 | 4.59 | 723 | 0.0809 | n/a |
| 4 | 76.76 | 17.78 | 5.05 | 774 | 0.2088 | n/a |
| 5 | 171.66 | 38.54 | 8.60 | 771 | 0.6118 | n/a |
| 6 | 204.03 | 35.05 | 9.20 | 763 | 0.7177 | n/a |
| 7 | 148.06 | 39.07 | 5.32 | 709 | 0.5496 | n/a |
| 8 | 66.97 | 30.87 | 3.28 | 718 | 0.1716 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 0.7507)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2380.08 | 11.35 | 24.22 | 1.6193 |
| fees_2x | 2291.20 | 10.70 | 27.19 | 1.1870 |
| latency_plus1 | 2009.56 | 10.62 | 22.57 | 1.9670 |
| latency_plus2 | 1615.80 | 9.21 | 28.27 | 1.8355 |
| latency_plus3 | 1284.75 | 9.46 | 24.18 | 1.7467 |
| low_liquidity | 2382.02 | 10.87 | 26.99 | 1.9918 |
| very_low_liquidity | 2382.02 | 10.87 | 26.99 | 1.9918 |
| high_slippage | 2284.82 | 10.55 | 27.81 | 1.9447 |
| extreme_slippage | 2005.05 | 10.66 | 21.55 | 1.8769 |
| combined_adverse | 1848.24 | 10.16 | 25.61 | 1.5370 |
| spread_widen_10bps | 2239.39 | 10.88 | 23.43 | 1.9550 |
| spread_widen_25bps | 2005.67 | 10.77 | 18.89 | 1.8922 |
| thin_book | 1405.30 | 9.30 | 25.63 | 1.8112 |
| very_thin_book | 602.75 | 7.05 | 27.61 | 1.2842 |
| entry_spread_stress | 2238.59 | 10.74 | 23.72 | 1.9554 |
| combined_market_deterioration | 1443.70 | 9.25 | 25.33 | 1.4234 |
| severe_adverse | 394.74 | 5.44 | 26.73 | 0.7507 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0350)
- **Best holdout score**: 1.4040 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.3713 | 1.2183 | 455.55 | 10.32 | 1754 |
| 1 | 0.6821 | 1.4040 | 615.26 | 12.01 | 4985 |
| 2 | 0.5880 | 1.2342 | 483.83 | 12.90 | 4000 |
| 3 | 0.5859 | 1.2769 | 500.49 | 8.28 | 3449 |
| 4 | 0.5850 | 1.1597 | 416.05 | 14.57 | 2711 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 52
- **Forward-fill fraction**: 0.0010030670704654617
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.7060586026748353
- **PnL %**: 209.08752824676017
- **Trade count**: 1439

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.6443859244381058
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.6543, 1.6318 |
| sell_spread_base | 1.6661, 1.6318 |
| stop_loss | 1.6707, 1.6399 |
| take_profit | 1.6600, 1.6615 |
| executor_refresh_time | 1.6444, 1.6444 |
| cooldown_time | 1.6444, 1.6444 |
| total_amount_quote | 1.6510, 1.6463 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.354238426986332
- **Max CV**: 0.741604326701947
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time
- **Scattered params**: cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3667 | 0.20537679925729907 | 0.6232501036520065 | 0.38371072328427036 |
| buy_spread_ratio | 0.1663 | 1.4491881152861543 | 2.36417523213158 | 1.8686931594989524 |
| sell_spread_base | 0.4064 | 0.20068275866054378 | 0.6466510096379906 | 0.3420356514140836 |
| sell_spread_ratio | 0.2264 | 1.2383155564573392 | 2.6255627164356876 | 1.9838686799407745 |
| buy_side_weight | 0.2294 | 0.2890819409001841 | 0.5917882212860227 | 0.4184720855910994 |
| amount_skew | 0.1684 | 2.392070505867431 | 3.959121911218636 | 3.3823425005852883 |
| stop_loss | 0.3775 | 0.04834991520821532 | 0.16370149559482272 | 0.08776847823036459 |
| take_profit | 0.3990 | 0.03537100474765422 | 0.13187756749655152 | 0.07962006843438092 |
| executor_refresh_time | 0.2667 | 330.0 | 700.0 | 515.7 |
| cooldown_time | 0.7416 | 68.0 | 787.0 | 302.7 |
| total_amount_quote | 0.5482 | 34.650627548875754 | 179.10422732434353 | 80.71901297067103 |

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
| recent_objective | > 0 | 0.7060586026748353 | PASS |
| recent_pnl | >= 0 | 209.08752824676017 | PASS |
| recent_trades | >= 5 | 1439 | PASS |
| worst_stress | > -10 | 0.7507124267345999 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.2183 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=0.7507124267345999 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=0.7060586026748353, pnl=209.08752824676017, trades=1439, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.354238426986332 |

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
- **run_timestamp**: 2026-03-28T08:47:35.368767+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11368
