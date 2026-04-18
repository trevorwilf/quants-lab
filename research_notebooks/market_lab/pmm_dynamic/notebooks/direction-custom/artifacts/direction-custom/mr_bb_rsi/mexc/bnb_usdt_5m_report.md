# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-17 23:14:22 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-17T23:14:22.881603+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 375 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m
- **n_candles**: 51774
- **dataset_hash**: 1dd71d2171080d0805dd0a5bea02ae6038c219c9da41dd63c094a35813bf568f
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 512.5489178446605
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 13 |
| bb_length | 103 |
| bb_std | 2.15910464438719 |
| bbp_entry_threshold | 0.07962078306865222 |
| cooldown_time | 2745 |
| max_atr_pct_for_entry | 0.005298236856499875 |
| min_volume_quantile | 0.47294126612937976 |
| rsi_entry_threshold | 33.74592404356349 |
| rsi_length | 18 |
| stop_loss | 0.03159566291076205 |
| take_profit | 0.0075750803184062975 |
| take_profit_order_type | LIMIT |
| time_limit | 79446 |
| total_amount_quote | 512.5489178446605 |
| trailing_stop_activation | 0.0002117772819017343 |
| trailing_stop_delta | 0.013247923452515168 |
| trend_ema_length | 312 |
| use_trend_filter | False |
| volume_filter_window | 176 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 512.5489178446605 |
| Selected | 512.5489178446605 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -3.5952
- **Net PnL (quote)**: -18.4274
- **Sharpe Ratio**: -1.0353
- **Max Drawdown %**: 5.8766
- **Profit Factor**: 0.48567931357832256
- **Trade Count**: 55
- **Total Fees (quote)**: 8.6037
- **Maker Fees**: 4.3028
- **Taker Fees**: 4.3009
- **Fee Drag %**: 1.6786

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0893
- **PnL Component**: -0.0366
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0441
- **Fee Drag Component**: -0.0084
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.32 | -0.38 | 3.20 | -0.1370 |
| fees_2x | -1.82 | -0.55 | 3.29 | -0.1453 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -3.60 | -1.04 | 5.88 | -0.0893 |
| very_low_liquidity | -3.60 | -1.04 | 5.88 | -0.0893 |
| high_slippage | -2.07 | -0.63 | 3.39 | -0.1436 |
| extreme_slippage | -1.04 | -0.60 | 2.22 | -0.2150 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.75 | -0.51 | 3.25 | -0.1391 |
| spread_widen_25bps | -3.00 | -1.40 | 3.32 | -0.2098 |
| thin_book | -2.60 | -1.51 | 3.24 | -0.2280 |
| very_thin_book | -3.26 | -1.23 | 6.22 | -0.1774 |
| entry_spread_stress | -3.05 | -1.43 | 3.33 | -0.2101 |
| combined_market_deterioration | -4.19 | -1.93 | 4.19 | -0.2654 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0019)
- **Trend**: ranging (efficiency: 0.0025)
- **Best holdout score**: -0.1846 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0447 | -0.1846 | -3.51 | 3.51 | 20 |
| 1 | -0.1570 | -0.1856 | -3.86 | 3.97 | 22 |
| 2 | -0.1611 | -1000.0000 | -1.04 | 1.25 | 3 |
| 3 | -0.1627 | -1000.0000 | -1.04 | 1.25 | 3 |
| 4 | -0.1681 | -0.1846 | -3.51 | 3.51 | 20 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51774
- **Expected rows**: 51841
- **Missing rows**: 67
- **Forward-fill count**: 191
- **Forward-fill fraction**: 0.003689110364275505
- **Longest gap (seconds)**: 13200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1971 <= 0; recent PnL -1.3234% < 0
- **Objective score**: -0.1970903560075403
- **PnL %**: -1.3233809787496837
- **Trade count**: 8

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1381 <= 0; recent PnL -0.9158% < 0
- **Objective score**: -0.13807050550941652
- **PnL %**: -0.915765310793397
- **Trade count**: 23

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.1290% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.1290105899691003
- **Trade count**: 3

## Sensitivity Analysis

- **Sensitivity penalty**: 0.5
- **Baseline score**: -0.08924079646218402
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.1387, -0.1758 |
| take_profit | -0.0892, -0.0892 |
| cooldown_time | -0.1397, -0.1359 |
| total_amount_quote | -0.0892, -0.0892 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5599019780451098
- **Max CV**: 0.8437180770626197
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3158 | 0.020830882481052807 | 0.05811064780767691 | 0.04314150929308744 |
| take_profit | 0.7684 | 0.005021152332854378 | 0.029995615007504067 | 0.010549637842470505 |
| cooldown_time | 0.8437 | 2745.0 | 38472.0 | 13921.1 |
| total_amount_quote | 0.3116 | 384.7665406308829 | 924.7191556151078 | 631.2874203190117 |

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
- walkforward_positive_majority: **FAIL**
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
| recent_objective | > 0 | -0.1970903560075403 | FAIL |
| recent_pnl | >= 0 | -1.3233809787496837 | FAIL |
| recent_trades | >= 5 | 8 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.5 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.18456204850326827 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.5 |
| recent_28d | FAIL | score=-0.1970903560075403, pnl=-1.3233809787496837, trades=8, reason=recent objective score -0.1971 <= 0; recent PnL -1.3234% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.13807050550941652, pnl=-0.915765310793397, trades=23, reason=recent objective score -0.1381 <= 0; recent PnL -0.9158% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-1.1290105899691003, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -1.1290% < 0; recent trades 3 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5599019780451098 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51774 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1971 <= 0; recent PnL -1.3234% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1381 <= 0; recent PnL -0.9158% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.1290% < 0; recent trades 3 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51774
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7998
- **Recent window start**: 1774032000

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-17T23:14:22.881603+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 375
