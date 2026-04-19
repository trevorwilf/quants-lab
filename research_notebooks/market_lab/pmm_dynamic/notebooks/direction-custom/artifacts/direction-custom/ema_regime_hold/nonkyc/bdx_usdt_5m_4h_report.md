# PMM Dynamic Optimization Report: nonkyc_BDX-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:27:23 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:27:23.193597+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 177 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BDX-USDT
- **interval**: 5m+4h
- **n_candles**: 81407
- **dataset_hash**: ed673e08de2d8c9f92dea02320e74ed3ce5b66384d7ff2851a0d2bf4b8c9af25
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 599.7446693223776
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 84906 |
| min_volume_quantile | 0.30840478751694467 |
| regime_adx_length | 7 |
| regime_adx_threshold | 26.084715063273002 |
| regime_ema_fast | 19 |
| regime_ema_slow | 166 |
| stop_loss | 0.024427729762038268 |
| take_profit | 0.025225132272173212 |
| take_profit_order_type | LIMIT |
| time_limit | 35470 |
| total_amount_quote | 599.7446693223776 |
| trailing_stop_activation | 0.006617810932743259 |
| trailing_stop_delta | 0.011479086262090824 |
| volume_filter_window | 52 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 599.7446693223776 |
| Selected | 599.7446693223776 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0105
- **Net PnL (quote)**: -6.0606
- **Sharpe Ratio**: -1.2833
- **Max Drawdown %**: 1.3904
- **Profit Factor**: 0.10878316042272423
- **Trade Count**: 135
- **Total Fees (quote)**: 3.7320
- **Maker Fees**: 1.3377
- **Taker Fees**: 2.3943
- **Fee Drag %**: 0.6223

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0237
- **PnL Component**: -0.0102
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0104
- **Fee Drag Component**: -0.0031
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2813**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.25 | -4.46 | 1.59 | 70 | -0.2017 | n/a |
| 1 | -0.57 | -0.99 | 1.51 | 419 | -0.2789 | n/a |
| 2 | -1.52 | -4.34 | 2.05 | 110 | -0.3866 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -0.06 | -0.10 | 2.05 | 305 | -0.2036 | n/a |
| 6 | -1.36 | -5.36 | 1.79 | 133 | -0.4842 | n/a |
| 7 | -1.34 | -6.65 | 1.40 | 107 | -0.1948 | n/a |
| 8 | -2.70 | -5.38 | 2.93 | 364 | -0.2301 | n/a |
| 9 | -1.01 | -5.32 | 1.67 | 59 | -0.3058 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | -2.43 | -11.99 | 2.44 | 120 | -0.2000 | n/a |
| 15 | -1.57 | -5.14 | 1.89 | 128 | -0.4902 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.32 | -1.67 | 1.46 | -0.1063 |
| fees_2x | -1.63 | -2.03 | 1.67 | -0.1895 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.79 | -2.22 | 2.05 | -0.0518 |
| very_low_liquidity | -3.03 | -5.99 | 3.10 | -0.2711 |
| high_slippage | -1.11 | -1.41 | 1.41 | -0.0410 |
| extreme_slippage | -1.31 | -1.64 | 1.45 | -0.1050 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.12 | -1.42 | 1.43 | -0.0401 |
| spread_widen_25bps | -1.19 | -1.42 | 1.61 | -0.0644 |
| thin_book | -2.77 | -4.92 | 2.86 | -0.2366 |
| very_thin_book | -2.39 | -3.01 | 2.44 | -0.1614 |
| entry_spread_stress | -1.17 | -1.48 | 1.44 | -0.0492 |
| combined_market_deterioration | -2.29 | -2.82 | 2.33 | -0.1491 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 14668
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0017)
- **Trend**: ranging (efficiency: 0.0016)
- **Best holdout score**: -0.0340 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0119 | -0.1503 | -2.43 | 2.44 | 120 |
| 1 | -0.1862 | -0.0874 | -2.13 | 4.78 | 101 |
| 2 | -0.1968 | -0.1476 | -4.22 | 4.42 | 226 |
| 3 | -0.1968 | -0.1004 | -2.84 | 5.33 | 58 |
| 4 | -0.2147 | -0.0340 | -1.71 | 1.71 | 77 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 81407
- **Expected rows**: 81839
- **Missing rows**: 432
- **Forward-fill count**: 1918
- **Forward-fill fraction**: 0.02356062746446866
- **Longest gap (seconds)**: 3900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3257 <= 0; recent PnL -1.5678% < 0
- **Objective score**: -0.32570269130542967
- **PnL %**: -1.5677631898723283
- **Trade count**: 128

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
- **Baseline score**: -0.0738595050107727
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0739, -0.0739 |
| regime_ema_slow | -0.3427, -0.0437 |
| regime_adx_length | -0.0882, -0.0386 |
| regime_adx_threshold | -0.0650, -0.3022 |
| volume_filter_window | -0.0248, -0.0739 |
| min_volume_quantile | -0.0248, -0.0739 |
| stop_loss | -0.0643, -0.0695 |
| take_profit | -0.0739, -0.0739 |
| cooldown_time | -0.0700, -0.0969 |
| total_amount_quote | -0.0246, -0.0721 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.26812665029329213
- **Max CV**: 0.4697994625760721
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1841 | 0.02323820685732602 | 0.03795026351079311 | 0.027504603010520844 |
| take_profit | 0.4698 | 0.011648366137586161 | 0.044885798413549526 | 0.026350261713471802 |
| cooldown_time | 0.1981 | 39016.0 | 85868.0 | 74106.7 |
| total_amount_quote | 0.2206 | 416.0247467784735 | 971.3178195723822 | 696.2565720604323 |

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
| recent_objective | > 0 | -0.32570269130542967 | FAIL |
| recent_pnl | >= 0 | -1.5677631898723283 | FAIL |
| recent_trades | >= 5 | 128 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.1 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.15034361294883294 |
| walkforward | PASS | 17 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.1 |
| recent_28d | FAIL | score=-0.32570269130542967, pnl=-1.5677631898723283, trades=128, reason=recent objective score -0.3257 <= 0; recent PnL -1.5678% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.26812665029329213 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 81407 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3257 <= 0; recent PnL -1.5678% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 81407
- **Pre-release bars**: 73343
- **Dev bars**: 58675
- **Holdout bars**: 14668
- **Recent 28d bars**: 8064
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:27:23.193597+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 177
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
