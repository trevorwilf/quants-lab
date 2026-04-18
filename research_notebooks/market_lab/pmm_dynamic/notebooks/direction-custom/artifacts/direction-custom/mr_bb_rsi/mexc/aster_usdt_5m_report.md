# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 06:19:11 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T06:19:11.170786+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1248 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m
- **n_candles**: 51651
- **dataset_hash**: 94e65d3ef6c6482445b337259c1eba462a79dfb609778afa6da6eff465000e28
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 638.1767495817559
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 11 |
| bb_length | 160 |
| bb_std | 1.6486774179025467 |
| bbp_entry_threshold | 0.3742102236390457 |
| cooldown_time | 8150 |
| max_atr_pct_for_entry | 0.047619348650096455 |
| min_volume_quantile | 0.44947494694670426 |
| rsi_entry_threshold | 47.19133108910596 |
| rsi_length | 13 |
| stop_loss | 0.06906755753197993 |
| take_profit | 0.050449323411552054 |
| take_profit_order_type | MARKET |
| time_limit | 339328 |
| total_amount_quote | 638.1767495817559 |
| trailing_stop_activation | 0.0003541543697027582 |
| trailing_stop_delta | 0.01888863163043231 |
| trend_ema_length | 268 |
| use_trend_filter | False |
| volume_filter_window | 184 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 638.1767495817559 |
| Selected | 638.1767495817559 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 45.3920
- **Net PnL (quote)**: 289.6809
- **Sharpe Ratio**: 4.8040
- **Max Drawdown %**: 5.0050
- **Profit Factor**: 58.60250647245339
- **Trade Count**: 137
- **Total Fees (quote)**: 33.7604
- **Maker Fees**: 16.8478
- **Taker Fees**: 16.9125
- **Fee Drag %**: 5.2901

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.3097
- **PnL Component**: 0.3743
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0375
- **Fee Drag Component**: -0.0265
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1331**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 2.66 | 4.77 | 2.14 | 17 | -0.1254 | n/a |
| 1 | 5.86 | 11.49 | 1.23 | 20 | -0.0761 | n/a |
| 2 | 1.42 | 2.85 | 1.93 | 19 | -0.1279 | n/a |
| 3 | 2.77 | 10.05 | 0.50 | 10 | -0.1383 | n/a |
| 4 | 4.09 | 5.47 | 2.03 | 15 | -0.1182 | n/a |
| 5 | 1.50 | 2.85 | 2.28 | 11 | -0.1609 | n/a |
| 6 | 0.53 | 7.88 | 0.00 | 3 | -1000.0000 | n/a |
| 7 | -1.17 | -4.93 | 1.36 | 1 | -1000.0000 | n/a |
| 8 | 0.76 | 4.71 | 0.46 | 10 | -0.1571 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 42.75 | 4.56 | 5.03 | 0.2779 |
| fees_2x | 40.10 | 4.31 | 5.06 | 0.2458 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 45.20 | 4.79 | 5.00 | 0.3082 |
| very_low_liquidity | 43.16 | 4.62 | 5.01 | 0.2942 |
| high_slippage | 38.76 | 4.20 | 5.05 | 0.2627 |
| extreme_slippage | 25.51 | 2.92 | 5.15 | 0.1615 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 34.10 | 3.60 | 7.65 | 0.2089 |
| spread_widen_25bps | 22.98 | 2.30 | 12.04 | 0.0894 |
| thin_book | 14.08 | 2.05 | 5.49 | 0.0465 |
| very_thin_book | 4.32 | 1.03 | 5.77 | -0.1326 |
| entry_spread_stress | 34.70 | 3.58 | 7.74 | 0.2131 |
| combined_market_deterioration | 16.41 | 2.01 | 5.20 | 0.0950 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0013)
- **Best holdout score**: -0.1318 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.8452 | -0.1376 | 0.81 | 3.01 | 20 |
| 1 | -0.1254 | -0.1590 | -0.84 | 3.14 | 19 |
| 2 | -0.1278 | -0.1673 | 1.56 | 4.77 | 14 |
| 3 | -0.1318 | -0.1464 | 0.73 | 3.01 | 18 |
| 4 | -0.1351 | -0.1318 | -0.08 | 3.60 | 25 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51651
- **Expected rows**: 51841
- **Missing rows**: 190
- **Forward-fill count**: 77
- **Forward-fill fraction**: 0.0014907746219821494
- **Longest gap (seconds)**: 15900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1498 <= 0
- **Objective score**: -0.14977976374448135
- **PnL %**: 0.11069842022334382
- **Trade count**: 14

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

- **Sensitivity penalty**: 0.34615384615384615
- **Baseline score**: 0.321071167687671
- **Sign flips**: 3
- **Collapse count**: 6
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2033, 0.1871 |
| bb_std | 0.3159, 0.2683 |
| bbp_entry_threshold | -0.2131, 0.1544 |
| rsi_length | 0.3407, 0.3337 |
| rsi_entry_threshold | 0.2885, 0.0556 |
| trend_ema_length | 0.3350, -0.3014 |
| max_atr_pct_for_entry | 0.3211, 0.3211 |
| volume_filter_window | 0.2572, 0.3208 |
| min_volume_quantile | 0.2873, 0.2996 |
| stop_loss | 0.3211, 0.3211 |
| take_profit | 0.3211, 0.3211 |
| cooldown_time | 0.1364, 0.2534 |
| total_amount_quote | 0.3208, 0.3212 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.385600461355276
- **Max CV**: 0.6747547565384536
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1555 | 0.04613685102446253 | 0.07683815024378471 | 0.05948802380534043 |
| take_profit | 0.4241 | 0.0064594358329226635 | 0.05753850735099027 | 0.036178492865556175 |
| cooldown_time | 0.6748 | 2284.0 | 47946.0 | 24892.8 |
| total_amount_quote | 0.2881 | 321.30464295578065 | 970.5778431319616 | 720.9885942179848 |

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
| recent_objective | > 0 | -0.14977976374448135 | FAIL |
| recent_pnl | >= 0 | 0.11069842022334382 | PASS |
| recent_trades | >= 5 | 14 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.34615384615384615 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.13763548153065774 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.34615384615384615 |
| recent_28d | FAIL | score=-0.14977976374448135, pnl=0.11069842022334382, trades=14, reason=recent objective score -0.1498 <= 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.385600461355276 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51651 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1498 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51651
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7875
- **Recent window start**: 1774072800

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T06:19:11.170786+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1248
- **validation_status**: validated_fail
