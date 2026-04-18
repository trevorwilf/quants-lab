# PMM Dynamic Optimization Report: mexc_ASTER-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-17 22:08:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-17T22:08:16.618320+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 249 |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: ASTER-USDT
- **interval**: 5m
- **n_candles**: 51806
- **dataset_hash**: c56ea416229c80b1b52eeeb3d0cd396d29df2ab7ce8863ee56d1298684a66fa7
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 15
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 855.1432742372102
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 7 |
| bb_length | 179 |
| bb_std | 2.5611845543011436 |
| bbp_entry_threshold | 0.14414569087496756 |
| cooldown_time | 36832 |
| max_atr_pct_for_entry | 0.03929301184026377 |
| min_volume_quantile | 0.4994326915068018 |
| rsi_entry_threshold | 41.409543480736104 |
| rsi_length | 17 |
| stop_loss | 0.039435513855172306 |
| take_profit | 0.01186398538457305 |
| take_profit_order_type | MARKET |
| time_limit | 278987 |
| total_amount_quote | 855.1432742372102 |
| trailing_stop_activation | 0.0005346583769063748 |
| trailing_stop_delta | 0.012089841143535446 |
| trend_ema_length | 136 |
| use_trend_filter | False |
| volume_filter_window | 198 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 855.1432742372102 |
| Selected | 855.1432742372102 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 9.3322
- **Net PnL (quote)**: 79.8039
- **Sharpe Ratio**: 1.7949
- **Max Drawdown %**: 10.1998
- **Profit Factor**: 1.5715103193535653
- **Trade Count**: 76
- **Total Fees (quote)**: 24.6490
- **Maker Fees**: 12.3141
- **Taker Fees**: 12.3350
- **Fee Drag %**: 2.8824

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0020
- **PnL Component**: 0.0892
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0765
- **Fee Drag Component**: -0.0144
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.89 | 1.53 | 10.54 | -0.0250 |
| fees_2x | 6.45 | 1.27 | 10.89 | -0.0482 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 9.06 | 1.74 | 10.33 | -0.0054 |
| very_low_liquidity | 5.32 | 1.06 | 12.30 | -0.0547 |
| high_slippage | 5.73 | 1.15 | 11.04 | -0.0418 |
| extreme_slippage | -2.70 | -0.57 | 11.08 | -0.1736 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 7.17 | 1.36 | 10.83 | -0.0264 |
| spread_widen_25bps | 9.40 | 1.43 | 10.43 | -0.0029 |
| thin_book | -2.35 | -1.07 | 3.96 | -0.2268 |
| very_thin_book | -3.45 | -1.61 | 4.10 | -0.2505 |
| entry_spread_stress | 6.55 | 1.23 | 10.91 | -0.0328 |
| combined_market_deterioration | -2.82 | -1.29 | 4.05 | -0.2252 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8765
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0036)
- **Best holdout score**: -0.1077 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0010 | -0.1077 | 4.06 | 1.67 | 17 |
| 1 | -0.1351 | -0.1582 | -1.00 | 2.35 | 18 |
| 2 | -0.1372 | -0.2040 | -2.70 | 4.00 | 14 |
| 3 | -0.1493 | -0.1882 | -1.21 | 2.40 | 11 |
| 4 | -0.1513 | -0.1625 | 1.71 | 1.32 | 8 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51806
- **Expected rows**: 51890
- **Missing rows**: 84
- **Forward-fill count**: 77
- **Forward-fill fraction**: 0.001486314326525885
- **Longest gap (seconds)**: 13800

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1536 <= 0
- **Objective score**: -0.15357590481387884
- **PnL %**: 1.2217143116610425
- **Trade count**: 9

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

- **Sensitivity penalty**: 0.375
- **Baseline score**: 0.04168674409965224
- **Sign flips**: 1
- **Collapse count**: 2
- **Perturbations**: 8
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| stop_loss | 0.0200, 0.0632 |
| take_profit | 0.0417, 0.0417 |
| cooldown_time | -1000.0000, 0.0281 |
| total_amount_quote | 0.0413, 0.0422 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.426456368033859
- **Max CV**: 0.6096842196637131
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3235 | 0.015296980089564413 | 0.07549693862627278 | 0.05444466086112323 |
| take_profit | 0.6097 | 0.005904697567467772 | 0.038665866574977927 | 0.0189394428654428 |
| cooldown_time | 0.3864 | 15093.0 | 84770.0 | 46032.8 |
| total_amount_quote | 0.3863 | 293.98342748993576 | 920.2586763037435 | 667.3497965906746 |

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
| recent_objective | > 0 | -0.15357590481387884 | FAIL |
| recent_pnl | >= 0 | 1.2217143116610425 | PASS |
| recent_trades | >= 5 | 9 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.375 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.10769354150382968 |
| walkforward | SKIPPED |  |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.375 |
| recent_28d | FAIL | score=-0.15357590481387884, pnl=1.2217143116610425, trades=9, reason=recent objective score -0.1536 <= 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.426456368033859 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51806 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1536 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | false | NOT_RUN | — | — | — | not executed |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51806
- **Pre-release bars**: 43825
- **Dev bars**: 35060
- **Holdout bars**: 8765
- **Recent 28d bars**: 7981
- **Recent window start**: 1774039500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-17T22:08:16.618320+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 249
