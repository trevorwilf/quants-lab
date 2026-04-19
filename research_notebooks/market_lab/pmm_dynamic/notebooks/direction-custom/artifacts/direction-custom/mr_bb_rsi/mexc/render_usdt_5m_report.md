# PMM Dynamic Optimization Report: mexc_RENDER-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 09:54:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T09:54:32.447072+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 1867 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: RENDER-USDT
- **interval**: 5m
- **n_candles**: 51840
- **dataset_hash**: 77f1082fcf605d1b478954be536b55bbcefa1ad0213885d44e639f975e9698d0
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 746.611222775524
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 21 |
| bb_length | 199 |
| bb_std | 1.5381335410326027 |
| bbp_entry_threshold | 0.10326405793294657 |
| cooldown_time | 5188 |
| max_atr_pct_for_entry | 0.03521867190142161 |
| min_volume_quantile | 0.18205152034860972 |
| rsi_entry_threshold | 49.6346765665332 |
| rsi_length | 30 |
| stop_loss | 0.017450526851163443 |
| take_profit | 0.02334681531483621 |
| take_profit_order_type | MARKET |
| time_limit | 186306 |
| total_amount_quote | 746.611222775524 |
| trailing_stop_activation | 0.0003820703510042738 |
| trailing_stop_delta | 0.0008957937931635285 |
| trend_ema_length | 136 |
| use_trend_filter | False |
| volume_filter_window | 191 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 746.611222775524 |
| Selected | 746.611222775524 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1453
- **Net PnL (quote)**: -8.5508
- **Sharpe Ratio**: -0.8071
- **Max Drawdown %**: 1.8213
- **Profit Factor**: 0.5017788594004935
- **Trade Count**: 58
- **Total Fees (quote)**: 4.0203
- **Maker Fees**: 2.0106
- **Taker Fees**: 2.0097
- **Fee Drag %**: 0.5385

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0279
- **PnL Component**: -0.0115
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0137
- **Fee Drag Component**: -0.0027
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0247**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.34 | 0.76 | 2.51 | 97 | -0.0190 | n/a |
| 1 | -1.83 | -4.89 | 1.91 | 2 | -1000.0000 | n/a |
| 2 | 2.01 | 3.53 | 1.56 | 87 | 0.0041 | n/a |
| 3 | 3.17 | 4.77 | 2.71 | 72 | 0.0044 | n/a |
| 4 | -1.77 | -7.14 | 1.84 | 9 | -0.2053 | n/a |
| 5 | -1.72 | -3.61 | 2.54 | 55 | -0.0390 | n/a |
| 6 | 0.94 | 2.56 | 1.82 | 80 | -0.0064 | n/a |
| 7 | -1.18 | -2.21 | 2.69 | 32 | -0.1069 | n/a |
| 8 | 3.49 | 3.27 | 5.63 | 92 | -0.0112 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.41 | -1.00 | 1.85 | -0.0369 |
| fees_2x | -1.68 | -1.19 | 1.90 | -0.0479 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.05 | -4.64 | 1.05 | -0.3232 |
| very_low_liquidity | -1.44 | -5.61 | 1.44 | -0.3334 |
| high_slippage | -1.82 | -1.30 | 1.93 | -0.0500 |
| extreme_slippage | -1.06 | -2.02 | 1.47 | -0.1791 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.61 | -1.99 | 3.63 | -0.0564 |
| spread_widen_25bps | -2.34 | -2.86 | 2.60 | -0.0451 |
| thin_book | -1.01 | -0.44 | 3.36 | -0.0408 |
| very_thin_book | 1.84 | 1.08 | 2.39 | -0.0385 |
| entry_spread_stress | -1.06 | -0.95 | 1.82 | -0.0269 |
| combined_market_deterioration | -1.54 | -2.79 | 1.61 | -0.1800 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0044)
- **Trend**: ranging (efficiency: 0.0078)
- **Best holdout score**: 0.0302 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0140 | -1000.0000 | -1.83 | 1.83 | 3 |
| 1 | 0.0067 | 0.0302 | 6.45 | 3.24 | 120 |
| 2 | 0.0059 | -0.1857 | -1.17 | 1.54 | 29 |
| 3 | -0.0059 | 0.0055 | 3.63 | 2.93 | 119 |
| 4 | -0.0072 | -0.0318 | -1.05 | 2.23 | 80 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51840
- **Expected rows**: 51841
- **Missing rows**: 1
- **Forward-fill count**: 78
- **Forward-fill fraction**: 0.0015046296296296296
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1715 <= 0; recent PnL -1.7029% < 0
- **Objective score**: -0.17152869623255831
- **PnL %**: -1.702929105686275
- **Trade count**: 16

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0574 <= 0; recent PnL -1.0612% < 0
- **Objective score**: -0.05741674666132211
- **PnL %**: -1.0612331388671148
- **Trade count**: 44

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1780 <= 0; recent PnL -1.5569% < 0
- **Objective score**: -0.17798397271723143
- **PnL %**: -1.556895411510439
- **Trade count**: 14

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.027895436933426363
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0279, -0.0271 |
| bb_std | -0.2056, -0.0630 |
| bbp_entry_threshold | -0.0273, -0.0287 |
| rsi_length | -0.0279, -0.0279 |
| rsi_entry_threshold | -0.0279, -0.2139 |
| trend_ema_length | -0.0279, -0.0279 |
| max_atr_pct_for_entry | -0.0279, -0.0279 |
| volume_filter_window | -0.0279, -0.0279 |
| min_volume_quantile | -0.0279, -0.0279 |
| stop_loss | -0.0312, -0.0540 |
| take_profit | -0.0279, -0.0279 |
| cooldown_time | -0.0366, -0.0285 |
| total_amount_quote | -0.0297, -0.0266 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.43618484315499795
- **Max CV**: 0.6302079904602335
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2196 | 0.015041023969027647 | 0.03218873941162693 | 0.022377944807961566 |
| take_profit | 0.5964 | 0.005072519979972948 | 0.040349938382064104 | 0.020963743304034676 |
| cooldown_time | 0.6302 | 969.0 | 15237.0 | 6753.0 |
| total_amount_quote | 0.2986 | 286.9490534488694 | 980.36844235403 | 684.2179746553838 |

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
| recent_objective | > 0 | -0.17152869623255831 | FAIL |
| recent_pnl | >= 0 | -1.702929105686275 | FAIL |
| recent_trades | >= 5 | 16 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.17152869623255831, pnl=-1.702929105686275, trades=16, reason=recent objective score -0.1715 <= 0; recent PnL -1.7029% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.05741674666132211, pnl=-1.0612331388671148, trades=44, reason=recent objective score -0.0574 <= 0; recent PnL -1.0612% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.17798397271723143, pnl=-1.556895411510439, trades=14, reason=recent objective score -0.1780 <= 0; recent PnL -1.5569% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.43618484315499795 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51840 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1715 <= 0; recent PnL -1.7029% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0574 <= 0; recent PnL -1.0612% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1780 <= 0; recent PnL -1.5569% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51840
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T09:54:32.447072+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 1867
- **validation_status**: validated_fail
