# PMM Dynamic Optimization Report: mexc_SAHARA-USDT_5m_sweep_v1

Generated: 2026-03-28 18:07:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T18:07:56.466652+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7484 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SAHARA-USDT
- **interval**: 5m
- **n_candles**: 51985
- **dataset_hash**: ae67b02d4ffab59a3800a9806a8d4d2eb00708e1e676b45475ca67cc6b471fde
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 935.4116536248715
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.4984713670772907 |
| buy_n_levels | 6 |
| buy_side_weight | 0.584345879200904 |
| buy_spread_base | 0.34742861537358005 |
| buy_spread_ratio | 1.2432449751792816 |
| cooldown_time | 988 |
| executor_refresh_time | 1823 |
| macd_fast | 44 |
| macd_signal | 8 |
| macd_slow | 90 |
| natr_length | 7 |
| sell_n_levels | 5 |
| sell_spread_base | 2.260690575431315 |
| sell_spread_ratio | 2.08336945590285 |
| stop_loss | 0.018688712956277685 |
| take_profit | 0.006689041776666548 |
| time_limit | 137933 |
| total_amount_quote | 935.4116536248715 |
| trailing_stop_activation | 0.015247344229983537 |
| trailing_stop_delta | 0.01355577280031559 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 935.4116536248715 |
| Selected | 935.4116536248715 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 24.6858
- **Net PnL (quote)**: 230.9137
- **Sharpe Ratio**: 3.7753
- **Max Drawdown %**: 5.7122
- **Profit Factor**: 2.712956638522321
- **Trade Count**: 364
- **Total Fees (quote)**: 14.2184
- **Maker Fees**: 11.8112
- **Taker Fees**: 2.4072
- **Fee Drag %**: 1.5200

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.1681
- **PnL Component**: 0.2206
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0428
- **Fee Drag Component**: -0.0076
- **Inventory Component**: -0.0017
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1279**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 3.99 | 12.75 | 0.75 | 73 | 0.0300 | n/a |
| 1 | 19.11 | 11.62 | 1.95 | 140 | 0.0304 | n/a |
| 2 | 0.04 | 0.19 | 1.44 | 23 | -0.1191 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -1.19 | -4.51 | 2.26 | 25 | -0.1296 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 4.40 | 8.97 | 0.43 | 26 | -0.0568 | n/a |
| 8 | -4.90 | -11.40 | 4.90 | 19 | -0.2899 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0436)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 23.92 | 3.67 | 5.82 | 0.1574 |
| fees_2x | 23.16 | 3.56 | 5.93 | 0.1466 |
| latency_plus1 | 17.83 | 3.30 | 5.98 | 0.1098 |
| latency_plus2 | 17.48 | 3.23 | 5.99 | 0.1070 |
| latency_plus3 | 15.16 | 2.88 | 6.07 | 0.0871 |
| low_liquidity | 23.53 | 3.66 | 4.85 | 0.1661 |
| very_low_liquidity | 20.71 | 3.46 | 3.97 | 0.1491 |
| high_slippage | 24.04 | 3.68 | 5.88 | 0.1617 |
| extreme_slippage | 22.75 | 3.49 | 6.20 | 0.1488 |
| combined_adverse | 15.71 | 2.95 | 5.44 | 0.0931 |
| spread_widen_10bps | 22.19 | 3.36 | 6.90 | 0.1389 |
| spread_widen_25bps | 15.48 | 2.38 | 9.98 | 0.0591 |
| thin_book | 11.30 | 1.77 | 6.18 | 0.0515 |
| very_thin_book | 4.25 | 1.85 | 1.86 | 0.0256 |
| entry_spread_stress | 17.14 | 2.62 | 10.24 | 0.0714 |
| combined_market_deterioration | 12.26 | 2.65 | 5.49 | 0.0637 |
| severe_adverse | 0.73 | 0.22 | 5.47 | -0.0436 |

## Holdout Validation

- **Holdout bars**: 8784
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0052)
- **Trend**: ranging (efficiency: 0.0140)
- **Best holdout score**: -0.0488 (rank #3)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.0623 | -0.1104 | 1.55 | 2.28 | 23 |
| 1 | 0.0289 | -0.0488 | 5.51 | 1.28 | 27 |
| 2 | 0.0275 | -0.0841 | 4.81 | 1.39 | 20 |
| 3 | 0.0268 | -0.0488 | 5.33 | 1.07 | 27 |
| 4 | 0.0257 | -0.1104 | 1.55 | 2.28 | 23 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51985
- **Expected rows**: 51985
- **Missing rows**: 0
- **Forward-fill count**: 92
- **Forward-fill fraction**: 0.0017697412715206309
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1729 <= 0; recent PnL -3.9008% < 0
- **Objective score**: -0.17290291693822313
- **PnL %**: -3.900814495249636
- **Trade count**: 34

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.1497333635256099
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.1482, 0.1504 |
| sell_spread_base | 0.1493, 0.1495 |
| stop_loss | 0.1600, 0.0622 |
| take_profit | 0.1397, 0.1457 |
| executor_refresh_time | 0.1497, 0.1823 |
| cooldown_time | 0.1497, 0.1471 |
| total_amount_quote | 0.1638, 0.1497 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2723552211503669
- **Max CV**: 0.6985523700826426
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.3012 | 0.21824683353418964 | 0.5218630354982271 | 0.3511622650989006 |
| buy_spread_ratio | 0.1571 | 1.2331750172954592 | 1.8659694385080066 | 1.4534970450740556 |
| sell_spread_base | 0.3297 | 2.260690575431315 | 5.663094975185526 | 3.825611422266738 |
| sell_spread_ratio | 0.1896 | 1.218469322907259 | 2.1118445536473365 | 1.7226587538171418 |
| buy_side_weight | 0.1092 | 0.5787281471822742 | 0.7943570633779309 | 0.7275703837202503 |
| amount_skew | 0.1492 | 2.1638843821776965 | 3.933647524048027 | 3.4844301615954882 |
| stop_loss | 0.1612 | 0.010218940448603563 | 0.018688712956277685 | 0.013923735731460727 |
| take_profit | 0.0787 | 0.005574381890342747 | 0.007215105099086192 | 0.006615971420332187 |
| executor_refresh_time | 0.6579 | 646.0 | 4689.0 | 1943.5 |
| cooldown_time | 0.6986 | 319.0 | 5090.0 | 2518.9 |
| total_amount_quote | 0.1635 | 536.2199452714364 | 983.6068031018103 | 804.6746213868306 |

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
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.17290291693822313 | FAIL |
| recent_pnl | >= 0 | -3.900814495249636 | FAIL |
| recent_trades | >= 5 | 34 | PASS |
| worst_stress | > -10 | -0.04364240784616595 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.11038733459649344 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.04364240784616595 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.17290291693822313, pnl=-3.900814495249636, trades=34, reason=recent objective score -0.1729 <= 0; recent PnL -3.9008% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2723552211503669 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51985 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1729 <= 0; recent PnL -3.9008% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35136
- **Holdout bars**: 8784
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T18:07:56.466652+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7484
