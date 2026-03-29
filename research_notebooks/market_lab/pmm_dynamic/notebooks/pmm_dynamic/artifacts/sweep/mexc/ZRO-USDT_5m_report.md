# PMM Dynamic Optimization Report: mexc_ZRO-USDT_5m_sweep_v1

Generated: 2026-03-29 03:48:55 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T03:48:55.557641+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 7446 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ZRO-USDT
- **interval**: 5m
- **n_candles**: 52057
- **dataset_hash**: 3f2cc519073708219e91f00d49e7a9a16b7545ef54c6538b587404bdf1fc26b8
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 908.1855888671765
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.0420246023829964 |
| buy_n_levels | 6 |
| buy_side_weight | 0.2066414750697794 |
| buy_spread_base | 2.270045441276422 |
| buy_spread_ratio | 1.7183729659021714 |
| cooldown_time | 5228 |
| executor_refresh_time | 13606 |
| macd_fast | 49 |
| macd_signal | 19 |
| macd_slow | 94 |
| natr_length | 7 |
| sell_n_levels | 8 |
| sell_spread_base | 1.074852555855746 |
| sell_spread_ratio | 2.4573113302780234 |
| stop_loss | 0.013937390378352735 |
| take_profit | 0.010258655044244051 |
| time_limit | 111033 |
| total_amount_quote | 908.1855888671765 |
| trailing_stop_activation | 0.000951448892846361 |
| trailing_stop_delta | 0.00102917376883848 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 908.1855888671765 |
| Selected | 908.1855888671765 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.3942
- **Net PnL (quote)**: 12.6617
- **Sharpe Ratio**: 2.4214
- **Max Drawdown %**: 0.7197
- **Profit Factor**: 1.5951054016056707
- **Trade Count**: 979
- **Total Fees (quote)**: 3.2407
- **Maker Fees**: 1.6187
- **Taker Fees**: 1.6219
- **Fee Drag %**: 0.3568

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0066
- **PnL Component**: 0.0138
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0054
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0014**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.77 | 7.93 | 0.06 | 97 | 0.0070 | n/a |
| 1 | -0.00 | -0.15 | 0.07 | 65 | -0.0007 | n/a |
| 2 | 0.07 | 3.22 | 0.15 | 73 | -0.0007 | n/a |
| 3 | -0.01 | -1.30 | 0.04 | 59 | -0.0005 | n/a |
| 4 | -0.32 | -2.29 | 0.65 | 65 | -0.0083 | n/a |
| 5 | 0.19 | 7.52 | 0.14 | 91 | 0.0006 | n/a |
| 6 | 0.03 | 0.53 | 0.35 | 88 | -0.0025 | n/a |
| 7 | 0.31 | 8.16 | 0.10 | 93 | 0.0021 | n/a |
| 8 | 0.17 | 13.01 | 0.04 | 82 | 0.0013 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0621)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 1.22 | 2.11 | 0.76 | 0.0037 |
| fees_2x | 1.04 | 1.81 | 0.79 | 0.0008 |
| latency_plus1 | 1.39 | 2.41 | 0.72 | 0.0066 |
| latency_plus2 | 1.38 | 2.40 | 0.72 | 0.0065 |
| latency_plus3 | 1.34 | 2.33 | 0.72 | 0.0062 |
| low_liquidity | 1.39 | 2.41 | 0.72 | 0.0066 |
| very_low_liquidity | 1.44 | 2.50 | 0.66 | 0.0075 |
| high_slippage | 0.95 | 1.66 | 0.81 | 0.0016 |
| extreme_slippage | 0.05 | 0.11 | 1.10 | -0.0095 |
| combined_adverse | 0.76 | 1.34 | 0.85 | -0.0015 |
| spread_widen_10bps | 1.10 | 1.88 | 0.85 | 0.0027 |
| spread_widen_25bps | 0.30 | 0.50 | 0.97 | -0.0062 |
| thin_book | -0.35 | -0.02 | 5.25 | -0.0444 |
| very_thin_book | -1.92 | -2.17 | 2.03 | -0.0358 |
| entry_spread_stress | 0.90 | 1.54 | 0.90 | 0.0004 |
| combined_market_deterioration | -1.45 | -2.79 | 1.80 | -0.0329 |
| severe_adverse | -3.22 | -1.93 | 3.31 | -0.0621 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0070)
- **Trend**: ranging (efficiency: 0.0028)
- **Best holdout score**: 0.0018 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0277 | 0.0018 | 0.51 | 0.37 | 201 |
| 1 | -0.0004 | -0.0011 | 0.06 | 0.18 | 175 |
| 2 | -0.0004 | -0.0022 | 0.30 | 0.46 | 271 |
| 3 | -0.0004 | -0.0031 | 0.25 | 0.39 | 292 |
| 4 | -0.0005 | -0.0092 | 0.70 | 1.22 | 961 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52057
- **Expected rows**: 52057
- **Missing rows**: 0
- **Forward-fill count**: 3
- **Forward-fill fraction**: 5.7629137291814744e-05
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.0029319325804339673
- **PnL %**: 0.36406129016373207
- **Trade count**: 168

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: 0.013969911838494187
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0124, 0.0201 |
| sell_spread_base | 0.0140, 0.0140 |
| stop_loss | 0.0157, 0.0144 |
| take_profit | 0.0140, 0.0140 |
| executor_refresh_time | 0.0069, 0.0159 |
| cooldown_time | 0.0127, 0.0129 |
| total_amount_quote | 0.0139, 0.0139 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.35265920667134504
- **Max CV**: 0.7668832044119549
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2104 | 1.7501337998263364 | 3.1290948686386764 | 2.2629040643809786 |
| buy_spread_ratio | 0.1878 | 1.5549609815560272 | 2.766335029130674 | 2.02409892173978 |
| sell_spread_base | 0.7669 | 0.24409033314427198 | 3.8462596890277885 | 1.6562552872135217 |
| sell_spread_ratio | 0.2468 | 1.53327173000137 | 2.97585321528747 | 2.2408325868727874 |
| buy_side_weight | 0.2673 | 0.20878455467284718 | 0.4453323286886036 | 0.3114067919270991 |
| amount_skew | 0.2678 | 1.5307856020434067 | 3.3021714016936494 | 2.343365239278396 |
| stop_loss | 0.4025 | 0.011154336030786853 | 0.032203485162826846 | 0.016517647281985997 |
| take_profit | 0.5044 | 0.0058498936599951186 | 0.0259478339612114 | 0.013497169814571757 |
| executor_refresh_time | 0.4083 | 2695.0 | 14148.0 | 9541.7 |
| cooldown_time | 0.4438 | 349.0 | 6706.0 | 4133.5 |
| total_amount_quote | 0.1732 | 519.4348994321356 | 974.6495063741975 | 769.2411516566012 |

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
| recent_objective | > 0 | 0.0029319325804339673 | PASS |
| recent_pnl | >= 0 | 0.36406129016373207 | PASS |
| recent_trades | >= 5 | 168 | PASS |
| worst_stress | > -10 | -0.062137057792687106 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0018 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.062137057792687106 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | PASS | score=0.0029319325804339673, pnl=0.36406129016373207, trades=168, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.35265920667134504 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52057 |  |
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
- **Dev bars**: 35194
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T03:48:55.557641+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 7446
