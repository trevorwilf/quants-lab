# PMM Dynamic Optimization Report: mexc_ZRO-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:20:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:20:32.441223+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 18 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ZRO-USDT
- **interval**: 5m+4h
- **n_candles**: 103797
- **dataset_hash**: b160dc5cfd448880291c4a868c87c43b5fb7fdf4608d04c61651b7982d5cd05e
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 332.6196813213258
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 76046 |
| min_volume_quantile | 0.5146856411813219 |
| regime_adx_length | 12 |
| regime_adx_threshold | 10.272708344204537 |
| regime_ema_fast | 82 |
| regime_ema_slow | 135 |
| stop_loss | 0.024925943102706197 |
| take_profit | 0.02811206862184203 |
| take_profit_order_type | MARKET |
| time_limit | 526230 |
| total_amount_quote | 332.6196813213258 |
| trailing_stop_activation | 0.015001100721176315 |
| trailing_stop_delta | 0.012712290604730165 |
| volume_filter_window | 550 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 332.6196813213258 |
| Selected | 332.6196813213258 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 6.7583
- **Net PnL (quote)**: 22.4793
- **Sharpe Ratio**: 1.4101
- **Max Drawdown %**: 3.4844
- **Profit Factor**: 2.3014319332702144
- **Trade Count**: 49
- **Total Fees (quote)**: 1.3448
- **Maker Fees**: 0.6700
- **Taker Fees**: 0.6748
- **Fee Drag %**: 0.4043

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0331
- **PnL Component**: 0.0654
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0261
- **Fee Drag Component**: -0.0020
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0040
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 2.83 | 4.21 | 2.79 | 20 | -0.1144 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 12.44 | 11.17 | 2.09 | 52 | -0.1390 | n/a |
| 16 | -2.58 | -5.99 | 2.84 | 7 | -0.4809 | n/a |
| 17 | -2.58 | -7.93 | 2.58 | 2 | -1000.0000 | n/a |
| 18 | -1.21 | -2.64 | 2.63 | 4 | -0.2167 | n/a |
| 19 | -1.20 | -1.27 | 5.14 | 8 | -0.2207 | n/a |
| 20 | -2.58 | -7.14 | 2.61 | 3 | -1000.0000 | n/a |
| 21 | -2.44 | -4.01 | 5.03 | 7 | -0.2357 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.56 | 1.37 | 3.52 | 0.0299 |
| fees_2x | 6.35 | 1.33 | 3.56 | 0.0267 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 4.67 | 1.01 | 4.80 | 0.0076 |
| very_low_liquidity | 4.16 | 1.02 | 3.17 | 0.0152 |
| high_slippage | 6.25 | 1.30 | 3.58 | 0.0276 |
| extreme_slippage | 5.24 | 1.09 | 3.78 | 0.0165 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 5.15 | 1.09 | 3.66 | 0.0167 |
| spread_widen_25bps | -2.07 | -0.32 | 6.91 | -0.2082 |
| thin_book | -1.32 | -0.21 | 7.64 | -0.2339 |
| very_thin_book | -2.58 | -1.03 | 3.38 | -0.5195 |
| entry_spread_stress | 5.77 | 1.17 | 3.31 | 0.0252 |
| combined_market_deterioration | -2.34 | -0.71 | 5.41 | -0.2218 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19146
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0061)
- **Trend**: ranging (efficiency: 0.0054)
- **Best holdout score**: -0.0858 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9834 | -0.1562 | -1.14 | 3.72 | 21 |
| 1 | -1000.0000 | -0.2347 | -2.53 | 4.23 | 14 |
| 2 | -1000.0000 | -0.3957 | -2.75 | 15.63 | 148 |
| 3 | -1000.0000 | -0.0858 | -2.00 | 8.15 | 72 |
| 4 | -1000.0000 | -0.3380 | -1.65 | 3.60 | 15 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103797
- **Expected rows**: 103799
- **Missing rows**: 2
- **Forward-fill count**: 57
- **Forward-fill fraction**: 0.0005491488193300384
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.5808% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.580839640926853
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

- **Sensitivity penalty**: 0.35
- **Baseline score**: -0.09210892420849509
- **Sign flips**: 0
- **Collapse count**: 7
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.1547, -0.1407 |
| regime_ema_slow | -0.1427, -0.1029 |
| regime_adx_length | -0.0921, -0.0921 |
| regime_adx_threshold | -0.0921, -0.0921 |
| volume_filter_window | -0.0921, -0.0988 |
| min_volume_quantile | -0.0988, -0.1293 |
| stop_loss | -0.1453, -0.1734 |
| take_profit | -0.1000, -0.1154 |
| cooldown_time | -0.4209, -0.1845 |
| total_amount_quote | -0.0963, -0.1313 |

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
| recent_pnl | >= 0 | -2.580839640926853 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.35 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1561868949369365 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.35 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.580839640926853, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.5808% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103797 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.5808% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103797
- **Pre-release bars**: 95734
- **Dev bars**: 76588
- **Holdout bars**: 19146
- **Recent 28d bars**: 8063
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:20:32.441223+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 18
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
