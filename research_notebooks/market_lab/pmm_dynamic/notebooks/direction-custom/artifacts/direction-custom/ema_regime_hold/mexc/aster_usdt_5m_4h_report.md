# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 16:52:43 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T16:52:43.966652+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 67 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m+4h
- **n_candles**: 58918
- **dataset_hash**: 319a255974ddde9b6b62ff599c08cc5dd684c37568e0eb8e7d41e03fce8c5359
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 773.4204722581469
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 25916 |
| min_volume_quantile | 0.02450502763129408 |
| regime_adx_length | 19 |
| regime_adx_threshold | 20.357926033839043 |
| regime_ema_fast | 46 |
| regime_ema_slow | 175 |
| stop_loss | 0.07107197607004942 |
| take_profit | 0.025557875763764434 |
| take_profit_order_type | LIMIT |
| time_limit | 598771 |
| total_amount_quote | 773.4204722581469 |
| trailing_stop_activation | 0.002754384818074284 |
| trailing_stop_delta | 0.0125814184455143 |
| volume_filter_window | 494 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 773.4204722581469 |
| Selected | 773.4204722581469 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -5.4614
- **Net PnL (quote)**: -42.2396
- **Sharpe Ratio**: -2.1458
- **Max Drawdown %**: 7.1382
- **Profit Factor**: 0.24065105764718078
- **Trade Count**: 6
- **Total Fees (quote)**: 1.5387
- **Maker Fees**: 0.7734
- **Taker Fees**: 0.7653
- **Fee Drag %**: 0.1989

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2868
- **PnL Component**: -0.0562
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0535
- **Fee Drag Component**: -0.0010
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1760
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -3.95 | -5.67 | 6.72 | 6 | -0.2685 | n/a |
| 1 | 2.30 | 3.85 | 1.62 | 7 | -0.1631 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 1.90 | 7.53 | 0.71 | 5 | -0.1673 | n/a |
| 7 | 1.53 | 1.93 | 3.20 | 22 | -0.3702 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 2.80 | 6.22 | 0.95 | 21 | -0.0990 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -5.56 | -2.19 | 7.15 | -0.2885 |
| fees_2x | -5.66 | -2.23 | 7.17 | -0.2901 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -5.46 | -2.15 | 7.14 | -0.2868 |
| very_low_liquidity | -5.46 | -2.15 | 7.14 | -0.2868 |
| high_slippage | -5.71 | -2.26 | 7.20 | -0.2899 |
| extreme_slippage | -6.20 | -2.48 | 7.32 | -0.2960 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -5.80 | -2.09 | 7.10 | -0.2901 |
| spread_widen_25bps | -4.94 | -1.22 | 7.04 | -0.2767 |
| thin_book | 6.35 | 2.51 | 2.77 | -0.0793 |
| very_thin_book | -4.79 | -1.88 | 7.02 | -0.2750 |
| entry_spread_stress | -5.91 | -2.13 | 7.11 | -0.2913 |
| combined_market_deterioration | 5.36 | 1.31 | 5.62 | -0.1079 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 10229
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0029)
- **Trend**: ranging (efficiency: 0.0023)
- **Best holdout score**: -0.0205 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.1434 | -0.0205 | 4.33 | 3.20 | 42 |
| 1 | -1000.0000 | -1000.0000 | -2.38 | 3.08 | 2 |
| 2 | -1000.0000 | -0.4485 | -2.65 | 5.64 | 18 |
| 3 | -1000.0000 | -0.2076 | -1.01 | 4.17 | 9 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 58918
- **Expected rows**: 59212
- **Missing rows**: 294
- **Forward-fill count**: 77
- **Forward-fill fraction**: 0.0013069011168064088
- **Longest gap (seconds)**: 15900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

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

- **Sensitivity penalty**: 0.1
- **Baseline score**: -0.28676199923658724
- **Sign flips**: 1
- **Collapse count**: 1
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | 0.0734, -0.2794 |
| regime_ema_slow | -0.2931, -0.2775 |
| regime_adx_length | -0.2868, -0.2868 |
| regime_adx_threshold | -0.2868, -0.2868 |
| volume_filter_window | -0.2868, -0.2868 |
| min_volume_quantile | -0.2868, -0.2868 |
| stop_loss | -0.2995, -0.2740 |
| take_profit | -0.2868, -0.2868 |
| cooldown_time | -0.2808, -1000.0000 |
| total_amount_quote | -0.2868, -0.2868 |

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
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.1 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.02053750455814327 |
| walkforward | PASS | 11 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.1 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 58918 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 58918
- **Pre-release bars**: 51147
- **Dev bars**: 40918
- **Holdout bars**: 10229
- **Recent 28d bars**: 7771
- **Recent window start**: 1774109100

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T16:52:43.966652+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 67
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
