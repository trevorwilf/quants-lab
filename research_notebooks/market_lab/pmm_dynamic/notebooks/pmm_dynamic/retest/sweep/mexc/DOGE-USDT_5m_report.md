# PMM Dynamic Optimization Report: mexc_DOGE-USDT_5m_retest_20260403

Generated: 2026-04-04 00:02:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-04T00:02:18.079491+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 10902 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOGE-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 7941f4a27ca92e5ee3477cec6bcf87b438f64d9f2f1e700ae6bf91f62c09fecd
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 35.995007335097604
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.261921996472233 |
| buy_n_levels | 3 |
| buy_side_weight | 0.39493292961761584 |
| buy_spread_base | 0.6867846801966583 |
| buy_spread_ratio | 2.9691373802838306 |
| cooldown_time | 203 |
| executor_refresh_time | 968 |
| macd_fast | 8 |
| macd_signal | 16 |
| macd_slow | 23 |
| natr_length | 44 |
| sell_n_levels | 8 |
| sell_spread_base | 0.43242946761537393 |
| sell_spread_ratio | 1.6796405881218275 |
| stop_loss | 0.15623321102278814 |
| take_profit | 0.09983727602459642 |
| time_limit | 157571 |
| total_amount_quote | 35.995007335097604 |
| trailing_stop_activation | 0.021702728302400255 |
| trailing_stop_delta | 0.0026952324289629256 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 35.995007335097604 |
| Selected | 35.995007335097604 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2841.2195
- **Net PnL (quote)**: 1022.6972
- **Sharpe Ratio**: 6.4399
- **Max Drawdown %**: 16.4203
- **Profit Factor**: 1.7934030092360203
- **Trade Count**: 8413
- **Total Fees (quote)**: 59.6268
- **Maker Fees**: 30.2536
- **Taker Fees**: 29.3732
- **Fee Drag %**: 165.6530

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.1753
- **PnL Component**: 3.3814
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1232
- **Fee Drag Component**: -0.8283
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7421**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 216.13 | 31.44 | 7.67 | 796 | 0.7680 | n/a |
| 1 | 312.63 | 33.80 | 5.65 | 777 | 1.0536 | n/a |
| 2 | 234.99 | 21.28 | 4.77 | 841 | 0.8459 | n/a |
| 3 | 329.66 | 30.18 | 6.22 | 797 | 1.0852 | n/a |
| 4 | 343.43 | 44.32 | 11.08 | 837 | 1.0776 | n/a |
| 5 | 397.96 | 36.08 | 16.24 | 827 | 1.1521 | n/a |
| 6 | 187.47 | 30.40 | 8.88 | 762 | 0.6648 | n/a |
| 7 | 153.53 | 31.92 | 6.27 | 745 | 0.5600 | n/a |
| 8 | 195.79 | 42.94 | 7.34 | 745 | 0.7094 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.1113)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2767.77 | 5.72 | 16.48 | 1.7427 |
| fees_2x | 2740.65 | 6.20 | 16.50 | 1.3220 |
| latency_plus1 | 2468.81 | 5.73 | 16.17 | 2.1258 |
| latency_plus2 | 2081.21 | 6.01 | 16.33 | 2.0677 |
| latency_plus3 | 1591.33 | 6.49 | 16.44 | 1.9535 |
| low_liquidity | 2841.22 | 6.44 | 16.42 | 2.1753 |
| very_low_liquidity | 2841.22 | 6.44 | 16.42 | 2.1753 |
| high_slippage | 2741.72 | 6.69 | 16.44 | 2.1450 |
| extreme_slippage | 2543.54 | 6.20 | 16.80 | 2.0753 |
| combined_adverse | 2369.74 | 6.35 | 16.28 | 1.7136 |
| spread_widen_10bps | 2737.36 | 5.89 | 16.63 | 2.1457 |
| spread_widen_25bps | 2610.52 | 5.33 | 16.51 | 2.0972 |
| thin_book | 1617.05 | 6.83 | 16.45 | 1.9657 |
| very_thin_book | 635.34 | 7.13 | 15.32 | 1.4225 |
| entry_spread_stress | 2685.06 | 6.24 | 16.41 | 2.1333 |
| combined_market_deterioration | 1993.15 | 5.42 | 16.54 | 1.6812 |
| severe_adverse | 564.31 | 6.07 | 15.90 | 1.1113 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0036)
- **Trend**: ranging (efficiency: 0.0103)
- **Best holdout score**: 1.6413 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.6433 | 1.1933 | 446.14 | 10.73 | 1752 |
| 1 | 1.2567 | 1.6413 | 808.89 | 8.77 | 4045 |
| 2 | 1.2010 | 1.4964 | 658.02 | 11.53 | 3371 |
| 3 | 1.1874 | 1.4796 | 650.21 | 10.34 | 2092 |
| 4 | 1.1841 | 1.4811 | 654.74 | 12.11 | 5774 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 68
- **Forward-fill fraction**: 0.0013117030921471421
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.421804422422528
- **PnL %**: 551.9691863485475
- **Trade count**: 1615

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.6863818705838358
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.6956, 1.6589 |
| sell_spread_base | 1.7382, 1.6811 |
| stop_loss | 1.7480, 1.6761 |
| take_profit | 1.6864, 1.6914 |
| executor_refresh_time | 1.6864, 1.6037 |
| cooldown_time | 1.6864, 1.6864 |
| total_amount_quote | 1.7199, 1.6875 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3229932068909332
- **Max CV**: 0.597034029935836
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time
- **Scattered params**: take_profit, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4151 | 0.21358126290306995 | 0.5898036278772137 | 0.3510630245592014 |
| buy_spread_ratio | 0.1811 | 1.412900460825166 | 2.874893717819604 | 2.5152903105094455 |
| sell_spread_base | 0.2921 | 0.20449042448375293 | 0.46644286737917906 | 0.30124703910363326 |
| sell_spread_ratio | 0.1646 | 1.2208919530421536 | 2.098819984001512 | 1.524690470986603 |
| buy_side_weight | 0.1461 | 0.31967128663701405 | 0.5003259047635654 | 0.42605727351449935 |
| amount_skew | 0.1763 | 1.9547932272407091 | 3.976014930838073 | 3.282576521478054 |
| stop_loss | 0.4100 | 0.04168968043286103 | 0.22478645604082145 | 0.12156990992868763 |
| take_profit | 0.5970 | 0.016819321581172345 | 0.11759537155722194 | 0.050621494388312684 |
| executor_refresh_time | 0.2439 | 413.0 | 809.0 | 481.0 |
| cooldown_time | 0.4073 | 183.0 | 516.0 | 313.4 |
| total_amount_quote | 0.5195 | 27.036705117730747 | 116.54845685293108 | 57.48991921100999 |

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
| recent_objective | > 0 | 1.421804422422528 | PASS |
| recent_pnl | >= 0 | 551.9691863485475 | PASS |
| recent_trades | >= 5 | 1615 | PASS |
| worst_stress | > -10 | 1.1112653982906169 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.1933 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.1112653982906169 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.421804422422528, pnl=551.9691863485475, trades=1615, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3229932068909332 |

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
- **run_timestamp**: 2026-04-04T00:02:18.079491+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 10902
