# PMM Dynamic Optimization Report: mexc_DOT-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:00:45 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:00:45.733074+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 32 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: DOT-USDT
- **interval**: 5m+4h
- **n_candles**: 103802
- **dataset_hash**: f15861b5a9c76ecbf5afc2ca7828f741a2fb89f474f38e16af01df1e418fb36b
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 483.49117722806966
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 21011 |
| min_volume_quantile | 0.3554829411666655 |
| regime_adx_length | 10 |
| regime_adx_threshold | 24.19094883560143 |
| regime_ema_fast | 82 |
| regime_ema_slow | 110 |
| stop_loss | 0.03910491491840715 |
| take_profit | 0.02086040783557632 |
| take_profit_order_type | LIMIT |
| time_limit | 97112 |
| total_amount_quote | 483.49117722806966 |
| trailing_stop_activation | 0.04219745730590843 |
| trailing_stop_delta | 0.007805239370491803 |
| volume_filter_window | 365 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 483.49117722806966 |
| Selected | 483.49117722806966 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 4.3544
- **Net PnL (quote)**: 21.0533
- **Sharpe Ratio**: 0.6300
- **Max Drawdown %**: 3.5604
- **Profit Factor**: 3.44351826227409
- **Trade Count**: 5
- **Total Fees (quote)**: 0.9713
- **Maker Fees**: 0.7796
- **Taker Fees**: 0.1918
- **Fee Drag %**: 0.2009

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1654
- **PnL Component**: 0.0426
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0267
- **Fee Drag Component**: -0.0010
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1800
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
| 15 | -1.10 | -1.45 | 3.58 | 3 | -1000.0000 | n/a |
| 16 | -1.39 | -2.67 | 3.81 | 3 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | -4.00 | -7.24 | 4.00 | 2 | -1000.0000 | n/a |
| 20 | -1.03 | -1.21 | 3.13 | 1 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 4.25 | 0.62 | 3.56 | -0.1669 |
| fees_2x | 4.15 | 0.60 | 3.57 | -0.1683 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 4.35 | 0.63 | 3.56 | -0.1614 |
| very_low_liquidity | 4.35 | 0.63 | 3.56 | -0.1494 |
| high_slippage | 4.26 | 0.62 | 3.56 | -0.1663 |
| extreme_slippage | 4.06 | 0.59 | 3.56 | -0.1682 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 4.26 | 0.61 | 3.56 | -0.1663 |
| spread_widen_25bps | 1.19 | 0.21 | 5.55 | -0.2110 |
| thin_book | -1.26 | -0.14 | 6.91 | -0.2456 |
| very_thin_book | -2.29 | -0.30 | 6.94 | -0.2793 |
| entry_spread_stress | 4.21 | 0.61 | 3.56 | -0.1668 |
| combined_market_deterioration | -1.49 | -0.17 | 6.98 | -0.2528 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19147
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0093)
- **Best holdout score**: -0.3960 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0827 | -0.3960 | -1.56 | 5.61 | 5 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103802
- **Expected rows**: 103803
- **Missing rows**: 1
- **Forward-fill count**: 23
- **Forward-fill fraction**: 0.00022157569218319494
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.1796% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.1795934609179684
- **Trade count**: 1

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

- **Sensitivity penalty**: 0.05
- **Baseline score**: -0.24958983977731702
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.2496, -0.2390 |
| regime_ema_slow | -0.2496, -0.2390 |
| regime_adx_length | -0.3410, -0.2496 |
| regime_adx_threshold | -0.3410, -0.2496 |
| volume_filter_window | -0.2496, -0.2496 |
| min_volume_quantile | -0.2496, -0.2496 |
| stop_loss | -0.2630, -0.2356 |
| take_profit | -0.2778, -0.2608 |
| cooldown_time | -1000.0000, -0.2363 |
| total_amount_quote | -0.2496, -0.2496 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5755714253901677
- **Max CV**: 0.7234175758948191
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4708 | 0.022961564713937427 | 0.0825158425491216 | 0.0441483479104786 |
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
| recent_pnl | >= 0 | -2.1795934609179684 | FAIL |
| recent_trades | >= 5 | 1 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.05 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.3959765715253656 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.05 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.1795934609179684, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.1796% < 0; recent trades 1 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103802 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.1796% < 0; recent trades 1 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103802
- **Pre-release bars**: 95738
- **Dev bars**: 76591
- **Holdout bars**: 19147
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:00:45.733074+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 32
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
