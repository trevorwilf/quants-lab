# PMM Dynamic Optimization Report: mexc_LTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 09:24:48 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T09:24:48.068498+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 2871 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 51839
- **dataset_hash**: dbf3b0fdb3f19dd93a0c69259c1b6e65ba245cc3a322249eca03697f823182e2
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 469.7441228277941
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 17 |
| bb_length | 73 |
| bb_std | 2.42516861451854 |
| bbp_entry_threshold | 0.23693162347089025 |
| cooldown_time | 64461 |
| max_atr_pct_for_entry | 0.007807015815722709 |
| min_volume_quantile | 0.3197817437833963 |
| rsi_entry_threshold | 49.82212702148016 |
| rsi_length | 18 |
| stop_loss | 0.04486183868931776 |
| take_profit | 0.02491924370158413 |
| take_profit_order_type | MARKET |
| time_limit | 236811 |
| total_amount_quote | 469.7441228277941 |
| trailing_stop_activation | 0.000683203417601787 |
| trailing_stop_delta | 0.013409144183265847 |
| trend_ema_length | 332 |
| use_trend_filter | False |
| volume_filter_window | 84 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 469.7441228277941 |
| Selected | 469.7441228277941 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 11.1466
- **Net PnL (quote)**: 52.3606
- **Sharpe Ratio**: 2.4965
- **Max Drawdown %**: 3.6191
- **Profit Factor**: 10.17163465638108
- **Trade Count**: 127
- **Total Fees (quote)**: 23.1265
- **Maker Fees**: 11.5557
- **Taker Fees**: 11.5708
- **Fee Drag %**: 4.9232

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0534
- **PnL Component**: 0.1057
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0271
- **Fee Drag Component**: -0.0246
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.4467**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.84 | -3.83 | 3.78 | 14 | -0.4396 | n/a |
| 1 | 1.05 | 3.66 | 0.63 | 16 | -0.1334 | n/a |
| 2 | 0.27 | 1.00 | 0.98 | 20 | -0.1277 | n/a |
| 3 | 0.39 | 0.94 | 1.39 | 20 | -0.3791 | n/a |
| 4 | 1.26 | 2.13 | 2.49 | 18 | -0.1371 | n/a |
| 5 | 0.20 | 0.37 | 2.06 | 19 | -0.1416 | n/a |
| 6 | -4.30 | -4.81 | 4.56 | 4 | -0.5143 | n/a |
| 7 | -1.35 | -2.10 | 2.29 | 10 | -0.4425 | n/a |
| 8 | 0.44 | 1.19 | 1.60 | 16 | -0.3957 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 8.69 | 1.96 | 3.69 | 0.0181 |
| fees_2x | 6.22 | 1.43 | 3.77 | -0.0246 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 11.39 | 2.55 | 3.59 | 0.0558 |
| very_low_liquidity | 10.26 | 2.35 | 3.63 | 0.0454 |
| high_slippage | -4.22 | -2.37 | 4.60 | -0.2510 |
| extreme_slippage | -5.10 | -2.89 | 5.25 | -0.2151 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 2.58 | 0.51 | 9.63 | -0.2972 |
| spread_widen_25bps | -3.90 | -1.50 | 4.58 | -0.2167 |
| thin_book | -4.07 | -2.11 | 4.62 | -0.2644 |
| very_thin_book | -4.27 | -3.05 | 4.56 | -1000.0000 |
| entry_spread_stress | -3.74 | -1.46 | 4.54 | -0.2228 |
| combined_market_deterioration | -3.56 | -1.55 | 4.59 | -0.2445 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0019)
- **Best holdout score**: -0.1536 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9733 | -0.2441 | -4.31 | 4.56 | 10 |
| 1 | -0.0664 | -0.1826 | -1.05 | 1.94 | 11 |
| 2 | -0.0679 | -0.2081 | -1.55 | 1.55 | 6 |
| 3 | -0.0723 | -0.1536 | -1.59 | 2.39 | 21 |
| 4 | -0.0728 | -0.4331 | -1.87 | 2.28 | 4 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51839
- **Expected rows**: 51841
- **Missing rows**: 2
- **Forward-fill count**: 53
- **Forward-fill fraction**: 0.0010223962653600571
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0831 <= 0
- **Objective score**: -0.08309506671638857
- **PnL %**: 0.6867750666864625
- **Trade count**: 32

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3878 <= 0
- **Objective score**: -0.3878461866905772
- **PnL %**: 0.12436157711105233
- **Trade count**: 19

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4667 <= 0; recent PnL -0.4344% < 0
- **Objective score**: -0.46666920640368686
- **PnL %**: -0.4343946896856624
- **Trade count**: 14

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.30827311083334263
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.2161, -0.1066 |
| bb_std | -0.2276, -0.1183 |
| bbp_entry_threshold | -0.0882, -0.2276 |
| rsi_length | -0.3083, -0.3083 |
| rsi_entry_threshold | -0.3083, -0.1115 |
| trend_ema_length | -0.3009, -0.3120 |
| max_atr_pct_for_entry | -0.3069, -0.3087 |
| volume_filter_window | -0.3085, -0.4054 |
| min_volume_quantile | -0.4040, -0.3124 |
| stop_loss | -0.3236, -0.2937 |
| take_profit | -0.3083, -0.3083 |
| cooldown_time | -0.2485, -0.2382 |
| total_amount_quote | -0.3082, -0.3084 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.674341160680498
- **Max CV**: 0.942400803265634
- **Clustered params**: stop_loss, take_profit
- **Scattered params**: cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4707 | 0.01954158719339393 | 0.06157132503038487 | 0.031634963808437756 |
| take_profit | 0.4574 | 0.013575475251934413 | 0.05970736302765017 | 0.04006670101738742 |
| cooldown_time | 0.9424 | 2501.0 | 23861.0 | 6672.4 |
| total_amount_quote | 0.8269 | 29.115385574792498 | 523.6930980173448 | 188.849008805226 |

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
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.08309506671638857 | FAIL |
| recent_pnl | >= 0 | 0.6867750666864625 | PASS |
| recent_trades | >= 5 | 32 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.24407619176190715 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.08309506671638857, pnl=0.6867750666864625, trades=32, reason=recent objective score -0.0831 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.3878461866905772, pnl=0.12436157711105233, trades=19, reason=recent objective score -0.3878 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.46666920640368686, pnl=-0.4343946896856624, trades=14, reason=recent objective score -0.4667 <= 0; recent PnL -0.4344% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.674341160680498 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51839 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0831 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3878 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4667 <= 0; recent PnL -0.4344% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51839
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8063
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T09:24:48.068498+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 2871
- **validation_status**: validated_fail
