# PMM Dynamic Optimization Report: nonkyc_SAL-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:22:35 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:22:35.588395+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8533 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: SAL-USDT
- **interval**: 5m
- **n_candles**: 51875
- **dataset_hash**: f4457fac8ca45ca99a19a18f8187b870ce0fce4ee7b9cd28481c6d4b2a7ceb8a
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 916.1696907564419
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 189 |
| bb_std | 2.1951157408231525 |
| bbp_entry_threshold | 0.09308537298305779 |
| cooldown_time | 22688 |
| max_atr_pct_for_entry | 0.007225841573899188 |
| min_volume_quantile | 0.1538102522751233 |
| rsi_entry_threshold | 35.83568325040317 |
| rsi_length | 27 |
| stop_loss | 0.06658927938408793 |
| take_profit | 0.04833157199698307 |
| take_profit_order_type | LIMIT |
| time_limit | 327327 |
| total_amount_quote | 916.1696907564419 |
| trailing_stop_activation | 0.020953400245191572 |
| trailing_stop_delta | 0.0006350736518626571 |
| trend_ema_length | 217 |
| use_trend_filter | False |
| volume_filter_window | 427 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 916.1696907564419 |
| Selected | 916.1696907564419 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 61.3744
- **Net PnL (quote)**: 562.2940
- **Sharpe Ratio**: 5.1820
- **Max Drawdown %**: 5.4063
- **Profit Factor**: inf
- **Trade Count**: 718
- **Total Fees (quote)**: 36.3438
- **Maker Fees**: 12.4556
- **Taker Fees**: 23.8882
- **Fee Drag %**: 3.9669

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.4144
- **PnL Component**: 0.4786
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0405
- **Fee Drag Component**: -0.0198
- **Inventory Component**: -0.0031
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0946**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 4.78 | 3.12 | 3.12 | 113 | -0.0426 | n/a |
| 1 | 7.44 | 6.17 | 2.01 | 91 | 0.0538 | n/a |
| 2 | 8.68 | 6.98 | 0.81 | 83 | 0.0656 | n/a |
| 3 | 1.07 | 6.71 | 0.11 | 11 | -0.1466 | n/a |
| 4 | 9.60 | 5.41 | 3.55 | 135 | 0.0610 | n/a |
| 5 | 7.92 | 7.12 | 2.02 | 124 | 0.0546 | n/a |
| 6 | -7.00 | -8.85 | 7.11 | 42 | -0.4513 | n/a |
| 7 | -4.85 | -8.76 | 5.45 | 51 | -0.3502 | n/a |
| 8 | -3.03 | -2.64 | 4.44 | 113 | -0.1517 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 59.39 | 5.06 | 5.43 | 0.3919 |
| fees_2x | 57.41 | 4.94 | 5.46 | 0.3693 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 33.30 | 3.59 | 5.49 | 0.2186 |
| very_low_liquidity | 17.30 | 2.43 | 5.95 | 0.0889 |
| high_slippage | 60.72 | 5.15 | 5.41 | 0.4103 |
| extreme_slippage | 59.42 | 5.08 | 5.43 | 0.4021 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 60.75 | 5.13 | 5.42 | 0.4105 |
| spread_widen_25bps | 59.87 | 5.05 | 5.43 | 0.4045 |
| thin_book | 9.13 | 1.55 | 5.20 | 0.0377 |
| very_thin_book | -3.05 | -2.77 | 4.80 | -0.2066 |
| entry_spread_stress | 60.49 | 5.11 | 5.42 | 0.4085 |
| combined_market_deterioration | 29.71 | 3.23 | 5.57 | 0.1833 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8776
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0081)
- **Trend**: ranging (efficiency: 0.0053)
- **Best holdout score**: 0.0198 (rank #3)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.7928 | -0.1055 | -4.86 | 6.96 | 99 |
| 1 | 0.0584 | -0.0878 | 5.85 | 0.40 | 15 |
| 2 | 0.0577 | -0.0903 | 5.58 | 0.40 | 15 |
| 3 | 0.0574 | 0.0198 | 8.65 | 2.09 | 39 |
| 4 | 0.0571 | 0.0176 | 8.41 | 2.09 | 39 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51875
- **Expected rows**: 51949
- **Missing rows**: 74
- **Forward-fill count**: 1057
- **Forward-fill fraction**: 0.020375903614457833
- **Longest gap (seconds)**: 11400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1495 <= 0; recent PnL -3.0285% < 0
- **Objective score**: -0.1494655590365193
- **PnL %**: -3.0285230374409053
- **Trade count**: 113

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0089 <= 0
- **Objective score**: -0.008911002665601162
- **PnL %**: 2.2441967230858726
- **Trade count**: 56

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0156 <= 0
- **Objective score**: -0.015560199978175704
- **PnL %**: 2.2441967230858726
- **Trade count**: 56

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: 0.21380817400091906
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.1430, 0.1595 |
| bb_std | 0.1224, 0.0898 |
| bbp_entry_threshold | 0.2163, 0.1624 |
| rsi_length | 0.1347, 0.2173 |
| rsi_entry_threshold | 0.5089, 0.2342 |
| trend_ema_length | 0.2138, 0.2138 |
| max_atr_pct_for_entry | 0.2154, 0.2646 |
| volume_filter_window | 0.2138, 0.2138 |
| min_volume_quantile | 0.2238, 0.2138 |
| stop_loss | 0.1854, 0.1913 |
| take_profit | 0.2138, 0.2138 |
| cooldown_time | 0.2138, 0.2532 |
| total_amount_quote | 0.1891, 0.2343 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.167975402520258
- **Max CV**: 0.2412847458972165
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2413 | 0.033154400643111676 | 0.06600485813735243 | 0.046830675128313036 |
| take_profit | 0.1505 | 0.03580772158883516 | 0.058981649316634376 | 0.0498828186069456 |
| cooldown_time | 0.2142 | 38469.0 | 81074.0 | 62014.8 |
| total_amount_quote | 0.0659 | 791.511155275824 | 937.0197406990522 | 875.5898716028198 |

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
- walkforward_positive_majority: PASS
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
| recent_objective | > 0 | -0.1494655590365193 | FAIL |
| recent_pnl | >= 0 | -3.0285230374409053 | FAIL |
| recent_trades | >= 5 | 113 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.10545698640857286 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.1494655590365193, pnl=-3.0285230374409053, trades=113, reason=recent objective score -0.1495 <= 0; recent PnL -3.0285% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.008911002665601162, pnl=2.2441967230858726, trades=56, reason=recent objective score -0.0089 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.015560199978175704, pnl=2.2441967230858726, trades=56, reason=recent objective score -0.0156 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.167975402520258 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51875 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1495 <= 0; recent PnL -3.0285% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0089 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0156 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51875
- **Pre-release bars**: 43884
- **Dev bars**: 35108
- **Holdout bars**: 8776
- **Recent 28d bars**: 7991
- **Recent window start**: 1774105500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:22:35.588395+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8533
- **validation_status**: validated_fail
