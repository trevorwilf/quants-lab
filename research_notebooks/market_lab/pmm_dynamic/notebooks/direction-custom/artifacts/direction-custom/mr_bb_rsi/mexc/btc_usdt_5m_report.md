# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-17 23:48:58 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-17T23:48:58.026094+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 163 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51765
- **dataset_hash**: 99628f5beaa81e87323dc90ab0b1c94e8dbc5776a28720d6bf20043aba3b2e4d
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 366.47015775556025
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 30 |
| bb_length | 90 |
| bb_std | 2.7132036000998405 |
| bbp_entry_threshold | 0.18897280172200856 |
| cooldown_time | 11357 |
| max_atr_pct_for_entry | 0.02045551881543069 |
| min_volume_quantile | 0.4820404115941603 |
| rsi_entry_threshold | 37.3707748493244 |
| rsi_length | 7 |
| stop_loss | 0.028893667255665084 |
| take_profit | 0.018617567898066997 |
| take_profit_order_type | LIMIT |
| time_limit | 20910 |
| total_amount_quote | 366.47015775556025 |
| trailing_stop_activation | 0.0021258266467220933 |
| trailing_stop_delta | 0.011348333876324963 |
| trend_ema_length | 291 |
| use_trend_filter | True |
| volume_filter_window | 391 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 366.47015775556025 |
| Selected | 366.47015775556025 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.6510
- **Net PnL (quote)**: -6.0506
- **Sharpe Ratio**: -0.8130
- **Max Drawdown %**: 3.8671
- **Profit Factor**: 0.6554805922779249
- **Trade Count**: 30
- **Total Fees (quote)**: 4.3906
- **Maker Fees**: 2.1955
- **Taker Fees**: 2.1952
- **Fee Drag %**: 1.1981

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1318
- **PnL Component**: -0.0166
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0290
- **Fee Drag Component**: -0.0060
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0800
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -2.25 | -1.11 | 4.05 | -0.1423 |
| fees_2x | -2.85 | -1.41 | 4.23 | -0.1448 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.65 | -0.81 | 3.87 | -0.1318 |
| very_low_liquidity | -1.65 | -0.81 | 3.87 | -0.1318 |
| high_slippage | -3.15 | -1.57 | 4.35 | -0.1268 |
| extreme_slippage | -1.08 | -0.87 | 1.94 | -0.2864 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.92 | -1.39 | 4.25 | -0.1157 |
| spread_widen_25bps | -1.20 | -0.60 | 2.46 | -0.1115 |
| thin_book | 0.43 | 0.48 | 1.12 | -0.1499 |
| very_thin_book | 0.75 | 0.91 | 0.93 | -0.1692 |
| entry_spread_stress | -3.54 | -1.62 | 4.47 | -0.1158 |
| combined_market_deterioration | -0.63 | -0.49 | 1.47 | -0.1306 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8758
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0021)
- **Trend**: ranging (efficiency: 0.0044)
- **Best holdout score**: -0.1888 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0659 | -0.1888 | -1.39 | 1.74 | 10 |
| 1 | -0.1532 | -0.2161 | -3.11 | 3.53 | 11 |
| 2 | -0.1649 | -0.2108 | -1.02 | 2.08 | 4 |
| 3 | -0.1710 | -0.2062 | -1.32 | 2.06 | 6 |
| 4 | -0.1777 | -0.2247 | -2.45 | 3.51 | 7 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51765
- **Expected rows**: 51859
- **Missing rows**: 94
- **Forward-fill count**: 786
- **Forward-fill fraction**: 0.015184004636337293
- **Longest gap (seconds)**: 8100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2039 <= 0; recent PnL -1.0943% < 0
- **Objective score**: -0.20394884654388562
- **PnL %**: -1.0942573676543859
- **Trade count**: 5

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -1.5514% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -1.5514058738000365
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.0475% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.04748975592197502
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.13175568861488277
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | -0.1368, -0.1267 |
| take_profit | -0.1318, -0.1318 |
| cooldown_time | -0.1318, -0.1252 |
| total_amount_quote | -0.1317, -0.1317 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4891532852557585
- **Max CV**: 0.6695646286179661
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3014 | 0.016272599861502646 | 0.037151465630128826 | 0.024274648708790862 |
| take_profit | 0.6696 | 0.006478423412667631 | 0.055993656231960204 | 0.025292121908164066 |
| cooldown_time | 0.6425 | 3764.0 | 32278.0 | 12571.0 |
| total_amount_quote | 0.3431 | 286.3477736406726 | 868.0776156657018 | 516.4331937976992 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.20394884654388562 | FAIL |
| recent_pnl | >= 0 | -1.0942573676543859 | FAIL |
| recent_trades | >= 5 | 5 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.18883456187807796 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.20394884654388562, pnl=-1.0942573676543859, trades=5, reason=recent objective score -0.2039 <= 0; recent PnL -1.0943% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-1.5514058738000365, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -1.5514% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.04748975592197502, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -0.0475% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4891532852557585 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51765 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2039 <= 0; recent PnL -1.0943% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -1.5514% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.0475% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51765
- **Pre-release bars**: 43794
- **Dev bars**: 35036
- **Holdout bars**: 8758
- **Recent 28d bars**: 7971
- **Recent window start**: 1774042200

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-17T23:48:58.026094+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 163
