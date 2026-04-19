# PMM Dynamic Optimization Report: nonkyc_AAVE-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:40:40 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:40:40.732277+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 4035 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AAVE-USDT
- **interval**: 5m
- **n_candles**: 51876
- **dataset_hash**: bdfe21e8aa8ddde6e03f8438da5ec6654c22587b45cd2838882e108669f83d3e
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 887.729256894634
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 10 |
| bb_length | 30 |
| bb_std | 1.473076024342199 |
| bbp_entry_threshold | 0.15099670539261678 |
| cooldown_time | 72344 |
| max_atr_pct_for_entry | 0.036270259757495135 |
| min_volume_quantile | 0.05261082986557978 |
| rsi_entry_threshold | 47.59589451712742 |
| rsi_length | 10 |
| stop_loss | 0.016142096246720115 |
| take_profit | 0.005026634511922205 |
| take_profit_order_type | MARKET |
| time_limit | 268704 |
| total_amount_quote | 887.729256894634 |
| trailing_stop_activation | 0.027351784615801046 |
| trailing_stop_delta | 0.002969366254163228 |
| trend_ema_length | 266 |
| use_trend_filter | False |
| volume_filter_window | 280 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 887.729256894634 |
| Selected | 887.729256894634 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.2444
- **Net PnL (quote)**: -11.0468
- **Sharpe Ratio**: -1.8157
- **Max Drawdown %**: 1.4752
- **Profit Factor**: 0.12461221815900621
- **Trade Count**: 123
- **Total Fees (quote)**: 5.4572
- **Maker Fees**: 1.9175
- **Taker Fees**: 3.5397
- **Fee Drag %**: 0.6147

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0267
- **PnL Component**: -0.0125
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0111
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0413**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.36 | -8.03 | 1.62 | 102 | -0.0307 | n/a |
| 1 | -1.26 | -6.26 | 1.56 | 23 | -0.1355 | n/a |
| 2 | -1.10 | -4.13 | 1.36 | 27 | -0.1165 | n/a |
| 3 | -1.55 | -3.84 | 1.94 | 56 | -0.0352 | n/a |
| 4 | -1.72 | -8.75 | 1.89 | 32 | -0.3347 | n/a |
| 5 | -1.63 | -5.73 | 1.98 | 113 | -0.0370 | n/a |
| 6 | -1.56 | -4.35 | 2.06 | 65 | -0.0377 | n/a |
| 7 | -1.56 | -9.41 | 1.66 | 61 | -0.0315 | n/a |
| 8 | -1.36 | -15.17 | 1.40 | 30 | -0.3348 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.55 | -2.23 | 1.59 | -0.0322 |
| fees_2x | -1.86 | -2.62 | 1.87 | -0.0652 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.73 | -3.68 | 2.80 | -0.2047 |
| very_low_liquidity | -2.26 | -4.69 | 2.34 | -0.1643 |
| high_slippage | -1.34 | -1.95 | 1.51 | -0.0279 |
| extreme_slippage | -1.54 | -2.22 | 1.62 | -0.0308 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.62 | -2.81 | 1.64 | -0.0318 |
| spread_widen_25bps | -2.08 | -3.78 | 2.11 | -0.0400 |
| thin_book | -2.38 | -4.14 | 2.47 | -0.1767 |
| very_thin_book | -2.05 | -5.46 | 2.12 | -0.1825 |
| entry_spread_stress | -2.07 | -3.78 | 2.09 | -0.0396 |
| combined_market_deterioration | -1.23 | -5.25 | 1.23 | -0.1322 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0062)
- **Best holdout score**: -0.0520 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0133 | -0.2138 | -1.52 | 1.56 | 51 |
| 1 | -0.0329 | -0.3861 | -1.86 | 1.92 | 15 |
| 2 | -0.0335 | -0.3199 | -1.92 | 2.05 | 17 |
| 3 | -0.0343 | -0.0520 | -2.45 | 2.68 | 61 |
| 4 | -0.0345 | -0.2886 | -2.81 | 3.07 | 26 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51876
- **Expected rows**: 51899
- **Missing rows**: 23
- **Forward-fill count**: 192
- **Forward-fill fraction**: 0.0037011334721258385
- **Longest gap (seconds)**: 6300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0963 <= 0; recent PnL -1.9685% < 0
- **Objective score**: -0.09631417977799273
- **PnL %**: -1.9684976494189272
- **Trade count**: 72

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1295 <= 0; recent PnL -1.6484% < 0
- **Objective score**: -0.12947813157517107
- **PnL %**: -1.6484150221562113
- **Trade count**: 190

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1606 <= 0; recent PnL -1.0266% < 0
- **Objective score**: -0.16062309620238688
- **PnL %**: -1.026632140970183
- **Trade count**: 115

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07692307692307693
- **Baseline score**: -0.026434286333029404
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0264, -0.0264 |
| bb_std | -0.0264, -0.0264 |
| bbp_entry_threshold | -0.0264, -0.0264 |
| rsi_length | -0.0264, -0.0264 |
| rsi_entry_threshold | -0.0264, -0.0264 |
| trend_ema_length | -0.2353, -0.2397 |
| max_atr_pct_for_entry | -0.0264, -0.0264 |
| volume_filter_window | -0.0264, -0.0264 |
| min_volume_quantile | -0.0264, -0.0264 |
| stop_loss | -0.0284, -0.0369 |
| take_profit | -0.0258, -0.0271 |
| cooldown_time | -0.0360, -0.0276 |
| total_amount_quote | -0.0364, -0.0248 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.17701365479001824
- **Max CV**: 0.3303057124276569
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.0354 | 0.015005279491481636 | 0.016455888483635855 | 0.015599097593672867 |
| take_profit | 0.3303 | 0.005119051610294515 | 0.012783550605647783 | 0.0068597310583542025 |
| cooldown_time | 0.2876 | 25052.0 | 81099.0 | 58836.9 |
| total_amount_quote | 0.0547 | 829.1437521350484 | 968.2255295608745 | 907.7073445916398 |

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **refresh_close_mode**: market_close

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: **FAIL**
- yaml_validates: **FAIL**
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
| recent_objective | > 0 | -0.09631417977799273 | FAIL |
| recent_pnl | >= 0 | -1.9684976494189272 | FAIL |
| recent_trades | >= 5 | 72 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.07692307692307693 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.21381923953524834 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.07692307692307693 |
| recent_28d | FAIL | score=-0.09631417977799273, pnl=-1.9684976494189272, trades=72, reason=recent objective score -0.0963 <= 0; recent PnL -1.9685% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.12947813157517107, pnl=-1.6484150221562113, trades=190, reason=recent objective score -0.1295 <= 0; recent PnL -1.6484% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.16062309620238688, pnl=-1.026632140970183, trades=115, reason=recent objective score -0.1606 <= 0; recent PnL -1.0266% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.17701365479001824 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51876 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0963 <= 0; recent PnL -1.9685% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1295 <= 0; recent PnL -1.6484% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1606 <= 0; recent PnL -1.0266% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51876
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8042
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T11:40:40.732277+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 4035
- **validation_status**: validated_fail
