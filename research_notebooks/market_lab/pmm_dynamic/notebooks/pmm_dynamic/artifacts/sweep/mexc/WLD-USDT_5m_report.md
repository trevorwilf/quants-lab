# PMM Dynamic Optimization Report: mexc_WLD-USDT_5m_sweep_v1

Generated: 2026-03-28 22:10:49 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-28T22:10:49.205301+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 3846 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLD-USDT
- **interval**: 5m
- **n_candles**: 51987
- **dataset_hash**: 48ba98ef095bc9e74a2fcdc7e88ae4d79f670b628febf8d3feb6fac250838bd6
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 910.5193528095342
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.2715452662196722 |
| buy_n_levels | 10 |
| buy_side_weight | 0.2165959887074217 |
| buy_spread_base | 0.9228541184213942 |
| buy_spread_ratio | 2.538841194820583 |
| cooldown_time | 4944 |
| executor_refresh_time | 3181 |
| macd_fast | 8 |
| macd_signal | 11 |
| macd_slow | 53 |
| natr_length | 15 |
| sell_n_levels | 10 |
| sell_spread_base | 0.8010090181064041 |
| sell_spread_ratio | 1.3154295177409772 |
| stop_loss | 0.012190402217586762 |
| take_profit | 0.10611639001547134 |
| time_limit | 34546 |
| total_amount_quote | 910.5193528095342 |
| trailing_stop_activation | 0.0022870762470739558 |
| trailing_stop_delta | 0.0011242728744296998 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 910.5193528095342 |
| Selected | 910.5193528095342 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.5970
- **Net PnL (quote)**: 32.7515
- **Sharpe Ratio**: 3.3774
- **Max Drawdown %**: 1.3291
- **Profit Factor**: 1.9240659069644839
- **Trade Count**: 1969
- **Total Fees (quote)**: 6.5346
- **Maker Fees**: 3.2634
- **Taker Fees**: 3.2712
- **Fee Drag %**: 0.7177

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0191
- **PnL Component**: 0.0353
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0100
- **Fee Drag Component**: -0.0036
- **Inventory Component**: -0.0026
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0034**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 1.36 | 9.08 | 0.11 | 131 | 0.0095 | n/a |
| 1 | 0.23 | 5.42 | 0.19 | 97 | -0.0022 | n/a |
| 2 | 0.07 | 1.63 | 0.14 | 91 | -0.0035 | n/a |
| 3 | -0.11 | -3.78 | 0.17 | 70 | -0.0027 | n/a |
| 4 | -0.11 | -3.21 | 0.29 | 788 | -0.0062 | n/a |
| 5 | 0.55 | 7.78 | 0.32 | 98 | 0.0000 | n/a |
| 6 | 0.00 | 0.09 | 0.26 | 72 | -0.0022 | n/a |
| 7 | 0.28 | 9.36 | 0.09 | 81 | 0.0018 | n/a |
| 8 | -0.09 | -3.72 | 0.15 | 48 | -0.0102 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0931)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.24 | 3.05 | 1.33 | 0.0138 |
| fees_2x | 2.88 | 2.72 | 1.34 | 0.0085 |
| latency_plus1 | 3.71 | 3.45 | 1.33 | 0.0201 |
| latency_plus2 | 1.98 | 1.88 | 1.47 | 0.0017 |
| latency_plus3 | 0.23 | 0.22 | 2.96 | -0.0310 |
| low_liquidity | 3.60 | 3.38 | 1.33 | 0.0191 |
| very_low_liquidity | 3.60 | 3.38 | 1.33 | 0.0191 |
| high_slippage | 2.70 | 2.56 | 1.34 | 0.0103 |
| extreme_slippage | 0.90 | 0.88 | 1.44 | -0.0081 |
| combined_adverse | 2.40 | 2.26 | 1.36 | 0.0053 |
| spread_widen_10bps | -0.07 | -0.04 | 3.01 | -0.0350 |
| spread_widen_25bps | -2.57 | -2.26 | 3.84 | -0.0658 |
| thin_book | 0.24 | 0.15 | 2.39 | -0.0211 |
| very_thin_book | -2.02 | -0.48 | 4.97 | -0.0621 |
| entry_spread_stress | -0.23 | -0.19 | 2.27 | -0.0280 |
| combined_market_deterioration | -0.23 | -0.10 | 2.54 | -0.0291 |
| severe_adverse | -4.17 | -3.24 | 4.21 | -0.0931 |

## Holdout Validation

- **Holdout bars**: 8785
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0043)
- **Trend**: ranging (efficiency: 0.0183)
- **Best holdout score**: 0.0317 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0370 | 0.0019 | 0.51 | 0.32 | 184 |
| 1 | 0.0003 | 0.0132 | 2.54 | 0.91 | 497 |
| 2 | -0.0001 | 0.0055 | 0.92 | 0.40 | 178 |
| 3 | -0.0001 | 0.0037 | 0.64 | 0.28 | 120 |
| 4 | -0.0003 | 0.0317 | 4.28 | 1.08 | 129 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51987
- **Expected rows**: 51993
- **Missing rows**: 6
- **Forward-fill count**: 3
- **Forward-fill fraction**: 5.770673437590167e-05
- **Longest gap (seconds)**: 1500

## Recent 28-Day Window

- **Passed**: True
- **Reason**: 
- **Objective score**: 0.00036676931287863606
- **PnL %**: 0.19822966062796277
- **Trade count**: 124

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35714285714285715
- **Baseline score**: 0.024923412206091795
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.0216, 0.0342 |
| sell_spread_base | 0.0073, 0.0049 |
| stop_loss | 0.0223, 0.0113 |
| take_profit | 0.0249, 0.0249 |
| executor_refresh_time | 0.0087, 0.0016 |
| cooldown_time | 0.0215, 0.0160 |
| total_amount_quote | 0.0245, 0.0251 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4511217670178212
- **Max CV**: 1.134615186373742
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2783 | 1.013232594922158 | 2.180406173936766 | 1.6381921121986582 |
| buy_spread_ratio | 0.1714 | 1.54301728010825 | 2.617458153328844 | 1.897565660957819 |
| sell_spread_base | 0.6450 | 0.20490606349482104 | 1.5166900544906703 | 0.6832719269042493 |
| sell_spread_ratio | 0.1782 | 1.301807058011093 | 2.285926456896903 | 1.624568133199491 |
| buy_side_weight | 0.2451 | 0.2576762289744276 | 0.4847839171561106 | 0.35017839237658227 |
| amount_skew | 0.1679 | 1.9605270542940896 | 3.339515188665578 | 2.5204433702756637 |
| stop_loss | 1.1346 | 0.01187511952849419 | 0.11614927970235976 | 0.02792423984699834 |
| take_profit | 0.9267 | 0.008397169671941221 | 0.0872744883272883 | 0.029858040562508226 |
| executor_refresh_time | 0.4567 | 2109.0 | 11583.0 | 6990.0 |
| cooldown_time | 0.4486 | 1290.0 | 5930.0 | 3568.5 |
| total_amount_quote | 0.3099 | 185.16932151389972 | 977.5952923575834 | 718.1647898179929 |

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
| recent_objective | > 0 | 0.00036676931287863606 | PASS |
| recent_pnl | >= 0 | 0.19822966062796277 | PASS |
| recent_trades | >= 5 | 124 | PASS |
| worst_stress | > -10 | -0.09307165236923666 | PASS |
| sensitivity_penalty | < 0.50 | 0.35714285714285715 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | PASS | score=0.0019 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.09307165236923666 |
| sensitivity | PASS | penalty=0.35714285714285715 |
| recent_28d | PASS | score=0.00036676931287863606, pnl=0.19822966062796277, trades=124, reason= |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4511217670178212 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51987 |  |
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
- **Dev bars**: 35143
- **Holdout bars**: 8785
- **Recent 28d bars**: 8059

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-28T22:10:49.205301+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 3846
