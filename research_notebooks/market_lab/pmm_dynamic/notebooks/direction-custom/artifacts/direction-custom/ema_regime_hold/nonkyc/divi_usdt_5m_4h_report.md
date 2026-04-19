# PMM Dynamic Optimization Report: nonkyc_DIVI-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:28:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:28:05.061481+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 261 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: DIVI-USDT
- **interval**: 5m+4h
- **n_candles**: 47473
- **dataset_hash**: e8520341b00329fd15a20b75ac5a1ea8608b47afc8b72e4a3e9d3df75750d50c
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 227.33767561524797
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 14494 |
| min_volume_quantile | 0.4481495333754004 |
| regime_adx_length | 18 |
| regime_adx_threshold | 19.087799121722067 |
| regime_ema_fast | 23 |
| regime_ema_slow | 184 |
| stop_loss | 0.08570580870387569 |
| take_profit | 0.07093948143144636 |
| take_profit_order_type | LIMIT |
| time_limit | 107189 |
| total_amount_quote | 227.33767561524797 |
| trailing_stop_activation | 0.01575027274268869 |
| trailing_stop_delta | 0.02026508146764351 |
| volume_filter_window | 169 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 227.33767561524797 |
| Selected | 227.33767561524797 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1548
- **Net PnL (quote)**: -2.6253
- **Sharpe Ratio**: -0.2394
- **Max Drawdown %**: 7.5536
- **Profit Factor**: 0.41419966040066364
- **Trade Count**: 52
- **Total Fees (quote)**: 1.3956
- **Maker Fees**: 0.4892
- **Taker Fees**: 0.9064
- **Fee Drag %**: 0.6139

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0717
- **PnL Component**: -0.0116
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0567
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.3771**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | -5.34 | -4.96 | 5.89 | 48 | -0.2075 | n/a |
| 2 | -4.63 | -5.09 | 4.63 | 44 | -0.2244 | n/a |
| 3 | -4.36 | -7.52 | 5.79 | 17 | -0.4987 | n/a |
| 4 | -1.40 | -1.72 | 1.60 | 38 | -0.3917 | n/a |
| 5 | 0.03 | 0.91 | 0.05 | 1 | -1000.0000 | n/a |
| 6 | 3.54 | 2.65 | 2.78 | 51 | 0.0101 | n/a |
| 7 | -8.91 | -21.09 | 8.97 | 34 | -0.4834 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.46 | -0.32 | 7.62 | -0.0768 |
| fees_2x | -1.77 | -0.40 | 7.68 | -0.0820 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -7.92 | -1.10 | 8.83 | -0.1974 |
| very_low_liquidity | -1.29 | -0.08 | 7.56 | -0.0769 |
| high_slippage | -1.25 | -0.27 | 7.56 | -0.0727 |
| extreme_slippage | -1.45 | -0.32 | 7.56 | -0.0748 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.26 | -0.27 | 7.61 | -0.0731 |
| spread_widen_25bps | -1.41 | -0.30 | 7.69 | -0.0752 |
| thin_book | -5.53 | -0.89 | 7.60 | -0.1189 |
| very_thin_book | -4.94 | -0.90 | 7.66 | -0.3741 |
| entry_spread_stress | -1.31 | -0.28 | 7.63 | -0.0738 |
| combined_market_deterioration | -6.29 | -1.01 | 7.64 | -0.1296 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 7883
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0060)
- **Trend**: ranging (efficiency: 0.0023)
- **Best holdout score**: 0.0108 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: YES

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0358 | 0.0108 | 3.58 | 2.78 | 52 |
| 1 | -0.1548 | -0.1707 | -1.77 | 11.06 | 165 |
| 2 | -0.1641 | -0.0355 | -1.49 | 2.08 | 86 |
| 3 | -0.1674 | -0.3411 | -1.42 | 1.57 | 46 |
| 4 | -0.1689 | -0.4553 | -1.80 | 2.05 | 22 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 47473
- **Expected rows**: 47480
- **Missing rows**: 7
- **Forward-fill count**: 1442
- **Forward-fill fraction**: 0.030375160617614222
- **Longest gap (seconds)**: 900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.4832 <= 0; recent PnL -8.9149% < 0
- **Objective score**: -0.4831698437581661
- **PnL %**: -8.914890651257055
- **Trade count**: 34

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
- **Baseline score**: -0.07125913341102866
- **Sign flips**: 0
- **Collapse count**: 7
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0713, -0.0713 |
| regime_ema_slow | -0.1231, -0.0713 |
| regime_adx_length | -0.1184, -0.1305 |
| regime_adx_threshold | -0.1184, -0.1305 |
| volume_filter_window | -0.1206, -0.0713 |
| min_volume_quantile | -0.0713, -0.1206 |
| stop_loss | -0.0713, -0.0713 |
| take_profit | -0.0713, -0.0713 |
| cooldown_time | -0.0713, -0.0713 |
| total_amount_quote | -0.0850, -0.0928 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.44258416737398687
- **Max CV**: 0.7810338922696368
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1825 | 0.05508130053632071 | 0.09605538062017595 | 0.07849046096848271 |
| take_profit | 0.5487 | 0.011111325164275905 | 0.08861027217377573 | 0.05684299733035521 |
| cooldown_time | 0.7810 | 730.0 | 14662.0 | 5402.1 |
| total_amount_quote | 0.2581 | 369.5136325807174 | 840.0145165461589 | 670.715191065554 |

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
- holdout_passed: PASS
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
| recent_objective | > 0 | -0.4831698437581661 | FAIL |
| recent_pnl | >= 0 | -8.914890651257055 | FAIL |
| recent_trades | >= 5 | 34 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.35 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | PASS | score=0.0108 |
| walkforward | PASS | 8 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.35 |
| recent_28d | FAIL | score=-0.4831698437581661, pnl=-8.914890651257055, trades=34, reason=recent objective score -0.4832 <= 0; recent PnL -8.9149% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.44258416737398687 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 47473 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | PASS | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.4832 <= 0; recent PnL -8.9149% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 47473
- **Pre-release bars**: 39415
- **Dev bars**: 31532
- **Holdout bars**: 7883
- **Recent 28d bars**: 8058
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:28:05.061481+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 261
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
