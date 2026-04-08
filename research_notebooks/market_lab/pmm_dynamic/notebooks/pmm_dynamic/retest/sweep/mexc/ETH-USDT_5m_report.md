# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_retest_20260408

Generated: 2026-04-08 08:18:04 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T08:18:04.692560+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 8679 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 020e5a71f0d444e313e436fe4ccf120671d8e95ae6dd03abb9eef919e06a8573
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 883.4959161256265
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6992447215799764 |
| buy_n_levels | 5 |
| buy_side_weight | 0.2159150448916478 |
| buy_spread_base | 3.2185630040594164 |
| buy_spread_ratio | 2.897578385437867 |
| cooldown_time | 2785 |
| executor_refresh_time | 2663 |
| macd_fast | 38 |
| macd_signal | 10 |
| macd_slow | 80 |
| natr_length | 39 |
| sell_n_levels | 4 |
| sell_spread_base | 5.698996924730115 |
| sell_spread_ratio | 2.7133887858715178 |
| stop_loss | 0.019464640109334568 |
| take_profit | 0.005772335986221556 |
| time_limit | 50545 |
| total_amount_quote | 883.4959161256265 |
| trailing_stop_activation | 0.003794138753375701 |
| trailing_stop_delta | 0.0014335555599359784 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 883.4959161256265 |
| Selected | 883.4959161256265 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.0093
- **Net PnL (quote)**: -17.7517
- **Sharpe Ratio**: -5.4205
- **Max Drawdown %**: 2.0589
- **Profit Factor**: 0.5567202261008838
- **Trade Count**: 981
- **Total Fees (quote)**: 3.2549
- **Maker Fees**: 1.6289
- **Taker Fees**: 1.6260
- **Fee Drag %**: 0.3684

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0435
- **PnL Component**: -0.0203
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0154
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0058
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0070**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.37 | -10.45 | 0.46 | 54 | -0.0103 | n/a |
| 1 | -0.12 | -3.27 | 0.29 | 67 | -0.0066 | n/a |
| 2 | -0.17 | -9.61 | 0.19 | 54 | -0.0062 | n/a |
| 3 | 0.10 | 8.39 | 0.03 | 52 | -0.0023 | n/a |
| 4 | -0.19 | -5.52 | 0.24 | 70 | -0.0069 | n/a |
| 5 | -0.23 | -6.17 | 0.28 | 65 | -0.0075 | n/a |
| 6 | -0.14 | -3.98 | 0.14 | 67 | -0.0056 | n/a |
| 7 | 0.11 | 8.72 | 0.03 | 61 | -0.0022 | n/a |
| 8 | -0.48 | -8.12 | 0.50 | 74 | -0.0118 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0870)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.19 | -5.91 | 2.24 | -0.0476 |
| fees_2x | -2.38 | -6.39 | 2.42 | -0.0518 |
| latency_plus1 | -2.54 | -6.32 | 2.59 | -0.0530 |
| latency_plus2 | -2.28 | -5.63 | 2.33 | -0.0483 |
| latency_plus3 | -1.77 | -4.61 | 1.82 | -0.0393 |
| low_liquidity | -2.01 | -5.42 | 2.06 | -0.0435 |
| very_low_liquidity | -2.01 | -5.42 | 2.06 | -0.0435 |
| high_slippage | -2.47 | -6.62 | 2.52 | -0.0516 |
| extreme_slippage | -3.39 | -8.92 | 3.43 | -0.0680 |
| combined_adverse | -3.19 | -7.84 | 3.23 | -0.0654 |
| spread_widen_10bps | -2.17 | -3.11 | 2.94 | -0.0548 |
| spread_widen_25bps | -2.59 | -4.03 | 3.11 | -0.0604 |
| thin_book | -2.43 | -7.04 | 2.47 | -0.0475 |
| very_thin_book | -1.56 | -5.02 | 1.65 | -0.0318 |
| entry_spread_stress | -1.46 | -2.45 | 2.09 | -0.0383 |
| combined_market_deterioration | -2.99 | -7.93 | 3.04 | -0.0615 |
| severe_adverse | -4.39 | -10.56 | 4.53 | -0.0870 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0029)
- **Trend**: ranging (efficiency: 0.0036)
- **Best holdout score**: -0.0057 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0652 | -0.0057 | -0.09 | 0.19 | 137 |
| 1 | -0.0023 | -0.0168 | -0.46 | 0.57 | 412 |
| 2 | -0.0028 | -0.0091 | -0.17 | 0.33 | 378 |
| 3 | -0.0030 | -0.0426 | -1.71 | 1.76 | 531 |
| 4 | -0.0033 | -0.0889 | -3.46 | 3.92 | 655 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 242
- **Forward-fill fraction**: 0.004668119827935418
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0184 <= 0; recent PnL -0.5869% < 0
- **Objective score**: -0.018351291458571704
- **PnL %**: -0.586857618747449
- **Trade count**: 130

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0328 <= 0; recent PnL -0.1705% < 0
- **Objective score**: -0.03278452503397451
- **PnL %**: -0.1704542814468408
- **Trade count**: 64

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1428 <= 0; recent PnL -0.1502% < 0
- **Objective score**: -0.1427604931864923
- **PnL %**: -0.15018408484180093
- **Trade count**: 30

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.06079665648396125
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0265, -0.0873 |
| sell_spread_base | -0.0626, -0.0699 |
| stop_loss | -0.0479, -0.0399 |
| take_profit | -0.0608, -0.0608 |
| executor_refresh_time | -0.0337, -0.0232 |
| cooldown_time | -0.0312, -0.0304 |
| total_amount_quote | -0.0602, -0.0602 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.26763558006216326
- **Max CV**: 0.7375022630530805
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0898 | 2.9182653168184154 | 3.7597218638038585 | 3.2128182836030144 |
| buy_spread_ratio | 0.0916 | 1.8701860835389372 | 2.5276037152030333 | 2.2898165651627584 |
| sell_spread_base | 0.6865 | 0.20520880008125506 | 1.4625545802473903 | 0.6191654946501124 |
| sell_spread_ratio | 0.2934 | 1.2582324427844302 | 2.9873792208299945 | 2.000506753070433 |
| buy_side_weight | 0.2048 | 0.21379217124356553 | 0.4114031246072797 | 0.2998585138102785 |
| amount_skew | 0.1319 | 2.019003493044818 | 3.5397104580688334 | 2.963430112908764 |
| stop_loss | 0.1358 | 0.01072588802665636 | 0.01608160761816211 | 0.012595940227296081 |
| take_profit | 0.1150 | 0.005016724138260548 | 0.006819862045354687 | 0.005826414677076016 |
| executor_refresh_time | 0.3486 | 3822.0 | 12868.0 | 8318.7 |
| cooldown_time | 0.7375 | 90.0 | 6036.0 | 2433.2 |
| total_amount_quote | 0.1091 | 748.1657745111871 | 990.7873197462112 | 878.5584242076624 |

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
| recent_objective | > 0 | -0.018351291458571704 | FAIL |
| recent_pnl | >= 0 | -0.586857618747449 | FAIL |
| recent_trades | >= 5 | 130 | PASS |
| worst_stress | > -10 | -0.08699016389848026 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.005713642113971372 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.08699016389848026 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.018351291458571704, pnl=-0.586857618747449, trades=130, reason=recent objective score -0.0184 <= 0; recent PnL -0.5869% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.03278452503397451, pnl=-0.1704542814468408, trades=64, reason=recent objective score -0.0328 <= 0; recent PnL -0.1705% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.1427604931864923, pnl=-0.15018408484180093, trades=30, reason=recent objective score -0.1428 <= 0; recent PnL -0.1502% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.26763558006216326 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0184 <= 0; recent PnL -0.5869% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0328 <= 0; recent PnL -0.1705% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1428 <= 0; recent PnL -0.1502% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1773207600

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T08:18:04.692560+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 8679
