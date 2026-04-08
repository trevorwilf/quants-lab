# PMM Dynamic Optimization Report: nonkyc_ARRR-XMR_5m_sweep_v1

Generated: 2026-04-08 19:50:17 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T19:50:17.888026+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 11496 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARRR-XMR
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 3f339a2a3c485e80dd8d6a8e4d4e6e7c07299fc6be4629e45470b43717e2f0f2
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 614.2599043311498
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.778070791311487 |
| buy_n_levels | 4 |
| buy_side_weight | 0.5687607338243532 |
| buy_spread_base | 4.23675058038094 |
| buy_spread_ratio | 2.8438947324668016 |
| cooldown_time | 197 |
| executor_refresh_time | 2650 |
| macd_fast | 23 |
| macd_signal | 15 |
| macd_slow | 39 |
| natr_length | 13 |
| sell_n_levels | 8 |
| sell_spread_base | 2.584054763201826 |
| sell_spread_ratio | 2.656996471340739 |
| stop_loss | 0.12761515746676508 |
| take_profit | 0.008889054987421211 |
| time_limit | 125528 |
| total_amount_quote | 614.2599043311498 |
| trailing_stop_activation | 0.030577042640267046 |
| trailing_stop_delta | 0.006118627154575592 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 614.2599043311498 |
| Selected | 614.2599043311498 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.1096
- **Net PnL (quote)**: -0.6730
- **Sharpe Ratio**: -2.8523
- **Max Drawdown %**: 0.1149
- **Profit Factor**: 0.4069066632976763
- **Trade Count**: 1002
- **Total Fees (quote)**: 0.0671
- **Maker Fees**: 0.0228
- **Taker Fees**: 0.0444
- **Fee Drag %**: 0.0109
- **TP Min-Notional Failures**: 10862 :warning:
  > 10862 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0022
- **PnL Component**: -0.0011
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0009
- **Fee Drag Component**: -0.0001
- **Inventory Component**: -0.0002
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0751**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 1.60 | 0.00 | 157 | -0.0000 | n/a |
| 1 | 0.00 | 0.80 | 0.00 | 1 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 1.43 | 0.01 | 133 | -0.0000 | n/a |
| 4 | -0.00 | -4.49 | 0.00 | 42 | -0.0501 | n/a |
| 5 | -0.00 | -2.41 | 0.01 | 90 | -0.2956 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | -0.00 | -0.21 | 0.00 | 24 | -0.3728 | n/a |

## Stress Test Results

Worst Scenario: **very_thin_book** (score: -0.1280)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.12 | -3.00 | 0.12 | -0.0023 |
| fees_2x | -0.12 | -3.14 | 0.13 | -0.0024 |
| latency_plus1 | -0.11 | -2.86 | 0.11 | -0.0022 |
| latency_plus2 | -0.11 | -2.85 | 0.11 | -0.0022 |
| latency_plus3 | -0.10 | -2.77 | 0.11 | -0.0021 |
| low_liquidity | -0.05 | -2.85 | 0.06 | -0.0011 |
| very_low_liquidity | -0.03 | -2.85 | 0.03 | -0.0005 |
| high_slippage | -0.11 | -2.90 | 0.12 | -0.0022 |
| extreme_slippage | -0.11 | -3.00 | 0.12 | -0.0023 |
| combined_adverse | -0.06 | -3.05 | 0.06 | -0.0012 |
| spread_widen_10bps | -0.11 | -2.88 | 0.12 | -0.0022 |
| spread_widen_25bps | -0.11 | -2.83 | 0.12 | -0.0022 |
| thin_book | 0.00 | 0.28 | 0.00 | -0.0280 |
| very_thin_book | -0.00 | -0.24 | 0.00 | -0.1280 |
| entry_spread_stress | -0.11 | -2.86 | 0.12 | -0.0022 |
| combined_market_deterioration | -0.03 | -2.71 | 0.03 | -0.0005 |
| severe_adverse | -0.00 | -0.16 | 0.00 | -0.0640 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0075)
- **Trend**: ranging (efficiency: 0.0081)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0651 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | 0.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 514
- **Forward-fill fraction**: 0.009901180821759482
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.002162123529472465
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0018, -0.0020 |
| sell_spread_base | -0.0022, -0.0022 |
| stop_loss | -0.0024, -0.0297 |
| take_profit | -0.0022, -0.0022 |
| executor_refresh_time | -0.0294, -0.0300 |
| cooldown_time | -0.0022, -0.0022 |
| total_amount_quote | -0.0020, -0.0024 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3905207579273923
- **Max CV**: 1.1761506778548372
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0962 | 4.389017340886252 | 5.935763466551744 | 5.40635571982237 |
| buy_spread_ratio | 0.1789 | 1.3679252286093764 | 2.5356563492658455 | 1.870172417437913 |
| sell_spread_base | 0.6384 | 0.22104839966820708 | 5.150016625780557 | 2.5206246263530336 |
| sell_spread_ratio | 0.1433 | 1.6030263415334032 | 2.421995948437262 | 1.8376146131737716 |
| buy_side_weight | 0.3655 | 0.2151372430407515 | 0.7271827669474195 | 0.43816224891307326 |
| amount_skew | 0.2377 | 1.0927284253203493 | 1.949682103614 | 1.5591827623770738 |
| stop_loss | 0.3684 | 0.07348654708514606 | 0.24756393607843466 | 0.1784828001954871 |
| take_profit | 1.1762 | 0.005167632238246366 | 0.08856014495078347 | 0.02774185997882602 |
| executor_refresh_time | 0.3905 | 2168.0 | 5579.0 | 3809.3 |
| cooldown_time | 0.3928 | 1445.0 | 5192.0 | 3203.6 |
| total_amount_quote | 0.3078 | 305.18654427906057 | 959.125275599009 | 731.5768812635631 |

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
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -0.12802580046137998 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=very_thin_book score=-0.12802580046137998 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3905207579273923 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51913
- **Pre-release bars**: 43848
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T19:50:17.888026+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 11496
