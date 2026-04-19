# PMM Dynamic Optimization Report: mexc_ETH-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:03:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:03:56.717572+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 75 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ETH-USDT
- **interval**: 5m+4h
- **n_candles**: 103830
- **dataset_hash**: 8179d2bce5ecb5edceb678f08a7ffe8640a862d1e34b3ffb3759e8206a8a0935
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 503.1070093180463
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 1405 |
| min_volume_quantile | 0.24440927695546374 |
| regime_adx_length | 12 |
| regime_adx_threshold | 14.65678199088072 |
| regime_ema_fast | 23 |
| regime_ema_slow | 52 |
| stop_loss | 0.06989339495436407 |
| take_profit | 0.03512417677930595 |
| take_profit_order_type | LIMIT |
| time_limit | 128178 |
| total_amount_quote | 503.1070093180463 |
| trailing_stop_activation | 0.04550958604735765 |
| trailing_stop_delta | 0.01845636300082202 |
| volume_filter_window | 399 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 503.1070093180463 |
| Selected | 503.1070093180463 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 49.9178
- **Net PnL (quote)**: 251.1400
- **Sharpe Ratio**: 1.8560
- **Max Drawdown %**: 22.5078
- **Profit Factor**: 1.280042886589068
- **Trade Count**: 140
- **Total Fees (quote)**: 28.2204
- **Maker Fees**: 20.0172
- **Taker Fees**: 8.2031
- **Fee Drag %**: 5.6092

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0146
- **PnL Component**: 0.4049
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1688
- **Fee Drag Component**: -0.0280
- **Inventory Component**: -0.2201
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.3676**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.23 | -7.45 | 1.46 | 5 | -0.5106 | n/a |
| 1 | -1.86 | -4.58 | 4.07 | 20 | -0.3185 | n/a |
| 2 | -1.12 | -6.92 | 1.45 | 3 | -1000.0000 | n/a |
| 3 | -1.43 | -10.77 | 1.43 | 2 | -1000.0000 | n/a |
| 4 | -1.52 | -5.38 | 3.27 | 24 | -0.3217 | n/a |
| 5 | -1.34 | -5.38 | 1.83 | 3 | -1000.0000 | n/a |
| 6 | -1.69 | -8.72 | 1.69 | 3 | -1000.0000 | n/a |
| 7 | -1.10 | -2.95 | 1.86 | 2 | -1000.0000 | n/a |
| 8 | -1.25 | -11.09 | 1.26 | 3 | -1000.0000 | n/a |
| 9 | -1.06 | -12.15 | 1.06 | 3 | -1000.0000 | n/a |
| 10 | -1.14 | -2.23 | 3.84 | 30 | -0.1972 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | -1.02 | -5.56 | 1.37 | 6 | -0.4136 | n/a |
| 13 | -1.28 | -2.65 | 3.20 | 20 | -0.3144 | n/a |
| 14 | -1.23 | -8.24 | 1.31 | 16 | -0.2753 | n/a |
| 15 | -1.21 | -12.01 | 1.21 | 8 | -0.5470 | n/a |
| 16 | -1.08 | -8.23 | 1.08 | 3 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | -1.03 | -4.25 | 1.83 | 9 | -0.3045 | n/a |
| 20 | -1.16 | -8.28 | 1.50 | 4 | -0.5266 | n/a |
| 21 | -1.26 | -11.26 | 1.32 | 6 | -0.4309 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 47.11 | 1.77 | 23.14 | -0.0526 |
| fees_2x | 44.31 | 1.67 | 23.78 | -0.0911 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 49.92 | 1.86 | 22.51 | -0.0146 |
| very_low_liquidity | 49.92 | 1.86 | 22.51 | -0.0146 |
| high_slippage | 45.84 | 1.73 | 23.55 | -0.0504 |
| extreme_slippage | 37.69 | 1.46 | 25.71 | -0.1252 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 45.08 | 1.69 | 21.51 | -0.0404 |
| spread_widen_25bps | 26.05 | 1.08 | 30.23 | -0.2466 |
| thin_book | 47.75 | 1.77 | 25.99 | -0.0533 |
| very_thin_book | 55.06 | 2.13 | 24.23 | 0.0115 |
| entry_spread_stress | 33.96 | 1.35 | 27.47 | -0.1648 |
| combined_market_deterioration | 18.56 | 0.84 | 33.57 | -0.3471 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19211
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0030)
- **Trend**: ranging (efficiency: 0.0178)
- **Best holdout score**: -0.0402 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0073 | -1000.0000 | -1.24 | 1.46 | 3 |
| 1 | -0.1687 | -1000.0000 | -1.05 | 1.06 | 2 |
| 2 | -0.1752 | -0.0697 | -1.04 | 1.04 | 39 |
| 3 | -0.1798 | -0.0402 | -1.48 | 2.34 | 52 |
| 4 | -0.1834 | -0.0584 | -1.05 | 2.48 | 44 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103830
- **Expected rows**: 104122
- **Missing rows**: 292
- **Forward-fill count**: 360
- **Forward-fill fraction**: 0.0034672060098237503
- **Longest gap (seconds)**: 10800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.4380 <= 0; recent PnL -1.2109% < 0
- **Objective score**: -0.4379582416097719
- **PnL %**: -1.2109405162195785
- **Trade count**: 11

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3886 <= 0; recent PnL -1.0081% < 0
- **Objective score**: -0.3886118266249079
- **PnL %**: -1.0080933435677346
- **Trade count**: 8

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2582 <= 0; recent PnL -1.2584% < 0
- **Objective score**: -0.25816272756245623
- **PnL %**: -1.2583693559400442
- **Trade count**: 8

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.31167449567589955
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.3509, -0.4146 |
| regime_ema_slow | -0.2102, -0.3759 |
| regime_adx_length | -0.2851, -0.1619 |
| regime_adx_threshold | -0.4049, -0.2330 |
| volume_filter_window | -0.3067, -0.2878 |
| min_volume_quantile | -0.2909, -0.3042 |
| stop_loss | -0.2759, -0.3219 |
| take_profit | -0.2776, -0.4216 |
| cooldown_time | -0.3105, -0.3117 |
| total_amount_quote | -0.3118, -0.3117 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.37244241268621553
- **Max CV**: 0.5550771597627128
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4048 | 0.027678065228551475 | 0.09564885882251682 | 0.05581903714378137 |
| take_profit | 0.3638 | 0.019048707787474185 | 0.05479062392929983 | 0.037597211703076575 |
| cooldown_time | 0.5551 | 948.0 | 8216.0 | 4388.8 |
| total_amount_quote | 0.1662 | 480.8708682190812 | 885.4347290259966 | 714.8686520374565 |

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
| recent_objective | > 0 | -0.4379582416097719 | FAIL |
| recent_pnl | >= 0 | -1.2109405162195785 | FAIL |
| recent_trades | >= 5 | 11 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.4379582416097719, pnl=-1.2109405162195785, trades=11, reason=recent objective score -0.4380 <= 0; recent PnL -1.2109% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3886118266249079, pnl=-1.0080933435677346, trades=8, reason=recent objective score -0.3886 <= 0; recent PnL -1.0081% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.25816272756245623, pnl=-1.2583693559400442, trades=8, reason=recent objective score -0.2582 <= 0; recent PnL -1.2584% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.37244241268621553 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103830 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.4380 <= 0; recent PnL -1.2109% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3886 <= 0; recent PnL -1.0081% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2582 <= 0; recent PnL -1.2584% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103830
- **Pre-release bars**: 96057
- **Dev bars**: 76846
- **Holdout bars**: 19211
- **Recent 28d bars**: 7773
- **Recent window start**: 1774107900

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:03:56.717572+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 75
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
