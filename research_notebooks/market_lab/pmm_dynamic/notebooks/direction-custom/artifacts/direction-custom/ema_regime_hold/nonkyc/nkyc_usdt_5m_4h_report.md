# PMM Dynamic Optimization Report: nonkyc_NKYC-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:36:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:36:12.289313+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 131 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: NKYC-USDT
- **interval**: 5m+4h
- **n_candles**: 205974
- **dataset_hash**: a45186c52de9683d7c62b11bcd62984cf1f1e5ee408f6a6ce29dffa9ddbdae95
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 804.0025512558068
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 30120 |
| min_volume_quantile | 0.4258566104093621 |
| regime_adx_length | 13 |
| regime_adx_threshold | 27.702507666985056 |
| regime_ema_fast | 28 |
| regime_ema_slow | 181 |
| stop_loss | 0.020488093633305497 |
| take_profit | 0.02236893558297699 |
| take_profit_order_type | MARKET |
| time_limit | 273937 |
| total_amount_quote | 804.0025512558068 |
| trailing_stop_activation | 0.007424710791857851 |
| trailing_stop_delta | 0.01771277602741827 |
| volume_filter_window | 123 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 804.0025512558068 |
| Selected | 804.0025512558068 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.4444
- **Net PnL (quote)**: -11.6130
- **Sharpe Ratio**: -0.4758
- **Max Drawdown %**: 2.3916
- **Profit Factor**: 0.4003174167724165
- **Trade Count**: 241
- **Total Fees (quote)**: 9.1920
- **Maker Fees**: 3.2833
- **Taker Fees**: 5.9086
- **Fee Drag %**: 1.1433

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0382
- **PnL Component**: -0.0145
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0179
- **Fee Drag Component**: -0.0057
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2862**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.05 | -4.91 | 1.29 | 76 | -0.3228 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | -1.38 | -4.28 | 1.96 | 112 | -0.2230 | n/a |
| 3 | -2.07 | -10.46 | 2.41 | 56 | -0.3701 | n/a |
| 4 | -2.34 | -4.99 | 4.27 | 67 | -0.0591 | n/a |
| 5 | -2.41 | -6.03 | 2.66 | 41 | -0.3995 | n/a |
| 6 | -2.80 | -7.80 | 3.18 | 112 | -0.1558 | n/a |
| 7 | -1.13 | -3.31 | 1.62 | 67 | -0.2475 | n/a |
| 8 | -1.87 | -5.80 | 2.01 | 2965 | -0.0758 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | -0.30 | -1.10 | 1.78 | 164 | -0.0601 | n/a |
| 11 | -2.27 | -10.20 | 2.57 | 97 | -0.0467 | n/a |
| 12 | -3.09 | -11.71 | 3.64 | 126 | -0.2195 | n/a |
| 13 | -2.40 | -7.32 | 2.68 | 47 | -0.3287 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 17 | -1.40 | -2.31 | 2.75 | 191 | -0.2938 | n/a |
| 18 | 0.36 | 0.99 | 1.46 | 30 | -0.0907 | n/a |
| 19 | -2.35 | -7.81 | 2.86 | 30 | -0.1369 | n/a |
| 20 | -1.02 | -2.32 | 1.67 | 88 | -0.2781 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 22 | -1.92 | -6.68 | 1.93 | 19 | -0.4635 | n/a |
| 23 | -2.84 | -4.12 | 4.82 | 132 | -0.3263 | n/a |
| 24 | -2.36 | -6.90 | 2.71 | 31 | -0.1298 | n/a |
| 25 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 26 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 27 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 28 | -2.46 | -6.81 | 3.05 | 41 | -0.0890 | n/a |
| 29 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 30 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 31 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 32 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 33 | -0.07 | -2.83 | 0.12 | 4 | -0.4865 | n/a |
| 34 | -1.46 | -6.41 | 1.52 | 16 | -0.4643 | n/a |
| 35 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 36 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 37 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 38 | -0.83 | -1.99 | 2.67 | 30 | -0.1120 | n/a |
| 39 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 40 | -2.10 | -3.99 | 4.77 | 103 | -0.3144 | n/a |
| 41 | -2.27 | -8.79 | 2.74 | 31 | -0.2037 | n/a |
| 42 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 43 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 44 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 45 | -2.17 | -6.65 | 2.40 | 27 | -0.3092 | n/a |
| 46 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 47 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.02 | -0.67 | 2.56 | -0.0482 |
| fees_2x | -2.59 | -0.85 | 2.99 | -0.0666 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.98 | -0.69 | 2.49 | -0.0433 |
| very_low_liquidity | -2.68 | -1.47 | 3.13 | -0.1176 |
| high_slippage | -1.63 | -0.54 | 2.44 | -0.0405 |
| extreme_slippage | -1.99 | -0.66 | 2.56 | -0.0451 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.17 | -0.71 | 2.64 | -0.0450 |
| spread_widen_25bps | -2.25 | -0.73 | 2.65 | -0.0459 |
| thin_book | -1.80 | -0.80 | 2.43 | -0.0407 |
| very_thin_book | -3.31 | -2.54 | 3.40 | -0.3471 |
| entry_spread_stress | -2.20 | -0.72 | 2.64 | -0.0453 |
| combined_market_deterioration | -2.37 | -0.91 | 2.78 | -0.0682 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 39586
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0102)
- **Best holdout score**: -0.0455 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0191 | -0.0455 | -1.04 | 2.94 | 117 |
| 1 | -0.1436 | -0.2564 | -1.74 | 2.75 | 46 |
| 2 | -0.1576 | -0.1869 | -2.20 | 2.42 | 15 |
| 3 | -0.1689 | -0.1612 | -1.96 | 2.69 | 21 |
| 4 | -0.1723 | -0.2601 | -1.37 | 2.21 | 14 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 205974
- **Expected rows**: 210626
- **Missing rows**: 4652
- **Forward-fill count**: 852
- **Forward-fill fraction**: 0.004136444405604591
- **Longest gap (seconds)**: 23100

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

- **Sensitivity penalty**: 0.05
- **Baseline score**: -0.037498385672654296
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0375, -0.0375 |
| regime_ema_slow | -0.0375, -0.0375 |
| regime_adx_length | -0.4330, -0.0375 |
| regime_adx_threshold | -0.0425, -0.0402 |
| volume_filter_window | -0.0375, -0.0375 |
| min_volume_quantile | -0.0413, -0.0375 |
| stop_loss | -0.0411, -0.0339 |
| take_profit | -0.0375, -0.0375 |
| cooldown_time | -0.0434, -0.0426 |
| total_amount_quote | -0.0373, -0.0378 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3998592617174166
- **Max CV**: 0.5382787648166374
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4108 | 0.020314011704201437 | 0.05781005475560654 | 0.02831270397197262 |
| take_profit | 0.4400 | 0.02728318105203242 | 0.09880164878400093 | 0.06504897370139548 |
| cooldown_time | 0.5383 | 5363.0 | 37081.0 | 17604.9 |
| total_amount_quote | 0.2104 | 535.7374078874541 | 999.7200555615129 | 811.597081833378 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.05 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.04545502295948706 |
| walkforward | PASS | 48 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.05 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3998592617174166 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 205974 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 205974
- **Pre-release bars**: 197930
- **Dev bars**: 158344
- **Holdout bars**: 39586
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:36:12.289313+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 131
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
