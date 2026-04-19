# PMM Dynamic Optimization Report: nonkyc_PEP-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:53:22 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:53:22.994656+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8134 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: PEP-USDT
- **interval**: 5m
- **n_candles**: 51873
- **dataset_hash**: 3d349bebf89563efbc527a81b33f571051670a4aa0014af06e10931a17ba4493
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 579.4817507299631
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 15 |
| bb_length | 26 |
| bb_std | 2.7261653703303925 |
| bbp_entry_threshold | 0.34625205130245257 |
| cooldown_time | 8965 |
| max_atr_pct_for_entry | 0.04939770184390667 |
| min_volume_quantile | 0.010970850890280378 |
| rsi_entry_threshold | 48.195622779899125 |
| rsi_length | 12 |
| stop_loss | 0.041668005122174896 |
| take_profit | 0.058012193635807445 |
| take_profit_order_type | MARKET |
| time_limit | 21959 |
| total_amount_quote | 579.4817507299631 |
| trailing_stop_activation | 0.02994201772485725 |
| trailing_stop_delta | 0.010790232221312375 |
| trend_ema_length | 319 |
| use_trend_filter | False |
| volume_filter_window | 269 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 579.4817507299631 |
| Selected | 579.4817507299631 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 11.8795
- **Net PnL (quote)**: 68.8398
- **Sharpe Ratio**: 2.7668
- **Max Drawdown %**: 3.0054
- **Profit Factor**: 28.880268073754905
- **Trade Count**: 178
- **Total Fees (quote)**: 9.2077
- **Maker Fees**: 3.2585
- **Taker Fees**: 5.9492
- **Fee Drag %**: 1.5890

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0816
- **PnL Component**: 0.1123
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0225
- **Fee Drag Component**: -0.0079
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1206**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -4.51 | -7.70 | 4.51 | 25 | -0.4455 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 2.11 | 2.84 | 1.45 | 39 | -0.0360 | n/a |
| 4 | 2.23 | 6.61 | 0.68 | 23 | -0.0924 | n/a |
| 5 | -4.52 | -12.42 | 4.66 | 35 | -0.4561 | n/a |
| 6 | 1.34 | 2.52 | 0.85 | 36 | -0.0511 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 11.09 | 2.61 | 3.05 | 0.0701 |
| fees_2x | 10.29 | 2.46 | 3.11 | 0.0586 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 5.32 | 2.12 | 1.53 | 0.0355 |
| very_low_liquidity | 2.07 | 1.23 | 1.62 | -0.0004 |
| high_slippage | 11.62 | 2.72 | 3.01 | 0.0793 |
| extreme_slippage | 11.11 | 2.63 | 3.01 | 0.0747 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 11.63 | 2.71 | 3.04 | 0.0791 |
| spread_widen_25bps | -1.28 | -0.31 | 3.54 | -0.0427 |
| thin_book | 1.93 | 1.41 | 1.88 | -0.1399 |
| very_thin_book | 0.74 | 1.33 | 0.73 | -0.1824 |
| entry_spread_stress | -1.22 | -0.29 | 3.53 | -0.0419 |
| combined_market_deterioration | 1.97 | 1.33 | 2.12 | -0.1339 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0094)
- **Trend**: ranging (efficiency: 0.0104)
- **Best holdout score**: 0.0405 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9592 | -0.1744 | 0.65 | 0.09 | 5 |
| 1 | -0.0814 | 0.0405 | 6.57 | 1.00 | 47 |
| 2 | -0.0839 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -0.0853 | -0.0829 | 1.56 | 0.57 | 27 |
| 4 | -0.0863 | -0.4229 | -0.14 | 0.76 | 20 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51873
- **Expected rows**: 51899
- **Missing rows**: 26
- **Forward-fill count**: 459
- **Forward-fill fraction**: 0.008848533919380024
- **Longest gap (seconds)**: 6000

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

- **Sensitivity penalty**: 0.5384615384615384
- **Baseline score**: 0.08821858588739169
- **Sign flips**: 7
- **Collapse count**: 7
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0840, 0.0775 |
| bb_std | -0.0840, -0.0577 |
| bbp_entry_threshold | -0.0577, -0.0840 |
| rsi_length | 0.0775, 0.0882 |
| rsi_entry_threshold | 0.0882, -0.4623 |
| trend_ema_length | 0.0775, -0.0405 |
| max_atr_pct_for_entry | 0.0882, 0.0882 |
| volume_filter_window | 0.0882, 0.0882 |
| min_volume_quantile | 0.0882, 0.0882 |
| stop_loss | 0.0882, 0.0882 |
| take_profit | 0.0882, 0.0882 |
| cooldown_time | 0.0882, 0.0708 |
| total_amount_quote | 0.0802, 0.0924 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4763176565230763
- **Max CV**: 1.0693527193288352
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4286 | 0.015245187473083451 | 0.06538851463087003 | 0.03454011008754797 |
| take_profit | 0.2494 | 0.025181319664344837 | 0.05924131054423761 | 0.04421818979178922 |
| cooldown_time | 1.0694 | 1883.0 | 36889.0 | 13537.4 |
| total_amount_quote | 0.1579 | 389.02226706034287 | 600.54338242433 | 479.5158854748611 |

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
- sensitivity_stable: **FAIL**
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
| sensitivity_penalty | < 0.50 | 0.5384615384615384 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.17438856551017362 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.5384615384615384 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4763176565230763 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51873 |  |
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

- **Full bars**: 51873
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8039
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:53:22.994656+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8134
- **validation_status**: validated_fail
