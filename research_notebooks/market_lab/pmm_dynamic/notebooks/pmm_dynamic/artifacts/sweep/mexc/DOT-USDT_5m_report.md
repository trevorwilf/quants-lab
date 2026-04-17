# PMM Dynamic Optimization Report: mexc_DOT-USDT_5m_sweep_v1

Generated: 2026-04-09 03:27:06 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T03:27:06.493177+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 7276 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOT-USDT
- **interval**: 5m
- **n_candles**: 51871
- **dataset_hash**: 243a850f3dbf99fb8bb06f9906f0d734735311470cc15ebbe8a19edcb54a6117
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 603.0126658868548
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.414805441310114 |
| buy_n_levels | 10 |
| buy_side_weight | 0.5820381673317567 |
| buy_spread_base | 2.247288034635704 |
| buy_spread_ratio | 2.663105117134921 |
| cooldown_time | 593 |
| executor_refresh_time | 3358 |
| macd_fast | 28 |
| macd_signal | 6 |
| macd_slow | 74 |
| natr_length | 22 |
| sell_n_levels | 10 |
| sell_spread_base | 4.591017234203137 |
| sell_spread_ratio | 2.3995735438608325 |
| stop_loss | 0.18073746497674245 |
| take_profit | 0.033164686825304164 |
| time_limit | 84898 |
| total_amount_quote | 603.0126658868548 |
| trailing_stop_activation | 0.0015952545313835326 |
| trailing_stop_delta | 0.001176455477487875 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 603.0126658868548 |
| Selected | 603.0126658868548 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 0.8982
- **Net PnL (quote)**: 5.4165
- **Sharpe Ratio**: 0.9058
- **Max Drawdown %**: 1.4877
- **Profit Factor**: 1.3728776688358735
- **Trade Count**: 776
- **Total Fees (quote)**: 2.5473
- **Maker Fees**: 1.2735
- **Taker Fees**: 1.2738
- **Fee Drag %**: 0.4224

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0131
- **PnL Component**: 0.0089
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0112
- **Fee Drag Component**: -0.0021
- **Inventory Component**: -0.0086
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0006**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.25 | -7.85 | 0.28 | 86 | -0.0075 | n/a |
| 1 | -0.01 | -0.60 | 0.11 | 72 | -0.0011 | n/a |
| 2 | 0.10 | 11.49 | 0.01 | 47 | -0.0112 | n/a |
| 3 | 0.12 | 11.98 | 0.02 | 78 | 0.0008 | n/a |
| 4 | -0.27 | -1.91 | 0.70 | 81 | -0.0082 | n/a |
| 5 | 0.52 | 11.72 | 0.09 | 76 | 0.0043 | n/a |
| 6 | 0.09 | 3.62 | 0.10 | 58 | -0.0000 | n/a |
| 7 | 0.06 | 7.89 | 0.02 | 63 | 0.0003 | n/a |
| 8 | 0.02 | 1.97 | 0.03 | 54 | -0.0002 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.0753)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.69 | 0.70 | 1.51 | -0.0164 |
| fees_2x | 0.48 | 0.49 | 1.60 | -0.0203 |
| latency_plus1 | 0.34 | 0.38 | 1.65 | -0.0198 |
| latency_plus2 | 0.12 | 0.15 | 1.65 | -0.0220 |
| latency_plus3 | -0.06 | -0.05 | 1.71 | -0.0243 |
| low_liquidity | 0.90 | 0.91 | 1.49 | -0.0131 |
| very_low_liquidity | 0.90 | 0.91 | 1.49 | -0.0131 |
| high_slippage | 0.37 | 0.38 | 1.64 | -0.0195 |
| extreme_slippage | -0.69 | -0.67 | 2.08 | -0.0368 |
| combined_adverse | -0.39 | -0.41 | 1.86 | -0.0297 |
| spread_widen_10bps | -0.30 | -0.24 | 2.20 | -0.0348 |
| spread_widen_25bps | -0.48 | -0.42 | 2.45 | -0.0364 |
| thin_book | -1.21 | -0.92 | 3.34 | -0.0440 |
| very_thin_book | -0.99 | -2.43 | 1.11 | -0.0241 |
| entry_spread_stress | -0.41 | -0.36 | 2.13 | -0.0335 |
| combined_market_deterioration | -2.54 | -2.02 | 3.72 | -0.0702 |
| severe_adverse | -2.57 | -3.11 | 2.78 | -0.0753 |

## Holdout Validation

- **Holdout bars**: 8761
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0041)
- **Trend**: ranging (efficiency: 0.0083)
- **Best holdout score**: 0.0043 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0442 | -0.0001 | 0.10 | 0.10 | 126 |
| 1 | 0.0011 | -0.0016 | 0.72 | 0.22 | 166 |
| 2 | 0.0008 | 0.0043 | 1.22 | 0.16 | 309 |
| 3 | 0.0006 | 0.0024 | 1.02 | 0.34 | 138 |
| 4 | 0.0004 | 0.0011 | 0.41 | 0.05 | 141 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51871
- **Expected rows**: 51871
- **Missing rows**: 0
- **Forward-fill count**: 7
- **Forward-fill fraction**: 0.00013495016483198704
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0001 <= 0
- **Objective score**: -0.00013793404385314487
- **PnL %**: 0.05332265950931752
- **Trade count**: 100

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0203 <= 0
- **Objective score**: -0.020282540403071814
- **PnL %**: 0.022527877347193206
- **Trade count**: 45

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1241 <= 0
- **Objective score**: -0.12414983073678768
- **PnL %**: 0.001142002632691426
- **Trade count**: 19

## Sensitivity Analysis

- **Sensitivity penalty**: 0.42857142857142855
- **Baseline score**: -0.0067625128392689166
- **Sign flips**: 0
- **Collapse count**: 6
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0163, -0.0054 |
| sell_spread_base | -0.0133, -0.0136 |
| stop_loss | -0.0054, -0.0062 |
| take_profit | -0.0068, -0.0068 |
| executor_refresh_time | -0.0378, -0.0315 |
| cooldown_time | -0.0255, -0.0068 |
| total_amount_quote | -0.0091, -0.0100 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3591154843239792
- **Max CV**: 0.5850271731442042
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, total_amount_quote
- **Scattered params**: take_profit, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1835 | 1.8741056542954275 | 3.177223900557276 | 2.36455054396223 |
| buy_spread_ratio | 0.2620 | 1.4339035254589119 | 2.823060872775753 | 1.9001787952883789 |
| sell_spread_base | 0.4188 | 1.444962390131995 | 5.8646550284712 | 3.7875723590320156 |
| sell_spread_ratio | 0.2532 | 1.5259490637565718 | 2.9992834775943904 | 2.1405358448691705 |
| buy_side_weight | 0.3722 | 0.2070141744758947 | 0.794092829647653 | 0.5135155109211175 |
| amount_skew | 0.2756 | 1.3057423128868968 | 3.616268191953172 | 2.3164401400354175 |
| stop_loss | 0.3462 | 0.05138238968469729 | 0.14889531773540746 | 0.09683392390615223 |
| take_profit | 0.5632 | 0.013826271317007413 | 0.09998165485526393 | 0.051089088220676246 |
| executor_refresh_time | 0.5850 | 747.0 | 10639.0 | 5963.5 |
| cooldown_time | 0.5022 | 195.0 | 2601.0 | 1509.2 |
| total_amount_quote | 0.1883 | 590.7008068150243 | 983.9652649256718 | 797.8874409687878 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **touch_through**: False
- **maker_fill_probability**: 1.0
- **refresh_close_mode**: market_close

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
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.00013793404385314487 | FAIL |
| recent_pnl | >= 0 | 0.05332265950931752 | PASS |
| recent_trades | >= 5 | 100 | PASS |
| worst_stress | > -10 | -0.07532669334259649 | PASS |
| sensitivity_penalty | < 0.50 | 0.42857142857142855 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-7.7513229769168e-05 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.07532669334259649 |
| sensitivity | PASS | penalty=0.42857142857142855 |
| recent_28d | FAIL | score=-0.00013793404385314487, pnl=0.05332265950931752, trades=100, reason=recent objective score -0.0001 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.020282540403071814, pnl=0.022527877347193206, trades=45, reason=recent objective score -0.0203 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.12414983073678768, pnl=0.001142002632691426, trades=19, reason=recent objective score -0.1241 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3591154843239792 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51871 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0001 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0203 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1241 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51871
- **Pre-release bars**: 43806
- **Dev bars**: 35045
- **Holdout bars**: 8761
- **Recent 28d bars**: 8065
- **Recent window start**: 1773281400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T03:27:06.493177+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 7276
