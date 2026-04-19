# PMM Dynamic Optimization Report: mexc_APT-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 16:51:48 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T16:51:48.956012+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 50 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: APT-USDT
- **interval**: 5m+4h
- **n_candles**: 103807
- **dataset_hash**: 32dcea2d086536d2f380b1b8d64b590ba9d9556a8fa7fb29b6f955280a0ce6cf
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 714.0697928100619
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 33982 |
| min_volume_quantile | 0.0257958125349822 |
| regime_adx_length | 24 |
| regime_adx_threshold | 26.876227251191615 |
| regime_ema_fast | 82 |
| regime_ema_slow | 197 |
| stop_loss | 0.027772761162496735 |
| take_profit | 0.08906076836418185 |
| take_profit_order_type | LIMIT |
| time_limit | 189873 |
| total_amount_quote | 714.0697928100619 |
| trailing_stop_activation | 0.04524073206546157 |
| trailing_stop_delta | 0.017485290623470328 |
| volume_filter_window | 574 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 714.0697928100619 |
| Selected | 714.0697928100619 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.6866
- **Net PnL (quote)**: 26.3249
- **Sharpe Ratio**: 0.6550
- **Max Drawdown %**: 5.0739
- **Profit Factor**: 1.6432495031275565
- **Trade Count**: 5
- **Total Fees (quote)**: 1.1480
- **Maker Fees**: 0.5713
- **Taker Fees**: 0.5768
- **Fee Drag %**: 0.1608

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1828
- **PnL Component**: 0.0362
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0381
- **Fee Drag Component**: -0.0008
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
| 9 | 5.53 | 4.27 | 5.07 | 5 | -0.4011 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.61 | 0.64 | 5.10 | -0.1842 |
| fees_2x | 3.52 | 0.63 | 5.13 | -0.1857 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 3.69 | 0.66 | 5.07 | -0.1828 |
| very_low_liquidity | 3.69 | 0.66 | 5.07 | -0.1668 |
| high_slippage | 3.48 | 0.62 | 5.14 | -0.1852 |
| extreme_slippage | 3.08 | 0.55 | 5.33 | -0.1906 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 3.58 | 0.64 | 5.13 | -0.1844 |
| spread_widen_25bps | 3.42 | 0.61 | 5.21 | -0.1867 |
| thin_book | -0.28 | -0.00 | 6.16 | -0.2259 |
| very_thin_book | -2.87 | -2.01 | 2.87 | -1000.0000 |
| entry_spread_stress | 3.53 | 0.63 | 5.15 | -0.1852 |
| combined_market_deterioration | -0.68 | -0.06 | 6.34 | -0.2316 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19192
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0039)
- **Trend**: ranging (efficiency: 0.0210)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0914 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103807
- **Expected rows**: 104028
- **Missing rows**: 221
- **Forward-fill count**: 59
- **Forward-fill fraction**: 0.0005683624418391823
- **Longest gap (seconds)**: 25800

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

- **Sensitivity penalty**: 0.15
- **Baseline score**: -0.18277514648888354
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.1828, -0.1828 |
| regime_ema_slow | -1000.0000, -1000.0000 |
| regime_adx_length | -0.1828, -0.1828 |
| regime_adx_threshold | -1000.0000, -0.1828 |
| volume_filter_window | -0.1828, -0.1828 |
| min_volume_quantile | -0.1828, -0.1828 |
| stop_loss | -0.2052, -0.1754 |
| take_profit | -0.1828, -0.1828 |
| cooldown_time | -0.2118, -0.2609 |
| total_amount_quote | -0.1828, -0.1828 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5521242716009338
- **Max CV**: 0.7186684346676143
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4709 | 0.022961564713937427 | 0.0825158425491216 | 0.04654255919391697 |
| take_profit | 0.5884 | 0.01645477416780652 | 0.07948998901397729 | 0.03824200379425975 |
| cooldown_time | 0.7187 | 4806.0 | 83356.0 | 35705.5 |
| total_amount_quote | 0.4306 | 142.22499629651378 | 670.0304205910417 | 414.07806939947943 |

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
| sensitivity_penalty | < 0.50 | 0.15 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5521242716009338 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103807 |  |
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

- **Full bars**: 103807
- **Pre-release bars**: 95963
- **Dev bars**: 76771
- **Holdout bars**: 19192
- **Recent 28d bars**: 7844
- **Recent window start**: 1774079100

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T16:51:48.956012+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 50
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
