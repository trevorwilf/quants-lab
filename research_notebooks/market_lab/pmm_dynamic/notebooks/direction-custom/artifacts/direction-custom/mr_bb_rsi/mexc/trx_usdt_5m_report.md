# PMM Dynamic Optimization Report: mexc_TRX-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 10:25:24 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T10:25:24.400477+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 2651 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TRX-USDT
- **interval**: 5m
- **n_candles**: 51774
- **dataset_hash**: e47b45b6d892271c7a9d1693bd769279fdb1511c0559b56aa8aed9ce9e807dc3
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 141.60159179810316
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 18 |
| bb_length | 36 |
| bb_std | 1.186588737513449 |
| bbp_entry_threshold | 0.2809062590260444 |
| cooldown_time | 58154 |
| max_atr_pct_for_entry | 0.059607099569741924 |
| min_volume_quantile | 0.52206073006199 |
| rsi_entry_threshold | 49.4867440023035 |
| rsi_length | 10 |
| stop_loss | 0.03741318060586211 |
| take_profit | 0.02698849854551287 |
| take_profit_order_type | MARKET |
| time_limit | 311500 |
| total_amount_quote | 141.60159179810316 |
| trailing_stop_activation | 5.989643139968522e-05 |
| trailing_stop_delta | 0.00491094382904327 |
| trend_ema_length | 300 |
| use_trend_filter | True |
| volume_filter_window | 175 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 141.60159179810316 |
| Selected | 141.60159179810316 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.2002
- **Net PnL (quote)**: -0.2835
- **Sharpe Ratio**: -0.5963
- **Max Drawdown %**: 0.4343
- **Profit Factor**: 0.5073324752420193
- **Trade Count**: 25
- **Total Fees (quote)**: 0.7364
- **Maker Fees**: 0.3682
- **Taker Fees**: 0.3683
- **Fee Drag %**: 0.5201

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1083
- **PnL Component**: -0.0020
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0033
- **Fee Drag Component**: -0.0026
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.11 | 3.17 | 0.11 | 6 | -0.1764 | n/a |
| 1 | -0.16 | -1.63 | 0.43 | 8 | -0.3380 | n/a |
| 2 | -0.05 | -1.25 | 0.22 | 4 | -0.1866 | n/a |
| 3 | -0.03 | -1.27 | 0.09 | 2 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | -0.08 | -3.08 | 0.15 | 4 | -0.3613 | n/a |
| 8 | 0.00 | 0.03 | 1.02 | 2 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.46 | -1.37 | 0.55 | -0.1112 |
| fees_2x | -0.72 | -2.12 | 0.76 | -0.1182 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -0.20 | -0.60 | 0.43 | -0.1083 |
| very_low_liquidity | -0.20 | -0.60 | 0.43 | -0.1083 |
| high_slippage | -0.85 | -2.61 | 0.87 | -0.1184 |
| extreme_slippage | -1.04 | -4.86 | 1.05 | -0.1685 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -0.61 | -1.53 | 0.75 | -0.1141 |
| spread_widen_25bps | -0.24 | -0.20 | 1.33 | -0.1436 |
| thin_book | 0.01 | 0.04 | 0.45 | -0.2516 |
| very_thin_book | 0.15 | 0.57 | 0.45 | -0.2415 |
| entry_spread_stress | -0.41 | -0.55 | 1.23 | -0.1250 |
| combined_market_deterioration | -1.00 | -2.60 | 1.08 | -0.1539 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0010)
- **Trend**: ranging (efficiency: 0.0234)
- **Best holdout score**: -0.3613 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0542 | -0.3613 | -0.08 | 0.15 | 4 |
| 1 | -0.1831 | -1000.0000 | -1.85 | 1.99 | 1 |
| 2 | -0.1840 | -1000.0000 | -0.04 | 0.12 | 3 |
| 3 | -0.1843 | -1000.0000 | -1.26 | 1.34 | 1 |
| 4 | -0.1845 | -1000.0000 | -3.08 | 3.24 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51774
- **Expected rows**: 51841
- **Missing rows**: 67
- **Forward-fill count**: 49
- **Forward-fill fraction**: 0.0009464209835052343
- **Longest gap (seconds)**: 18900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1849 <= 0; recent PnL -0.0604% < 0
- **Objective score**: -0.18492610585377925
- **PnL %**: -0.06035244187995853
- **Trade count**: 6

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1860 <= 0; recent PnL -0.0611% < 0; recent trades 4 < 5
- **Objective score**: -0.18602116511804254
- **PnL %**: -0.061101480313254276
- **Trade count**: 4

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0006863652796079882
- **Trade count**: 2

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.07783418661173322
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.1601, -0.0943 |
| bb_std | -0.0853, -0.0778 |
| bbp_entry_threshold | -0.0785, -0.0853 |
| rsi_length | -0.0705, -0.0778 |
| rsi_entry_threshold | -0.0705, -0.0841 |
| trend_ema_length | -0.0778, -0.0683 |
| max_atr_pct_for_entry | -0.0778, -0.0778 |
| volume_filter_window | -0.0778, -0.0813 |
| min_volume_quantile | -0.0971, -0.0881 |
| stop_loss | -0.0778, -0.0778 |
| take_profit | -0.0778, -0.0778 |
| cooldown_time | -0.0956, -0.0895 |
| total_amount_quote | -0.0778, -0.0778 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.47196300067177727
- **Max CV**: 0.5900718166999485
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4609 | 0.016162937804357038 | 0.06337067364358465 | 0.030826506154066992 |
| take_profit | 0.5901 | 0.008636778693207198 | 0.05629245628105528 | 0.024609462613910137 |
| cooldown_time | 0.5015 | 10275.0 | 74715.0 | 44368.0 |
| total_amount_quote | 0.3354 | 313.1015417890882 | 969.4569750156458 | 721.633093553049 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.18492610585377925 | FAIL |
| recent_pnl | >= 0 | -0.06035244187995853 | FAIL |
| recent_trades | >= 5 | 6 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.3613305880336195 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.18492610585377925, pnl=-0.06035244187995853, trades=6, reason=recent objective score -0.1849 <= 0; recent PnL -0.0604% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.18602116511804254, pnl=-0.061101480313254276, trades=4, reason=recent objective score -0.1860 <= 0; recent PnL -0.0611% < 0; recent trades 4 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0006863652796079882, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.47196300067177727 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51774 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1849 <= 0; recent PnL -0.0604% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1860 <= 0; recent PnL -0.0611% < 0; recent trades 4 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51774
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 7998
- **Recent window start**: 1774032300

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T10:25:24.400477+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 2651
- **validation_status**: validated_fail
