# PMM Dynamic Optimization Report: mexc_SAHARA-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:12:00 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:12:00.057354+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 38 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SAHARA-USDT
- **interval**: 5m+4h
- **n_candles**: 57816
- **dataset_hash**: 8350abaa8644a8f519e5b5ff1e4a85494aec4b7abd4a49690915cc35146b45a7
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 318.3709738516127
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 27870 |
| min_volume_quantile | 0.5473825614821757 |
| regime_adx_length | 11 |
| regime_adx_threshold | 27.321386650878157 |
| regime_ema_fast | 90 |
| regime_ema_slow | 285 |
| stop_loss | 0.0267059819388628 |
| take_profit | 0.012705116089800631 |
| take_profit_order_type | LIMIT |
| time_limit | 240897 |
| total_amount_quote | 318.3709738516127 |
| trailing_stop_activation | 0.047624296317007514 |
| trailing_stop_delta | 0.003962571208207217 |
| volume_filter_window | 95 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 318.3709738516127 |
| Selected | 318.3709738516127 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 23.7661
- **Net PnL (quote)**: 75.6644
- **Sharpe Ratio**: 3.3273
- **Max Drawdown %**: 1.6848
- **Profit Factor**: 43084.036888144125
- **Trade Count**: 14
- **Total Fees (quote)**: 1.0341
- **Maker Fees**: 0.9608
- **Taker Fees**: 0.0734
- **Fee Drag %**: 0.3248

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0548
- **PnL Component**: 0.2132
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0126
- **Fee Drag Component**: -0.0016
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1440
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 5.28 | 8.64 | 1.67 | 8 | -0.3712 | n/a |
| 1 | 18.85 | 8.52 | 0.87 | 10 | 0.0050 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 1.23 | 7.22 | 0.00 | 2 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 23.60 | 3.31 | 1.69 | 0.0527 |
| fees_2x | 23.44 | 3.29 | 1.69 | 0.0506 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 23.77 | 3.34 | 1.68 | 0.0749 |
| very_low_liquidity | 22.41 | 3.14 | 1.68 | 0.1119 |
| high_slippage | 23.71 | 3.33 | 1.68 | 0.0544 |
| extreme_slippage | 23.59 | 3.32 | 1.68 | 0.0535 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 23.72 | 3.33 | 1.69 | 0.0545 |
| spread_widen_25bps | 19.65 | 2.69 | 3.60 | 0.0067 |
| thin_book | 23.77 | 3.37 | 1.45 | 0.0646 |
| very_thin_book | 22.24 | 3.19 | 1.45 | 0.0365 |
| entry_spread_stress | 23.69 | 3.33 | 1.69 | 0.0543 |
| combined_market_deterioration | 23.50 | 3.35 | 1.45 | 0.0617 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 9952
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0070)
- **Trend**: ranging (efficiency: 0.0124)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9726 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | -3.32 | 4.78 | 1 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 57816
- **Expected rows**: 57826
- **Missing rows**: 10
- **Forward-fill count**: 193
- **Forward-fill fraction**: 0.003338176283381763
- **Longest gap (seconds)**: 3300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 1.229459869819657
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2
- **Baseline score**: 0.0685743470311373
- **Sign flips**: 2
- **Collapse count**: 2
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | 0.0686, 0.0686 |
| regime_ema_slow | 0.0686, 0.0686 |
| regime_adx_length | 0.0526, 0.0389 |
| regime_adx_threshold | 0.0389, 0.0526 |
| volume_filter_window | 0.0647, 0.0903 |
| min_volume_quantile | -0.3717, 0.0823 |
| stop_loss | 0.0686, 0.0686 |
| take_profit | -0.0059, 0.0622 |
| cooldown_time | 0.0686, 0.0686 |
| total_amount_quote | 0.0686, 0.0686 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5755714253901677
- **Max CV**: 0.7234175758948191
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4708 | 0.022961564713937427 | 0.0825158425491216 | 0.04414834791047861 |
| take_profit | 0.6187 | 0.01645477416780652 | 0.07948998901397729 | 0.037266436929498895 |
| cooldown_time | 0.7234 | 4806.0 | 83356.0 | 36402.3 |
| total_amount_quote | 0.4893 | 142.22499629651378 | 670.0304205910417 | 380.94402331641834 |

## Execution Realism Assumptions

- **taker_probability**: 0.0
- **supports_post_only**: True
- **connector**: mexc
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
- walkforward_robust: **FAIL**
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 1.229459869819657 | PASS |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.2 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 11 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.2 |
| recent_28d | FAIL | score=-1000.0, pnl=1.229459869819657, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 57816 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 57816
- **Pre-release bars**: 49761
- **Dev bars**: 39809
- **Holdout bars**: 9952
- **Recent 28d bars**: 8055
- **Recent window start**: 1774015500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:12:00.057354+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 38
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
