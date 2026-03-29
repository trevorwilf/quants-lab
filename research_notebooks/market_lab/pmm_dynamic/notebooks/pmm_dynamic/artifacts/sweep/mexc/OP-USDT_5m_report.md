# PMM Dynamic Optimization Report: mexc_OP-USDT_5m_sweep_v1

Generated: 2026-03-28 16:22:07 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T16:22:07.262921+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 11734 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: OP-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: c31e2e9953383d6e8ee24b920ccf258a464299cb9ae6b41f4f0efed068c407f5
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 915.9714654225402
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.5378825550813593 |
| buy_n_levels | 10 |
| buy_side_weight | 0.3380510416041568 |
| buy_spread_base | 1.107412065293035 |
| buy_spread_ratio | 1.6482965471757753 |
| cooldown_time | 958 |
| executor_refresh_time | 7568 |
| macd_fast | 36 |
| macd_signal | 22 |
| macd_slow | 38 |
| natr_length | 28 |
| sell_n_levels | 10 |
| sell_spread_base | 4.107619747480378 |
| sell_spread_ratio | 1.7673168018736523 |
| stop_loss | 0.014583742647346106 |
| take_profit | 0.04544292437298762 |
| time_limit | 115007 |
| total_amount_quote | 915.9714654225402 |
| trailing_stop_activation | 0.00182797263579163 |
| trailing_stop_delta | 0.001256377583380512 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 915.9714654225402 |
| Selected | 915.9714654225402 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.2843
- **Net PnL (quote)**: 11.7636
- **Sharpe Ratio**: 0.3424
- **Max Drawdown %**: 5.9305
- **Profit Factor**: 1.428406690085567
- **Trade Count**: 943
- **Total Fees (quote)**: 4.0548
- **Maker Fees**: 2.0258
- **Taker Fees**: 2.0290
- **Fee Drag %**: 0.4427

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0355
- **PnL Component**: 0.0128
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0445
- **Fee Drag Component**: -0.0022
- **Inventory Component**: -0.0015
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0012**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.17 | 2.61 | 0.22 | 132 | -0.0003 | n/a |
| 1 | 0.04 | 1.29 | 0.17 | 91 | -0.0026 | n/a |
| 2 | 0.05 | 1.53 | 0.16 | 81 | -0.0024 | n/a |
| 3 | 0.11 | 7.06 | 0.04 | 61 | 0.0007 | n/a |
| 4 | 0.22 | 4.69 | 0.11 | 88 | 0.0011 | n/a |
| 5 | 0.29 | 5.46 | 0.14 | 103 | 0.0016 | n/a |
| 6 | -0.12 | -2.64 | 0.17 | 55 | -0.0026 | n/a |
| 7 | 0.21 | 4.36 | 0.14 | 57 | 0.0010 | n/a |
| 8 | 0.04 | 7.46 | 0.02 | 19 | -0.1238 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0951)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.06 | 0.30 | 5.94 | -0.0388 |
| fees_2x | 0.84 | 0.25 | 5.95 | -0.0422 |
| latency_plus1 | 1.27 | 0.34 | 5.93 | -0.0356 |
| latency_plus2 | 1.21 | 0.33 | 5.93 | -0.0361 |
| latency_plus3 | 0.99 | 0.28 | 5.93 | -0.0383 |
| low_liquidity | 1.28 | 0.34 | 5.93 | -0.0355 |
| very_low_liquidity | 1.28 | 0.34 | 5.93 | -0.0355 |
| high_slippage | 0.73 | 0.23 | 5.95 | -0.0411 |
| extreme_slippage | -0.38 | -0.01 | 6.05 | -0.0671 |
| combined_adverse | 0.50 | 0.18 | 5.97 | -0.0447 |
| spread_widen_10bps | 0.85 | 0.25 | 5.96 | -0.0400 |
| spread_widen_25bps | -0.04 | 0.06 | 6.09 | -0.0522 |
| thin_book | -1.19 | -0.19 | 6.90 | -0.0670 |
| very_thin_book | -2.42 | -1.76 | 2.74 | -0.0462 |
| entry_spread_stress | 0.19 | 0.11 | 6.05 | -0.0473 |
| combined_market_deterioration | -1.07 | -0.16 | 6.97 | -0.0685 |
| severe_adverse | -3.53 | -2.00 | 3.80 | -0.0951 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0049)
- **Trend**: ranging (efficiency: 0.0495)
- **Best holdout score**: 0.0171 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0653 | 0.0055 | 0.75 | 0.21 | 156 |
| 1 | 0.0046 | 0.0111 | 1.97 | 0.75 | 349 |
| 2 | 0.0038 | 0.0171 | 2.29 | 0.54 | 158 |
| 3 | 0.0033 | 0.0138 | 2.45 | 0.96 | 182 |
| 4 | 0.0032 | 0.0036 | 0.98 | 0.68 | 158 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 3
- **Forward-fill fraction**: 5.778899312310982e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0002 <= 0
- **Objective score**: -0.00022565063115561647
- **PnL %**: 0.052064288534723495
- **Trade count**: 56

## Sensitivity Analysis

- **Sensitivity penalty**: 0.14285714285714285
- **Baseline score**: -0.029569964124318934
- **Sign flips**: 2
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0369, 0.0020 |
| sell_spread_base | -0.0296, -0.0291 |
| stop_loss | -0.0311, -0.0290 |
| take_profit | -0.0296, -0.0296 |
| executor_refresh_time | -0.0338, -0.0358 |
| cooldown_time | -0.0296, -0.0316 |
| total_amount_quote | -0.0296, 0.0140 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3826241363503639
- **Max CV**: 0.6226628528624861
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4153 | 0.27166126504881394 | 1.4315278878678064 | 0.7574668806762463 |
| buy_spread_ratio | 0.1446 | 1.4302641141255017 | 2.1917921836605503 | 1.7584116633079088 |
| sell_spread_base | 0.4933 | 0.49606780393548394 | 3.945536531882031 | 2.2255735587729615 |
| sell_spread_ratio | 0.2186 | 1.4915751823394812 | 2.984630897508482 | 2.1118402729217207 |
| buy_side_weight | 0.3621 | 0.20549576121794635 | 0.5362985193965527 | 0.35575697156398245 |
| amount_skew | 0.2921 | 1.0609653151441243 | 2.637491183664929 | 1.6780531264821268 |
| stop_loss | 0.1451 | 0.010029329633723464 | 0.015560306607044565 | 0.011592618442402853 |
| take_profit | 0.6227 | 0.006236101449555912 | 0.0335207473826031 | 0.013805142453198823 |
| executor_refresh_time | 0.6192 | 1735.0 | 8857.0 | 4223.8 |
| cooldown_time | 0.5905 | 445.0 | 5843.0 | 2878.2 |
| total_amount_quote | 0.3054 | 297.7336578019888 | 989.0587561380544 | 770.4758425006756 |

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
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.00022565063115561647 | FAIL |
| recent_pnl | >= 0 | 0.052064288534723495 | PASS |
| recent_trades | >= 5 | 56 | PASS |
| worst_stress | > -10 | -0.09512354943660647 | PASS |
| sensitivity_penalty | < 0.50 | 0.14285714285714285 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0055 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.09512354943660647 |
| sensitivity | PASS | penalty=0.14285714285714285 |
| recent_28d | FAIL | score=-0.00022565063115561647, pnl=0.052064288534723495, trades=56, reason=recent objective score -0.0002 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3826241363503639 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0002 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T16:22:07.262921+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 11734
