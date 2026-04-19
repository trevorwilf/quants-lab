# PMM Dynamic Optimization Report: mexc_HYPE-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:05:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:05:32.195923+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 33 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: HYPE-USDT
- **interval**: 5m+4h
- **n_candles**: 103808
- **dataset_hash**: e944df7ca384dea35f694d804817e03f8227e257d0b18dc58122a76e7c0bebbd
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 269.90069778301563
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 60935 |
| min_volume_quantile | 0.265429383000454 |
| regime_adx_length | 7 |
| regime_adx_threshold | 16.822971426928895 |
| regime_ema_fast | 88 |
| regime_ema_slow | 103 |
| stop_loss | 0.04615033717035634 |
| take_profit | 0.038090756017081374 |
| take_profit_order_type | MARKET |
| time_limit | 289704 |
| total_amount_quote | 269.90069778301563 |
| trailing_stop_activation | 0.0024650641927280725 |
| trailing_stop_delta | 0.0033485217626621783 |
| volume_filter_window | 323 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 269.90069778301563 |
| Selected | 269.90069778301563 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.1413
- **Net PnL (quote)**: 3.0804
- **Sharpe Ratio**: 0.2570
- **Max Drawdown %**: 4.4422
- **Profit Factor**: 1.2427372258167255
- **Trade Count**: 14
- **Total Fees (quote)**: 1.4044
- **Maker Fees**: 0.7017
- **Taker Fees**: 0.7026
- **Fee Drag %**: 0.5203

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1687
- **PnL Component**: 0.0113
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0333
- **Fee Drag Component**: -0.0026
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1440
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
| 10 | 5.84 | 6.00 | 3.57 | 13 | -0.1212 | n/a |
| 11 | 0.17 | 6.57 | 0.00 | 2 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 16 | 0.28 | 0.61 | 2.63 | 2 | -1000.0000 | n/a |
| 17 | -3.14 | -3.26 | 4.63 | 5 | -0.2481 | n/a |
| 18 | -1.88 | -2.02 | 4.34 | 12 | -0.4530 | n/a |
| 19 | 3.96 | 3.19 | 4.21 | 11 | -0.4018 | n/a |
| 20 | -2.55 | -2.89 | 3.31 | 7 | -0.4741 | n/a |
| 21 | -3.07 | -3.26 | 4.14 | 4 | -0.6678 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 0.88 | 0.21 | 4.47 | -0.1727 |
| fees_2x | 0.62 | 0.16 | 4.50 | -0.1768 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 1.14 | 0.26 | 4.44 | -0.1687 |
| very_low_liquidity | 1.14 | 0.26 | 4.44 | -0.1687 |
| high_slippage | 0.49 | 0.13 | 4.51 | -0.1756 |
| extreme_slippage | -0.81 | -0.13 | 4.66 | -0.1898 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 0.54 | 0.14 | 4.47 | -0.1748 |
| spread_widen_25bps | -0.36 | -0.03 | 4.51 | -0.1802 |
| thin_book | -4.53 | -1.79 | 4.69 | -1000.0000 |
| very_thin_book | -4.70 | -2.20 | 4.70 | -1000.0000 |
| entry_spread_stress | 0.24 | 0.08 | 4.48 | -0.1779 |
| combined_market_deterioration | -3.35 | -0.63 | 4.78 | -0.2325 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19206
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0049)
- **Trend**: ranging (efficiency: 0.0098)
- **Best holdout score**: -0.2212 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0843 | -0.2212 | 7.67 | 6.36 | 62 |
| 1 | -1000.0000 | -1000.0000 | -2.38 | 2.38 | 2 |
| 2 | -1000.0000 | -1000.0000 | -3.56 | 3.57 | 2 |
| 3 | -1000.0000 | -1000.0000 | -1.87 | 3.92 | 3 |
| 4 | -1000.0000 | -0.2228 | -1.71 | 2.79 | 4 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103808
- **Expected rows**: 104098
- **Missing rows**: 290
- **Forward-fill count**: 275
- **Forward-fill fraction**: 0.0026491214549938347
- **Longest gap (seconds)**: 26700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2219 <= 0; recent PnL -3.1031% < 0
- **Objective score**: -0.2218884555214743
- **PnL %**: -3.1030607930138605
- **Trade count**: 12

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4484 <= 0; recent PnL -2.4733% < 0
- **Objective score**: -0.44842673099162766
- **PnL %**: -2.473326395219115
- **Trade count**: 15

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4840 <= 0; recent PnL -3.1518% < 0
- **Objective score**: -0.4840307876641494
- **PnL %**: -3.1518009070416344
- **Trade count**: 9

## Sensitivity Analysis

- **Sensitivity penalty**: 0.7
- **Baseline score**: -0.062175470982329645
- **Sign flips**: 1
- **Collapse count**: 13
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -0.2598 |
| regime_ema_slow | -1000.0000, -0.0711 |
| regime_adx_length | -0.1990, -0.1636 |
| regime_adx_threshold | -0.2101, -0.1631 |
| volume_filter_window | -0.2079, -0.1099 |
| min_volume_quantile | -0.0623, -0.2079 |
| stop_loss | -0.0592, -0.2395 |
| take_profit | -0.0622, -0.0622 |
| cooldown_time | 0.0548, -0.2458 |
| total_amount_quote | -0.1083, -0.0622 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.2218884555214743 | FAIL |
| recent_pnl | >= 0 | -3.1030607930138605 | FAIL |
| recent_trades | >= 5 | 12 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.7 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2212293362497223 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.7 |
| recent_28d | FAIL | score=-0.2218884555214743, pnl=-3.1030607930138605, trades=12, reason=recent objective score -0.2219 <= 0; recent PnL -3.1031% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.44842673099162766, pnl=-2.473326395219115, trades=15, reason=recent objective score -0.4484 <= 0; recent PnL -2.4733% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.4840307876641494, pnl=-3.1518009070416344, trades=9, reason=recent objective score -0.4840 <= 0; recent PnL -3.1518% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103808 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2219 <= 0; recent PnL -3.1031% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4484 <= 0; recent PnL -2.4733% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4840 <= 0; recent PnL -3.1518% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103808
- **Pre-release bars**: 96033
- **Dev bars**: 76827
- **Holdout bars**: 19206
- **Recent 28d bars**: 7775
- **Recent window start**: 1774101000

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:05:32.195923+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 33
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
