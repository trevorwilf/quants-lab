# PMM Dynamic Optimization Report: mexc_WLD-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:16:43 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:16:43.867739+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 27 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: WLD-USDT
- **interval**: 5m+4h
- **n_candles**: 103799
- **dataset_hash**: 8f1c0afd0308a6c19c88e4d34aeb0b4152d69557483310675968dd91d3746659
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 165.68446337759
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 84260 |
| min_volume_quantile | 0.5803622672606 |
| regime_adx_length | 18 |
| regime_adx_threshold | 13.157885622106722 |
| regime_ema_fast | 76 |
| regime_ema_slow | 96 |
| stop_loss | 0.07813259749146038 |
| take_profit | 0.02692412656578914 |
| take_profit_order_type | LIMIT |
| time_limit | 265499 |
| total_amount_quote | 165.68446337759 |
| trailing_stop_activation | 0.006724490614758733 |
| trailing_stop_delta | 0.000549345626451439 |
| volume_filter_window | 556 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 165.68446337759 |
| Selected | 165.68446337759 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.8461
- **Net PnL (quote)**: 8.0293
- **Sharpe Ratio**: 1.8139
- **Max Drawdown %**: 1.8843
- **Profit Factor**: inf
- **Trade Count**: 8
- **Total Fees (quote)**: 0.4656
- **Maker Fees**: 0.2320
- **Taker Fees**: 0.2337
- **Fee Drag %**: 0.2810

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1363
- **PnL Component**: 0.0473
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0141
- **Fee Drag Component**: -0.0014
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1680
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
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 6.55 | 9.42 | 1.88 | 10 | -0.3555 | n/a |
| 16 | -5.27 | -6.78 | 6.10 | 1 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | -3.41 | -6.58 | 4.16 | 3 | -1000.0000 | n/a |
| 20 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.71 | 1.76 | 1.89 | -0.1383 |
| fees_2x | 4.57 | 1.72 | 1.89 | -0.1404 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 4.85 | 1.81 | 1.88 | -0.1323 |
| very_low_liquidity | 4.85 | 1.81 | 1.88 | -0.1283 |
| high_slippage | 4.49 | 1.71 | 1.89 | -0.1397 |
| extreme_slippage | 3.79 | 1.48 | 1.90 | -0.1465 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 5.05 | 1.74 | 1.88 | -0.1343 |
| spread_widen_25bps | 4.87 | 1.55 | 1.88 | -0.1360 |
| thin_book | 4.28 | 0.86 | 3.71 | -0.1592 |
| very_thin_book | 4.25 | 1.63 | 1.80 | -0.1451 |
| entry_spread_stress | 4.87 | 1.67 | 1.88 | -0.1360 |
| combined_market_deterioration | 4.62 | 1.55 | 1.89 | -0.1391 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19156
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0137)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0681 | -1000.0000 | -3.77 | 6.01 | 3 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103799
- **Expected rows**: 103845
- **Missing rows**: 46
- **Forward-fill count**: 29
- **Forward-fill fraction**: 0.00027938612125357664
- **Longest gap (seconds)**: 13500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.628340573152643
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.628340573152643
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.628340573152643
- **Trade count**: 2

## Sensitivity Analysis

- **Sensitivity penalty**: 0.1
- **Baseline score**: -0.32135397961257445
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -0.3192 |
| regime_ema_slow | -1000.0000, -0.3192 |
| regime_adx_length | -0.3214, -0.3214 |
| regime_adx_threshold | -0.2557, -0.3214 |
| volume_filter_window | -0.3214, -0.3214 |
| min_volume_quantile | -0.3214, -0.3214 |
| stop_loss | -0.3094, -0.2940 |
| take_profit | -0.3214, -0.3214 |
| cooldown_time | -0.2460, -0.3138 |
| total_amount_quote | -0.3214, -0.3214 |

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
| recent_pnl | >= 0 | 0.628340573152643 | PASS |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.1 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.1 |
| recent_28d | FAIL | score=-1000.0, pnl=0.628340573152643, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.628340573152643, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.628340573152643, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103799 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103799
- **Pre-release bars**: 95780
- **Dev bars**: 76624
- **Holdout bars**: 19156
- **Recent 28d bars**: 8019
- **Recent window start**: 1774026000

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:16:43.867739+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 27
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
