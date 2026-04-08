# PMM Dynamic Optimization Report: mexc_XMR-USDT_5m_retest_20260408

Generated: 2026-04-08 10:56:40 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T10:56:40.327697+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 1559 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: a2514e76c3b9c0c0e2475696a3eefc35787c61c7f68fb2c16308a1776decd68d
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 857.3290788784221
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.323463064397399 |
| buy_n_levels | 10 |
| buy_side_weight | 0.31311795034733875 |
| buy_spread_base | 3.144989494519053 |
| buy_spread_ratio | 2.3994291970129686 |
| cooldown_time | 651 |
| executor_refresh_time | 3094 |
| macd_fast | 30 |
| macd_signal | 22 |
| macd_slow | 34 |
| natr_length | 45 |
| sell_n_levels | 5 |
| sell_spread_base | 3.6959759430234733 |
| sell_spread_ratio | 1.7509979864661867 |
| stop_loss | 0.0258246685555006 |
| take_profit | 0.006761878125229378 |
| time_limit | 37981 |
| total_amount_quote | 857.3290788784221 |
| trailing_stop_activation | 0.06929568579728915 |
| trailing_stop_delta | 0.04318075882926987 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 857.3290788784221 |
| Selected | 857.3290788784221 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.3367
- **Net PnL (quote)**: -2.8870
- **Sharpe Ratio**: -0.2869
- **Max Drawdown %**: 3.6647
- **Profit Factor**: 1.008994588281887
- **Trade Count**: 942
- **Total Fees (quote)**: 3.0843
- **Maker Fees**: 2.7592
- **Taker Fees**: 0.3251
- **Fee Drag %**: 0.3598

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0443
- **PnL Component**: -0.0034
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0275
- **Fee Drag Component**: -0.0018
- **Inventory Component**: -0.0114
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0026**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.02 | -2.53 | 0.05 | 45 | -0.0206 | n/a |
| 1 | 0.01 | 0.96 | 0.04 | 69 | -0.0018 | n/a |
| 2 | 0.01 | 1.29 | 0.05 | 70 | -0.0019 | n/a |
| 3 | 0.01 | 1.65 | 0.04 | 62 | -0.0017 | n/a |
| 4 | -0.01 | -0.57 | 0.10 | 83 | -0.0025 | n/a |
| 5 | -0.02 | -1.17 | 0.09 | 74 | -0.0025 | n/a |
| 6 | -0.03 | -3.11 | 0.08 | 67 | -0.0026 | n/a |
| 7 | -0.00 | -0.28 | 0.03 | 61 | -0.0018 | n/a |
| 8 | -0.03 | -3.96 | 0.06 | 72 | -0.0024 | n/a |

## Stress Test Results

Worst Scenario: **entry_spread_stress** (score: -0.0527)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.52 | -0.45 | 3.70 | -0.0473 |
| fees_2x | -0.70 | -0.61 | 3.74 | -0.0503 |
| latency_plus1 | -0.35 | -0.30 | 3.65 | -0.0444 |
| latency_plus2 | -0.39 | -0.39 | 3.06 | -0.0385 |
| latency_plus3 | -0.58 | -0.51 | 3.76 | -0.0475 |
| low_liquidity | -0.34 | -0.29 | 3.66 | -0.0443 |
| very_low_liquidity | -0.34 | -0.29 | 3.66 | -0.0443 |
| high_slippage | -0.43 | -0.37 | 3.68 | -0.0454 |
| extreme_slippage | -0.62 | -0.54 | 3.72 | -0.0475 |
| combined_adverse | -0.63 | -0.55 | 3.71 | -0.0485 |
| spread_widen_10bps | -0.72 | -0.63 | 3.79 | -0.0492 |
| spread_widen_25bps | -0.99 | -0.87 | 3.80 | -0.0522 |
| thin_book | -1.16 | -1.53 | 1.80 | -0.0318 |
| very_thin_book | -0.63 | -2.08 | 0.92 | -0.0166 |
| entry_spread_stress | -1.17 | -1.07 | 3.69 | -0.0527 |
| combined_market_deterioration | -1.38 | -1.96 | 2.60 | -0.0429 |
| severe_adverse | -1.37 | -2.65 | 1.87 | -0.0345 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0065)
- **Best holdout score**: -0.0024 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0485 | -0.0024 | -0.00 | 0.08 | 143 |
| 1 | 0.0022 | -0.0043 | 1.44 | 0.72 | 183 |
| 2 | 0.0010 | -0.0098 | 0.63 | 0.34 | 382 |
| 3 | 0.0009 | -0.0105 | 1.20 | 0.65 | 410 |
| 4 | 0.0008 | -0.0038 | 0.18 | 0.40 | 217 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 88
- **Forward-fill fraction**: 0.0016974981192492428
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0056 <= 0; recent PnL -0.0256% < 0
- **Objective score**: -0.005595086812589762
- **PnL %**: -0.025553259688224392
- **Trade count**: 143

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0915 <= 0; recent PnL -0.0307% < 0
- **Objective score**: -0.09145548013434146
- **PnL %**: -0.030703119618848296
- **Trade count**: 75

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1206 <= 0
- **Objective score**: -0.12055972909413068
- **PnL %**: 0.005799182184274023
- **Trade count**: 35

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.039455642354767326
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0211, -0.0277 |
| sell_spread_base | -0.0303, -0.0357 |
| stop_loss | -0.0349, -0.0412 |
| take_profit | -0.0364, -0.0371 |
| executor_refresh_time | -0.0171, -0.0339 |
| cooldown_time | -0.0395, -0.0301 |
| total_amount_quote | -0.0394, -0.0575 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3935716892485275
- **Max CV**: 0.8362966042776633
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.2169 | 1.6257260138236906 | 4.294371808121213 | 3.4795561681291445 |
| buy_spread_ratio | 0.2667 | 1.2621483626243493 | 2.473117653787463 | 1.530181278666224 |
| sell_spread_base | 0.6246 | 0.39466576278822796 | 4.100299824250021 | 2.0214987623972767 |
| sell_spread_ratio | 0.2533 | 1.2442194823525223 | 2.9334673902082384 | 2.160411935178006 |
| buy_side_weight | 0.2489 | 0.22730933375740528 | 0.7603988190093827 | 0.6546819871089029 |
| amount_skew | 0.2269 | 1.6357571493760188 | 3.6207422553093056 | 2.509957010330212 |
| stop_loss | 0.5674 | 0.027336820436659304 | 0.1738997901142235 | 0.09081020591482013 |
| take_profit | 0.6169 | 0.00837983966817242 | 0.14585726063674398 | 0.08270464993540404 |
| executor_refresh_time | 0.3433 | 2110.0 | 8035.0 | 5413.8 |
| cooldown_time | 0.8363 | 173.0 | 5361.0 | 1919.2 |
| total_amount_quote | 0.1281 | 585.7784295053456 | 972.6549974556914 | 833.6971595556977 |

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
| recent_objective | > 0 | -0.005595086812589762 | FAIL |
| recent_pnl | >= 0 | -0.025553259688224392 | FAIL |
| recent_trades | >= 5 | 143 | PASS |
| worst_stress | > -10 | -0.0526603305209033 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.002369173123797724 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=entry_spread_stress score=-0.0526603305209033 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.005595086812589762, pnl=-0.025553259688224392, trades=143, reason=recent objective score -0.0056 <= 0; recent PnL -0.0256% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.09145548013434146, pnl=-0.030703119618848296, trades=75, reason=recent objective score -0.0915 <= 0; recent PnL -0.0307% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12055972909413068, pnl=0.005799182184274023, trades=35, reason=recent objective score -0.1206 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3935716892485275 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0056 <= 0; recent PnL -0.0256% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0915 <= 0; recent PnL -0.0307% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1206 <= 0 |
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
- **run_timestamp**: 2026-04-08T10:56:40.327697+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 1559
