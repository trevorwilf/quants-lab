# PMM Dynamic Optimization Report: nonkyc_LTC-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:26:28 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:26:28.069610+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 5720 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 51878
- **dataset_hash**: 5267b56f676c50f8632107178faed26ccc550fa8f4a2351ca0fe5b94f2e44d0d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 818.3655737955348
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 21 |
| bb_length | 126 |
| bb_std | 2.4418090040306444 |
| bbp_entry_threshold | 0.19903217378465785 |
| cooldown_time | 14368 |
| max_atr_pct_for_entry | 0.021102867248389546 |
| min_volume_quantile | 0.0071183572065639245 |
| rsi_entry_threshold | 41.49958548187952 |
| rsi_length | 9 |
| stop_loss | 0.027250481602098534 |
| take_profit | 0.005966993181049912 |
| take_profit_order_type | LIMIT |
| time_limit | 231394 |
| total_amount_quote | 818.3655737955348 |
| trailing_stop_activation | 0.024496826471316433 |
| trailing_stop_delta | 0.005741790545930743 |
| trend_ema_length | 361 |
| use_trend_filter | True |
| volume_filter_window | 341 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 818.3655737955348 |
| Selected | 818.3655737955348 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 6.4876
- **Net PnL (quote)**: 53.0920
- **Sharpe Ratio**: 1.7106
- **Max Drawdown %**: 3.2772
- **Profit Factor**: 3.1144963594181707
- **Trade Count**: 114
- **Total Fees (quote)**: 47.8160
- **Maker Fees**: 46.2247
- **Taker Fees**: 1.5913
- **Fee Drag %**: 5.8429

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0086
- **PnL Component**: 0.0629
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0246
- **Fee Drag Component**: -0.0292
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1674**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.01 | -3.11 | 1.95 | 17 | -0.1679 | n/a |
| 1 | 1.12 | 4.87 | 0.55 | 22 | -0.1086 | n/a |
| 2 | -0.18 | -0.62 | 1.11 | 9 | -0.1793 | n/a |
| 3 | 1.54 | 5.93 | 0.33 | 14 | -0.1356 | n/a |
| 4 | -3.07 | -9.74 | 3.07 | 3 | -1000.0000 | n/a |
| 5 | -0.05 | -0.12 | 1.25 | 22 | -0.1261 | n/a |
| 6 | 0.99 | 2.42 | 1.53 | 23 | -0.1167 | n/a |
| 7 | -2.09 | -5.79 | 2.22 | 12 | -0.4340 | n/a |
| 8 | -1.03 | -5.60 | 1.67 | 30 | -0.2396 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.57 | 0.97 | 3.67 | -0.0368 |
| fees_2x | 0.64 | 0.22 | 4.08 | -0.0831 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 6.14 | 1.67 | 3.27 | 0.0074 |
| very_low_liquidity | 5.01 | 1.41 | 3.31 | -0.0026 |
| high_slippage | 6.44 | 1.70 | 3.32 | 0.0078 |
| extreme_slippage | 6.34 | 1.67 | 3.41 | 0.0063 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 2.63 | 0.74 | 3.45 | -0.0290 |
| spread_widen_25bps | 2.63 | 0.70 | 3.52 | -0.0312 |
| thin_book | 6.26 | 2.03 | 2.42 | 0.0258 |
| very_thin_book | 1.78 | 0.99 | 2.49 | -0.1220 |
| entry_spread_stress | 2.64 | 0.73 | 3.47 | -0.0292 |
| combined_market_deterioration | 5.90 | 1.71 | 2.51 | 0.0051 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0046)
- **Best holdout score**: -0.0465 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9957 | -0.0465 | -1.52 | 2.28 | 55 |
| 1 | -0.1176 | -0.2201 | -2.25 | 2.85 | 7 |
| 2 | -0.1266 | -0.4169 | -3.27 | 3.60 | 5 |
| 3 | -0.1293 | -0.4239 | -3.35 | 4.34 | 5 |
| 4 | -0.1303 | -0.4949 | -3.83 | 4.25 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51878
- **Expected rows**: 51899
- **Missing rows**: 21
- **Forward-fill count**: 771
- **Forward-fill fraction**: 0.014861791125332511
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2061 <= 0; recent PnL -1.1689% < 0
- **Objective score**: -0.20610311053623181
- **PnL %**: -1.1689179399456846
- **Trade count**: 34

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4185 <= 0; recent PnL -1.6805% < 0
- **Objective score**: -0.41851540050236546
- **PnL %**: -1.6805214822333412
- **Trade count**: 16

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.5097 <= 0; recent PnL -0.5972% < 0
- **Objective score**: -0.5097005192496864
- **PnL %**: -0.5972216740016703
- **Trade count**: 28

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.21737279920607488
- **Sign flips**: 1
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0732, -0.2686 |
| bb_std | -0.1596, -0.2512 |
| bbp_entry_threshold | -0.2484, -0.2124 |
| rsi_length | -0.2174, -0.2547 |
| rsi_entry_threshold | -0.2148, -0.2736 |
| trend_ema_length | -0.2064, 0.0352 |
| max_atr_pct_for_entry | -0.2174, -0.2174 |
| volume_filter_window | -0.2174, -0.2174 |
| min_volume_quantile | -0.2174, -0.2174 |
| stop_loss | -0.1720, -0.2391 |
| take_profit | -0.2556, -0.0996 |
| cooldown_time | -0.2209, -0.2139 |
| total_amount_quote | -0.2088, -0.2174 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.27348197194670326
- **Max CV**: 0.5462896600558425
- **Clustered params**: stop_loss, take_profit, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3820 | 0.017474523864448758 | 0.05404576720042713 | 0.03440156207630989 |
| take_profit | 0.0923 | 0.005067089144296611 | 0.006642715677509321 | 0.005567949401762253 |
| cooldown_time | 0.5463 | 7027.0 | 85767.0 | 57235.6 |
| total_amount_quote | 0.0733 | 759.2227247620594 | 974.1578549958788 | 894.2143736868877 |

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
| recent_objective | > 0 | -0.20610311053623181 | FAIL |
| recent_pnl | >= 0 | -1.1689179399456846 | FAIL |
| recent_trades | >= 5 | 34 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.046548860840679794 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.20610311053623181, pnl=-1.1689179399456846, trades=34, reason=recent objective score -0.2061 <= 0; recent PnL -1.1689% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.41851540050236546, pnl=-1.6805214822333412, trades=16, reason=recent objective score -0.4185 <= 0; recent PnL -1.6805% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.5097005192496864, pnl=-0.5972216740016703, trades=28, reason=recent objective score -0.5097 <= 0; recent PnL -0.5972% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.27348197194670326 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51878 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2061 <= 0; recent PnL -1.1689% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4185 <= 0; recent PnL -1.6805% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.5097 <= 0; recent PnL -0.5972% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51878
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:26:28.069610+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 5720
- **validation_status**: validated_fail
