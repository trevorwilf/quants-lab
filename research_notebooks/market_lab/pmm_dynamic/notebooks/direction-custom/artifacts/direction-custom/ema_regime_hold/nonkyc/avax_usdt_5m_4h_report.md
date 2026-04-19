# PMM Dynamic Optimization Report: nonkyc_AVAX-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:26:17 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:26:17.493827+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 421 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AVAX-USDT
- **interval**: 5m+4h
- **n_candles**: 213474
- **dataset_hash**: 8e1a9206cf3e4d1d0f93ac4f79d1786782947fac4286fa03448b26039a919d4c
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 906.7518679745236
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 5511 |
| min_volume_quantile | 0.37471522240883304 |
| regime_adx_length | 16 |
| regime_adx_threshold | 12.543346351287811 |
| regime_ema_fast | 71 |
| regime_ema_slow | 128 |
| stop_loss | 0.06061137037601309 |
| take_profit | 0.09032878755519558 |
| take_profit_order_type | MARKET |
| time_limit | 245766 |
| total_amount_quote | 906.7518679745236 |
| trailing_stop_activation | 0.004061077513583707 |
| trailing_stop_delta | 0.017023513362434926 |
| volume_filter_window | 543 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 906.7518679745236 |
| Selected | 906.7518679745236 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.4486
- **Net PnL (quote)**: -13.1356
- **Sharpe Ratio**: -0.7099
- **Max Drawdown %**: 1.7924
- **Profit Factor**: 0.15879387723534616
- **Trade Count**: 74
- **Total Fees (quote)**: 3.8482
- **Maker Fees**: 1.3658
- **Taker Fees**: 2.4824
- **Fee Drag %**: 0.4244

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0307
- **PnL Component**: -0.0146
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0134
- **Fee Drag Component**: -0.0021
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2175**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -4.43 | -9.38 | 5.14 | 91 | -0.1561 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | -3.32 | -6.40 | 4.34 | 75 | -0.1686 | n/a |
| 5 | -0.16 | -0.48 | 1.35 | 73 | -0.1836 | n/a |
| 6 | -2.43 | -4.10 | 3.48 | 97 | -0.2760 | n/a |
| 7 | -6.40 | -11.60 | 6.45 | 56 | -0.2405 | n/a |
| 8 | -1.44 | -1.87 | 2.21 | 66 | -0.1058 | n/a |
| 9 | -4.15 | -5.72 | 4.43 | 143 | -0.0912 | n/a |
| 10 | -1.86 | -2.62 | 3.00 | 219 | -0.1311 | n/a |
| 11 | -1.50 | -3.03 | 1.76 | 24 | -0.2680 | n/a |
| 12 | -1.10 | -1.34 | 3.15 | 136 | -0.0431 | n/a |
| 13 | -1.57 | -2.30 | 3.26 | 12 | -0.2204 | n/a |
| 14 | -2.46 | -2.05 | 5.32 | 96 | -0.0785 | n/a |
| 15 | -5.07 | -6.50 | 5.07 | 18 | -0.3168 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 22 | -1.55 | -2.73 | 2.04 | 19 | -0.1926 | n/a |
| 23 | -3.03 | -2.62 | 3.25 | 88 | -0.0654 | n/a |
| 24 | -1.70 | -1.39 | 3.96 | 187 | -0.0607 | n/a |
| 25 | -1.28 | -1.59 | 2.63 | 95 | -0.0368 | n/a |
| 26 | -1.14 | -3.60 | 1.51 | 177 | -0.0365 | n/a |
| 27 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 28 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 29 | -1.04 | -3.09 | 1.78 | 13 | -0.1775 | n/a |
| 30 | -3.46 | -6.41 | 4.07 | 23 | -0.1847 | n/a |
| 31 | -3.33 | -7.20 | 3.36 | 5 | -0.2507 | n/a |
| 32 | -3.22 | -8.43 | 3.74 | 18 | -0.2320 | n/a |
| 33 | -1.11 | -2.63 | 2.83 | 2 | -1000.0000 | n/a |
| 34 | -1.02 | -3.44 | 1.65 | 28 | -0.1834 | n/a |
| 35 | -1.81 | -5.15 | 2.35 | 8 | -0.2087 | n/a |
| 36 | -1.41 | -3.67 | 1.59 | 48 | -0.1157 | n/a |
| 37 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 38 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 39 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 40 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 41 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 42 | -1.08 | -8.68 | 1.08 | 5 | -0.5252 | n/a |
| 43 | -1.58 | -5.41 | 2.10 | 33 | -0.2609 | n/a |
| 44 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 45 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 46 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 47 | -1.59 | -3.72 | 2.18 | 28 | -0.1923 | n/a |
| 48 | -1.29 | -8.23 | 1.29 | 9 | -0.3854 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.66 | -0.81 | 1.86 | -0.0436 |
| fees_2x | -1.87 | -0.91 | 1.92 | -0.0555 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.92 | -1.15 | 4.09 | -0.0774 |
| very_low_liquidity | -2.41 | -1.24 | 2.49 | -0.0774 |
| high_slippage | -1.52 | -0.74 | 1.82 | -0.0336 |
| extreme_slippage | -1.65 | -0.81 | 1.86 | -0.0426 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.51 | -0.73 | 1.79 | -0.0333 |
| spread_widen_25bps | -1.59 | -0.77 | 1.80 | -0.0400 |
| thin_book | -1.22 | -1.02 | 1.49 | -0.1332 |
| very_thin_book | -1.08 | -0.99 | 1.12 | -0.0206 |
| entry_spread_stress | -1.53 | -0.75 | 1.80 | -0.0348 |
| combined_market_deterioration | -3.86 | -1.18 | 3.91 | -0.0967 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 41082
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0129)
- **Best holdout score**: -0.3413 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0154 | -0.5251 | -1.08 | 1.08 | 5 |
| 1 | -0.1364 | -0.3994 | -1.53 | 1.90 | 9 |
| 2 | -0.1612 | -0.4806 | -2.05 | 2.05 | 9 |
| 3 | -0.1673 | -0.3413 | -2.30 | 2.35 | 10 |
| 4 | -0.1676 | -0.5433 | -3.01 | 3.05 | 7 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 213474
- **Expected rows**: 214446
- **Missing rows**: 972
- **Forward-fill count**: 34125
- **Forward-fill fraction**: 0.15985553275808764
- **Longest gap (seconds)**: 17400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2775 <= 0; recent PnL -1.3983% < 0
- **Objective score**: -0.2775297838336015
- **PnL %**: -1.398296949185561
- **Trade count**: 45

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1619 <= 0; recent PnL -1.8450% < 0
- **Objective score**: -0.1619373875224483
- **PnL %**: -1.844959218291458
- **Trade count**: 103

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2582 <= 0; recent PnL -1.8450% < 0
- **Objective score**: -0.25817003565897184
- **PnL %**: -1.844959218291458
- **Trade count**: 103

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2
- **Baseline score**: -0.030356491842755195
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0308, -0.0998 |
| regime_ema_slow | -0.0308, -0.0991 |
| regime_adx_length | -0.0304, -0.0304 |
| regime_adx_threshold | -0.0304, -0.0304 |
| volume_filter_window | -0.0304, -0.0304 |
| min_volume_quantile | -0.0304, -0.0304 |
| stop_loss | -0.0332, -0.0276 |
| take_profit | -0.0304, -0.0304 |
| cooldown_time | -0.0304, -0.1168 |
| total_amount_quote | -0.0381, -0.0967 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.554290352692614
- **Max CV**: 1.1920594054714273
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3410 | 0.031690643630492184 | 0.09075818312931185 | 0.06297389656163808 |
| take_profit | 0.5688 | 0.019335588969031967 | 0.08757167459907843 | 0.04154125164915032 |
| cooldown_time | 1.1921 | 847.0 | 40980.0 | 10075.8 |
| total_amount_quote | 0.1154 | 491.3093500811951 | 716.1176257880818 | 607.6884667130939 |

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
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.2775297838336015 | FAIL |
| recent_pnl | >= 0 | -1.398296949185561 | FAIL |
| recent_trades | >= 5 | 45 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.2 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.5251231406041463 |
| walkforward | PASS | 49 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.2 |
| recent_28d | FAIL | score=-0.2775297838336015, pnl=-1.398296949185561, trades=45, reason=recent objective score -0.2775 <= 0; recent PnL -1.3983% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.1619373875224483, pnl=-1.844959218291458, trades=103, reason=recent objective score -0.1619 <= 0; recent PnL -1.8450% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.25817003565897184, pnl=-1.844959218291458, trades=103, reason=recent objective score -0.2582 <= 0; recent PnL -1.8450% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.554290352692614 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 213474 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2775 <= 0; recent PnL -1.3983% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1619 <= 0; recent PnL -1.8450% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2582 <= 0; recent PnL -1.8450% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 213474
- **Pre-release bars**: 205410
- **Dev bars**: 164328
- **Holdout bars**: 41082
- **Recent 28d bars**: 8064
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:26:17.493827+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 421
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
