# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 13:04:06 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T13:04:06.937847+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 465 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51899
- **dataset_hash**: 604068b218abf88d81768336c87510e01ff3086ff0be51d029c5caf0dd2bc637
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 903.117022622275
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 25 |
| bb_length | 103 |
| bb_std | 1.0758320761248712 |
| bbp_entry_threshold | 0.12693633559861353 |
| cooldown_time | 46549 |
| max_atr_pct_for_entry | 0.013665893573525892 |
| min_volume_quantile | 0.013890078350597294 |
| rsi_entry_threshold | 39.835726451428584 |
| rsi_length | 17 |
| stop_loss | 0.02833097030056942 |
| take_profit | 0.051260826788258 |
| take_profit_order_type | MARKET |
| time_limit | 17683 |
| total_amount_quote | 903.117022622275 |
| trailing_stop_activation | 0.0029141294193540308 |
| trailing_stop_delta | 0.007692368326967838 |
| trend_ema_length | 290 |
| use_trend_filter | True |
| volume_filter_window | 537 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 903.117022622275 |
| Selected | 903.117022622275 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0255
- **Net PnL (quote)**: -9.2615
- **Sharpe Ratio**: -0.6398
- **Max Drawdown %**: 1.9857
- **Profit Factor**: 0.24448775310029694
- **Trade Count**: 31
- **Total Fees (quote)**: 45.2179
- **Maker Fees**: 16.2517
- **Taker Fees**: 28.9663
- **Fee Drag %**: 5.0069

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1330
- **PnL Component**: -0.0103
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0149
- **Fee Drag Component**: -0.0250
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0760
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2031**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.66 | -3.31 | 0.98 | 12 | -0.2986 | n/a |
| 1 | -0.47 | -2.09 | 0.65 | 7 | -0.1882 | n/a |
| 2 | -1.44 | -6.13 | 1.44 | 2 | -1000.0000 | n/a |
| 3 | -0.11 | -2.35 | 0.21 | 2 | -1000.0000 | n/a |
| 4 | 0.05 | 0.42 | 0.35 | 7 | -0.1816 | n/a |
| 5 | -0.18 | -0.46 | 1.81 | 6 | -0.1980 | n/a |
| 6 | -0.56 | -2.03 | 1.52 | 11 | -0.2082 | n/a |
| 7 | -0.02 | -0.09 | 0.76 | 10 | -0.1751 | n/a |
| 8 | -1.51 | -4.47 | 1.58 | 10 | -0.2043 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.11 | -1.45 | 1.27 | -0.5215 |
| fees_2x | -1.11 | -1.52 | 1.11 | -0.6145 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.03 | -0.64 | 1.99 | -0.1256 |
| very_low_liquidity | -1.10 | -0.68 | 1.92 | -0.0982 |
| high_slippage | -1.15 | -1.04 | 2.02 | -0.2656 |
| extreme_slippage | -1.05 | -1.37 | 1.22 | -0.4621 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.18 | -0.88 | 2.00 | -0.1750 |
| spread_widen_25bps | -1.13 | -1.28 | 1.14 | -0.2735 |
| thin_book | -1.11 | -0.83 | 1.55 | -0.1573 |
| very_thin_book | -1.18 | -0.98 | 1.18 | -0.1946 |
| entry_spread_stress | -1.11 | -1.13 | 1.75 | -0.1996 |
| combined_market_deterioration | -1.29 | -2.00 | 1.39 | -0.4228 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0058)
- **Best holdout score**: -0.1227 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0665 | -0.1504 | -0.71 | 1.59 | 23 |
| 1 | -0.1751 | -0.1847 | -1.03 | 1.06 | 14 |
| 2 | -0.1758 | -0.1227 | -0.55 | 2.30 | 32 |
| 3 | -0.1767 | -1000.0000 | -2.08 | 2.08 | 3 |
| 4 | -0.1767 | -0.1532 | 1.26 | 1.59 | 18 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51899
- **Expected rows**: 51899
- **Missing rows**: 0
- **Forward-fill count**: 262
- **Forward-fill fraction**: 0.005048266825950404
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2065 <= 0; recent PnL -1.7225% < 0
- **Objective score**: -0.20648126104389214
- **PnL %**: -1.722480415689126
- **Trade count**: 15

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3013 <= 0; recent PnL -1.0091% < 0
- **Objective score**: -0.3013415059413302
- **PnL %**: -1.0091490428500058
- **Trade count**: 6

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.4740% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.4740280609085437
- **Trade count**: 2

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.11945404302311033
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1013, -0.1515 |
| bb_std | -0.1195, -0.1505 |
| bbp_entry_threshold | -0.1195, -0.1195 |
| rsi_length | -0.2952, -0.2733 |
| rsi_entry_threshold | -0.1793, -0.1590 |
| trend_ema_length | -1000.0000, -0.1255 |
| max_atr_pct_for_entry | -0.1195, -0.1195 |
| volume_filter_window | -0.1195, -0.1195 |
| min_volume_quantile | -0.1195, -0.1195 |
| stop_loss | -0.1195, -0.1194 |
| take_profit | -0.1195, -0.1195 |
| cooldown_time | -0.1195, -0.1254 |
| total_amount_quote | -0.1194, -0.1195 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4869087711066775
- **Max CV**: 0.6876415535870581
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4260 | 0.015025979020385565 | 0.05799941732236184 | 0.03375479090381083 |
| take_profit | 0.6876 | 0.006951616958371377 | 0.04793555989689641 | 0.01804151562917503 |
| cooldown_time | 0.3704 | 23231.0 | 76442.0 | 47649.3 |
| total_amount_quote | 0.4636 | 57.93330437699889 | 751.6517709101795 | 411.87701441322207 |

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
| recent_objective | > 0 | -0.20648126104389214 | FAIL |
| recent_pnl | >= 0 | -1.722480415689126 | FAIL |
| recent_trades | >= 5 | 15 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1503987010060242 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.20648126104389214, pnl=-1.722480415689126, trades=15, reason=recent objective score -0.2065 <= 0; recent PnL -1.7225% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.3013415059413302, pnl=-1.0091490428500058, trades=6, reason=recent objective score -0.3013 <= 0; recent PnL -1.0091% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-2.4740280609085437, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.4740% < 0; recent trades 2 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4869087711066775 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51899 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2065 <= 0; recent PnL -1.7225% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3013 <= 0; recent PnL -1.0091% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.4740% < 0; recent trades 2 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51899
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8065
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T13:04:06.937847+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 465
- **validation_status**: validated_fail
