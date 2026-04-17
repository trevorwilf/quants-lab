# PMM Dynamic Optimization Report: nonkyc_TRX-USDT_5m_sweep_v1

Generated: 2026-04-10 01:33:50 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-10T01:33:50.068325+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 11061 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: TRX-USDT
- **interval**: 5m
- **n_candles**: 52112
- **dataset_hash**: 93955fc7da43a5ed98fabad48341c16ee69b86b8da20c6d1a14f063cf25b03b5
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 825.7570817515802
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.9551821009404153 |
| buy_n_levels | 9 |
| buy_side_weight | 0.5382660185762481 |
| buy_spread_base | 4.391146776048398 |
| buy_spread_ratio | 1.5397088763398867 |
| cooldown_time | 5588 |
| executor_refresh_time | 3538 |
| macd_fast | 10 |
| macd_signal | 13 |
| macd_slow | 50 |
| natr_length | 22 |
| sell_n_levels | 4 |
| sell_spread_base | 2.4610450056833644 |
| sell_spread_ratio | 1.7718513884240383 |
| stop_loss | 0.02108818804222771 |
| take_profit | 0.010853498810562799 |
| time_limit | 5331 |
| total_amount_quote | 825.7570817515802 |
| trailing_stop_activation | 0.061526335145753376 |
| trailing_stop_delta | 0.016445687447911573 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 825.7570817515802 |
| Selected | 825.7570817515802 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -9.3299
- **Net PnL (quote)**: -77.0420
- **Sharpe Ratio**: -7.8263
- **Max Drawdown %**: 9.5552
- **Profit Factor**: 0.14195857471358178
- **Trade Count**: 544
- **Total Fees (quote)**: 61.4252
- **Maker Fees**: 22.8074
- **Taker Fees**: 38.6178
- **Fee Drag %**: 7.4387

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2636
- **PnL Component**: -0.0979
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0717
- **Fee Drag Component**: -0.0372
- **Inventory Component**: -0.0087
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1175**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.41 | -7.88 | 0.45 | 44 | -0.0755 | n/a |
| 1 | -0.72 | -10.28 | 0.72 | 56 | -0.1072 | n/a |
| 2 | -0.54 | -13.13 | 0.57 | 58 | -0.0814 | n/a |
| 3 | -0.20 | -6.78 | 0.29 | 60 | -0.1721 | n/a |
| 4 | -1.41 | -8.75 | 1.88 | 85 | -0.1160 | n/a |
| 5 | -0.56 | -7.02 | 0.60 | 48 | -0.0865 | n/a |
| 6 | -0.43 | -10.41 | 0.43 | 42 | -0.1029 | n/a |
| 7 | -0.94 | -15.61 | 0.94 | 42 | -0.1291 | n/a |
| 8 | -0.87 | -14.37 | 0.87 | 36 | -0.1270 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.4653)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -13.05 | -10.53 | 13.22 | -0.3667 |
| fees_2x | -16.77 | -12.89 | 16.88 | -0.4653 |
| latency_plus1 | -9.31 | -7.81 | 9.54 | -0.2625 |
| latency_plus2 | -8.98 | -7.57 | 9.21 | -0.2564 |
| latency_plus3 | -8.78 | -7.35 | 9.00 | -0.2547 |
| low_liquidity | -9.09 | -8.98 | 9.35 | -0.2577 |
| very_low_liquidity | -11.33 | -11.55 | 11.33 | -0.2970 |
| high_slippage | -10.50 | -8.70 | 10.70 | -0.2903 |
| extreme_slippage | -12.83 | -10.33 | 12.98 | -0.3427 |
| combined_adverse | -14.42 | -13.08 | 14.60 | -0.3951 |
| spread_widen_10bps | -10.64 | -8.96 | 10.64 | -0.2923 |
| spread_widen_25bps | -12.47 | -10.26 | 12.47 | -0.3333 |
| thin_book | -10.33 | -9.07 | 10.34 | -0.2717 |
| very_thin_book | -9.07 | -9.40 | 9.07 | -0.2277 |
| entry_spread_stress | -11.23 | -9.42 | 11.23 | -0.3063 |
| combined_market_deterioration | -13.71 | -12.02 | 13.78 | -0.3744 |
| severe_adverse | -15.45 | -12.36 | 15.45 | -0.4049 |

## Holdout Validation

- **Holdout bars**: 8809
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0009)
- **Trend**: ranging (efficiency: 0.0107)
- **Best holdout score**: -0.1083 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.3644 | -0.1083 | -1.40 | 1.41 | 93 |
| 1 | -0.0721 | -0.5094 | -12.41 | 12.41 | 677 |
| 2 | -0.0736 | -0.2710 | -3.75 | 3.75 | 318 |
| 3 | -0.0768 | -0.4747 | -12.31 | 12.31 | 754 |
| 4 | -0.0804 | -0.4088 | -6.32 | 6.32 | 321 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52112
- **Expected rows**: 52112
- **Missing rows**: 0
- **Forward-fill count**: 150
- **Forward-fill fraction**: 0.002878415719987719
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0793 <= 0; recent PnL -0.9058% < 0
- **Objective score**: -0.07934366567062481
- **PnL %**: -0.9058237039338344
- **Trade count**: 47

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3699 <= 0; recent PnL -0.0214% < 0; recent worst stress -1000.0000 < -10.0
- **Objective score**: -0.3698663785924613
- **PnL %**: -0.021424938778801077
- **Trade count**: 7

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.0070% < 0; recent trades 3 < 5; recent worst stress -1000.0000 < -10.0
- **Objective score**: -1000.0
- **PnL %**: -0.007022592376527327
- **Trade count**: 3

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.3043078560651994
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.2555, -0.3576 |
| sell_spread_base | -0.3043, -0.3043 |
| stop_loss | -0.3044, -0.3045 |
| take_profit | -0.3083, -0.2829 |
| executor_refresh_time | -0.3366, -0.2855 |
| cooldown_time | -0.2838, -0.3967 |
| total_amount_quote | -0.3099, -0.6151 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33182435776998837
- **Max CV**: 0.7905944816540122
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit, executor_refresh_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0937 | 3.660900300417186 | 4.6891129591671925 | 4.051222739830428 |
| buy_spread_ratio | 0.0742 | 1.218404561447407 | 1.5591802339962337 | 1.358641196289931 |
| sell_spread_base | 0.5942 | 0.4219551878510441 | 2.42366182039887 | 1.2817038075584215 |
| sell_spread_ratio | 0.1936 | 1.3017684765490112 | 2.5843769149324873 | 1.9393278998453674 |
| buy_side_weight | 0.1950 | 0.37141293908682926 | 0.6996687108678723 | 0.4829193580529948 |
| amount_skew | 0.1337 | 2.369968247706506 | 3.999195225922726 | 3.6582013998794123 |
| stop_loss | 0.3839 | 0.01162934860976366 | 0.03149012576530706 | 0.01866146523246837 |
| take_profit | 0.7906 | 0.005151317457986507 | 0.034062915185018625 | 0.011260294094956106 |
| executor_refresh_time | 0.7040 | 428.0 | 5306.0 | 2380.6 |
| cooldown_time | 0.4300 | 2073.0 | 7157.0 | 3391.0 |
| total_amount_quote | 0.0571 | 828.791996811426 | 994.246834714271 | 931.4964743694702 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
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
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -0.07934366567062481 | FAIL |
| recent_pnl | >= 0 | -0.9058237039338344 | FAIL |
| recent_trades | >= 5 | 47 | PASS |
| worst_stress | > -10 | -0.4652556332943189 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.10826307877305262 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.4652556332943189 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.07934366567062481, pnl=-0.9058237039338344, trades=47, reason=recent objective score -0.0793 <= 0; recent PnL -0.9058% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3698663785924613, pnl=-0.021424938778801077, trades=7, reason=recent objective score -0.3699 <= 0; recent PnL -0.0214% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.007022592376527327, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -0.0070% < 0; recent trades 3 < 5; recent worst stress -1000.0000 < -10.0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33182435776998837 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52112 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0793 <= 0; recent PnL -0.9058% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3699 <= 0; recent PnL -0.0214% < 0; recent worst stress -1000.0000 < -10.0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.0070% < 0; recent trades 3 < 5; recent worst stress -1000.0000 < -10.0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52112
- **Pre-release bars**: 44047
- **Dev bars**: 35238
- **Holdout bars**: 8809
- **Recent 28d bars**: 8065
- **Recent window start**: 1773354300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-10T01:33:50.068325+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 11061
