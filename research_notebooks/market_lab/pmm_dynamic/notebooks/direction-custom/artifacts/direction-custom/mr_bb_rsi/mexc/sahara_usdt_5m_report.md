# PMM Dynamic Optimization Report: mexc_SAHARA-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 10:04:48 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T10:04:48.724206+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 31 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: SAHARA-USDT
- **interval**: 5m
- **n_candles**: 51831
- **dataset_hash**: c17ec76329881b8f1195a59a86b7cff76f16dbcbff6d07b9924474f8dbcd489c
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 841.6990777590246
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 21 |
| bb_length | 59 |
| bb_std | 2.6342485455072513 |
| bbp_entry_threshold | 0.3808931526523845 |
| cooldown_time | 47744 |
| max_atr_pct_for_entry | 0.05094754793709507 |
| min_volume_quantile | 0.25260248425659204 |
| rsi_entry_threshold | 49.059658600530355 |
| rsi_length | 28 |
| stop_loss | 0.01654675488000816 |
| take_profit | 0.0169084243416754 |
| take_profit_order_type | MARKET |
| time_limit | 46358 |
| total_amount_quote | 841.6990777590246 |
| trailing_stop_activation | 0.005149821278336768 |
| trailing_stop_delta | 0.009100580537911273 |
| trend_ema_length | 99 |
| use_trend_filter | False |
| volume_filter_window | 173 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 841.6990777590246 |
| Selected | 841.6990777590246 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 3.0544
- **Net PnL (quote)**: 25.7093
- **Sharpe Ratio**: 3.3254
- **Max Drawdown %**: 0.5622
- **Profit Factor**: 8762.234861138497
- **Trade Count**: 16
- **Total Fees (quote)**: 2.0256
- **Maker Fees**: 1.0100
- **Taker Fees**: 1.0156
- **Fee Drag %**: 0.2407

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1113
- **PnL Component**: 0.0301
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0042
- **Fee Drag Component**: -0.0012
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1360
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.55 | 3.33 | 0.58 | 6 | -0.1753 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.47 | 4.47 | 0.32 | 2 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.93 | 3.22 | 0.58 | -0.1133 |
| fees_2x | 2.81 | 3.12 | 0.61 | -0.1152 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 1.56 | 1.65 | 1.04 | -0.0377 |
| very_low_liquidity | -1.13 | -4.55 | 1.19 | -0.4248 |
| high_slippage | 2.75 | 3.02 | 0.61 | -0.1146 |
| extreme_slippage | 2.15 | 2.36 | 0.71 | -0.1213 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 3.22 | 3.37 | 0.58 | -0.1099 |
| spread_widen_25bps | 0.90 | 0.81 | 2.07 | -0.1438 |
| thin_book | -0.66 | -2.35 | 0.76 | -1000.0000 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | 3.07 | 3.26 | 0.61 | -0.1116 |
| combined_market_deterioration | 0.26 | 0.33 | 1.87 | -0.1843 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0075)
- **Trend**: ranging (efficiency: 0.0134)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0557 | -1000.0000 | 0.47 | 0.32 | 2 |
| 1 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51831
- **Expected rows**: 51841
- **Missing rows**: 10
- **Forward-fill count**: 193
- **Forward-fill fraction**: 0.003723640292489051
- **Longest gap (seconds)**: 3300

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

- **Sensitivity penalty**: 0.11538461538461539
- **Baseline score**: -0.09894770954251259
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1239, -0.1131 |
| bb_std | -1000.0000, -0.1311 |
| bbp_entry_threshold | -0.1486, -0.1087 |
| rsi_length | -0.0841, -0.0989 |
| rsi_entry_threshold | -0.0989, -0.1724 |
| trend_ema_length | -0.0989, -0.0989 |
| max_atr_pct_for_entry | -0.0989, -0.0989 |
| volume_filter_window | -0.0989, -0.0989 |
| min_volume_quantile | -0.0989, -0.1186 |
| stop_loss | -0.0989, -0.0989 |
| take_profit | -0.0989, -0.0989 |
| cooldown_time | -0.0908, -0.0661 |
| total_amount_quote | -0.0987, -0.1035 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5465690930453482
- **Max CV**: 0.7035440873964931
- **Clustered params**: stop_loss
- **Scattered params**: take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4511 | 0.015846488196553956 | 0.06760341855737632 | 0.03903996279418816 |
| take_profit | 0.5016 | 0.005570740712340032 | 0.025877575042778093 | 0.014127329229890706 |
| cooldown_time | 0.7035 | 1319.0 | 81404.0 | 45223.8 |
| total_amount_quote | 0.5300 | 27.846360259215086 | 973.6975036774652 | 581.5399116555404 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.11538461538461539 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.11538461538461539 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5465690930453482 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51831 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51831
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8055
- **Recent window start**: 1774015500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T10:04:48.724206+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 31
- **validation_status**: validated_fail
