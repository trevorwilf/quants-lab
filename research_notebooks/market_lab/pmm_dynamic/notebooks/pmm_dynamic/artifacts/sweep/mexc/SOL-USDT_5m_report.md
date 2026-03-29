# PMM Dynamic Optimization Report: mexc_SOL-USDT_5m_sweep_v1

Generated: 2026-03-28 19:30:46 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T19:30:46.978611+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 2877 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SOL-USDT
- **interval**: 5m
- **n_candles**: 51973
- **dataset_hash**: 7ad831395b6b6e934eae44f1864b0b48c7a4414e047886396468a7791a775d03
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 198.0026256616942
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.918870079446188 |
| buy_n_levels | 5 |
| buy_side_weight | 0.4593430014273112 |
| buy_spread_base | 0.26569983156493754 |
| buy_spread_ratio | 1.4685561063616648 |
| cooldown_time | 66 |
| executor_refresh_time | 915 |
| macd_fast | 5 |
| macd_signal | 9 |
| macd_slow | 90 |
| natr_length | 47 |
| sell_n_levels | 7 |
| sell_spread_base | 0.31930249624597773 |
| sell_spread_ratio | 1.5589731424918971 |
| stop_loss | 0.19585699129091666 |
| take_profit | 0.03238043379894899 |
| time_limit | 159899 |
| total_amount_quote | 198.0026256616942 |
| trailing_stop_activation | 0.01566295594934379 |
| trailing_stop_delta | 0.001144861674587267 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 198.0026256616942 |
| Selected | 198.0026256616942 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2568.8920
- **Net PnL (quote)**: 5086.4737
- **Sharpe Ratio**: 13.4906
- **Max Drawdown %**: 18.9573
- **Profit Factor**: 2.164732903558586
- **Trade Count**: 22450
- **Total Fees (quote)**: 263.6180
- **Maker Fees**: 133.3631
- **Taker Fees**: 130.2549
- **Fee Drag %**: 133.1386

## Selected Candidate Single-Run Objective

- **Raw Score**: 2.2217
- **PnL Component**: 3.2842
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1422
- **Fee Drag Component**: -0.6657
- **Inventory Component**: -0.2499
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **0.7586**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 374.10 | 33.44 | 8.56 | 2259 | 1.1726 | n/a |
| 1 | 370.82 | 21.03 | 5.58 | 2278 | 1.1886 | n/a |
| 2 | 402.55 | 42.82 | 4.72 | 2389 | 1.2582 | n/a |
| 3 | 183.13 | 38.37 | 3.25 | 2288 | 0.7012 | n/a |
| 4 | 224.41 | 37.54 | 6.35 | 2199 | 0.8145 | n/a |
| 5 | 349.58 | 40.33 | 13.06 | 2298 | 1.0862 | n/a |
| 6 | 224.30 | 27.49 | 13.07 | 2142 | 0.7624 | n/a |
| 7 | 205.69 | 39.22 | 7.91 | 2125 | 0.7450 | n/a |
| 8 | 217.16 | 41.37 | 3.33 | 2124 | 0.8160 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: 1.0841)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2510.92 | 13.42 | 18.55 | 1.8700 |
| fees_2x | 2475.27 | 13.26 | 18.47 | 1.5292 |
| latency_plus1 | 2319.86 | 12.85 | 18.11 | 2.1897 |
| latency_plus2 | 1952.37 | 12.29 | 17.31 | 2.1127 |
| latency_plus3 | 1536.69 | 11.38 | 16.55 | 1.9777 |
| low_liquidity | 2568.89 | 13.49 | 18.96 | 2.2217 |
| very_low_liquidity | 2568.89 | 13.49 | 18.96 | 2.2217 |
| high_slippage | 2458.68 | 13.26 | 18.90 | 2.1834 |
| extreme_slippage | 2267.69 | 12.82 | 18.68 | 2.1159 |
| combined_adverse | 2179.43 | 12.55 | 17.78 | 1.8434 |
| spread_widen_10bps | 2478.36 | 13.29 | 18.10 | 2.2002 |
| spread_widen_25bps | 2316.24 | 12.95 | 17.40 | 2.1422 |
| thin_book | 1511.96 | 11.57 | 18.94 | 1.9963 |
| very_thin_book | 633.05 | 8.47 | 20.09 | 1.4161 |
| entry_spread_stress | 2408.80 | 13.18 | 17.62 | 2.1777 |
| combined_market_deterioration | 1837.68 | 12.06 | 19.54 | 1.8058 |
| severe_adverse | 539.20 | 7.53 | 19.85 | 1.0841 |

## Holdout Validation

- **Holdout bars**: 8783
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0269)
- **Best holdout score**: 1.5918 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 1.6529 | 1.2885 | 527.41 | 19.93 | 4957 |
| 1 | 1.2549 | 1.5522 | 734.83 | 16.72 | 2906 |
| 2 | 1.1978 | 1.3891 | 604.72 | 19.71 | 1959 |
| 3 | 1.1869 | 1.5918 | 798.30 | 19.98 | 4384 |
| 4 | 1.1733 | 1.5624 | 773.08 | 18.44 | 4462 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51973
- **Expected rows**: 51980
- **Missing rows**: 7
- **Forward-fill count**: 167
- **Forward-fill fraction**: 0.0032132068574067304
- **Longest gap (seconds)**: 2400

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 1.35518567195099
- **PnL %**: 502.9251751952752
- **Trade count**: 4384

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 1.7008569612231605
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 1.7075, 1.6922 |
| sell_spread_base | 1.6936, 1.6955 |
| stop_loss | 1.7055, 1.6838 |
| take_profit | 1.7009, 1.7009 |
| executor_refresh_time | 1.7009, 1.7034 |
| cooldown_time | 1.7009, 1.7009 |
| total_amount_quote | 1.7095, 1.6988 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.32769741584449963
- **Max CV**: 0.6412429554114498
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time
- **Scattered params**: total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.4167 | 0.22168551759029648 | 0.6742661578835539 | 0.394613225774884 |
| buy_spread_ratio | 0.2014 | 1.2115430828994735 | 2.274352932774227 | 1.5391063595363719 |
| sell_spread_base | 0.3839 | 0.20314851267839623 | 0.6087108805592281 | 0.3136818082386414 |
| sell_spread_ratio | 0.2226 | 1.2158392206133701 | 2.318456463051457 | 1.6910634795698414 |
| buy_side_weight | 0.1805 | 0.33380458424580456 | 0.6044118811572574 | 0.5003193266422972 |
| amount_skew | 0.1890 | 1.993412325562477 | 3.6313142653599706 | 2.8724128453446487 |
| stop_loss | 0.1773 | 0.11907598238148358 | 0.1952058213516744 | 0.15589961873912003 |
| take_profit | 0.4705 | 0.01440549430936342 | 0.07672560895389134 | 0.03815059519566235 |
| executor_refresh_time | 0.2938 | 313.0 | 844.0 | 507.9 |
| cooldown_time | 0.4276 | 100.0 | 454.0 | 253.0 |
| total_amount_quote | 0.6412 | 26.391714521323994 | 190.3961948607801 | 83.56422166361196 |

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
| recent_objective | > 0 | 1.35518567195099 | PASS |
| recent_pnl | >= 0 | 502.9251751952752 | PASS |
| recent_trades | >= 5 | 4384 | PASS |
| worst_stress | > -10 | 1.0840567830654146 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=1.2885 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=1.0840567830654146 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | PASS | score=1.35518567195099, pnl=502.9251751952752, trades=4384, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.32769741584449963 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51973 |  |
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
- **Dev bars**: 35132
- **Holdout bars**: 8783
- **Recent 28d bars**: 8058

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T19:30:46.978611+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 2877
