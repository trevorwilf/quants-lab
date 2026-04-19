# PMM Dynamic Optimization Report: nonkyc_BDX-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 12:45:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T12:45:34.595878+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 4114 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BDX-USDT
- **interval**: 5m
- **n_candles**: 51898
- **dataset_hash**: 96b55ffb9d511093c868669c1ea9f8d08ed3d0e5bd3758d4da971d5d41947b7d
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 689.878317864271
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 28 |
| bb_length | 109 |
| bb_std | 1.6630077626631958 |
| bbp_entry_threshold | 0.3001747589443551 |
| cooldown_time | 53981 |
| max_atr_pct_for_entry | 0.020935043571370424 |
| min_volume_quantile | 0.00042630815216022563 |
| rsi_entry_threshold | 38.56441297107192 |
| rsi_length | 30 |
| stop_loss | 0.02636337951522483 |
| take_profit | 0.008866268638309045 |
| take_profit_order_type | MARKET |
| time_limit | 273791 |
| total_amount_quote | 689.878317864271 |
| trailing_stop_activation | 0.008880831680635973 |
| trailing_stop_delta | 0.005221465743470969 |
| trend_ema_length | 331 |
| use_trend_filter | True |
| volume_filter_window | 404 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 689.878317864271 |
| Selected | 689.878317864271 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.6508
- **Net PnL (quote)**: 52.7814
- **Sharpe Ratio**: 1.5524
- **Max Drawdown %**: 2.0310
- **Profit Factor**: 4.697381744607684
- **Trade Count**: 373
- **Total Fees (quote)**: 11.7754
- **Maker Fees**: 4.1517
- **Taker Fees**: 7.6237
- **Fee Drag %**: 1.7069

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0390
- **PnL Component**: 0.0737
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0152
- **Fee Drag Component**: -0.0085
- **Inventory Component**: -0.0108
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.74 | 5.93 | 0.46 | 87 | 0.0015 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -1.60 | -8.53 | 2.21 | 81 | -0.2487 | n/a |
| 4 | 0.53 | 5.38 | 0.24 | 55 | 0.0019 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | -1.14 | -2.34 | 1.99 | 70 | -0.4914 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.79 | 1.41 | 2.16 | 0.0257 |
| fees_2x | 5.94 | 1.25 | 2.33 | 0.0121 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 5.02 | 1.05 | 3.35 | -0.0255 |
| very_low_liquidity | 3.57 | 0.78 | 4.75 | -0.0378 |
| high_slippage | 7.37 | 1.51 | 2.06 | 0.0362 |
| extreme_slippage | 6.82 | 1.42 | 2.16 | 0.0303 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 7.55 | 1.53 | 2.04 | 0.0379 |
| spread_widen_25bps | 6.64 | 1.35 | 2.55 | 0.0229 |
| thin_book | -2.23 | -4.00 | 2.36 | -0.3387 |
| very_thin_book | 0.00 | 0.00 | 0.00 | -1000.0000 |
| entry_spread_stress | 7.50 | 1.52 | 2.07 | 0.0373 |
| combined_market_deterioration | -1.61 | -3.19 | 1.82 | -0.0514 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0016)
- **Trend**: ranging (efficiency: 0.0005)
- **Best holdout score**: -0.3175 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9805 | -0.3175 | -1.14 | 1.99 | 70 |
| 1 | 0.0002 | -0.4129 | -1.24 | 2.12 | 28 |
| 2 | 0.0001 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -0.0001 | -0.4253 | -1.51 | 1.99 | 27 |
| 4 | -0.0002 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51898
- **Expected rows**: 51899
- **Missing rows**: 1
- **Forward-fill count**: 1868
- **Forward-fill fraction**: 0.03599367991059386
- **Longest gap (seconds)**: 600

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

- **Sensitivity penalty**: 0.46153846153846156
- **Baseline score**: 0.02468129744007288
- **Sign flips**: 5
- **Collapse count**: 7
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0216, 0.0098 |
| bb_std | 0.0247, 0.0234 |
| bbp_entry_threshold | 0.0112, 0.0216 |
| rsi_length | 0.0560, -0.0654 |
| rsi_entry_threshold | -0.3200, -0.3549 |
| trend_ema_length | -0.0448, 0.0674 |
| max_atr_pct_for_entry | 0.0247, 0.0247 |
| volume_filter_window | 0.0247, 0.0247 |
| min_volume_quantile | 0.0247, 0.0247 |
| stop_loss | 0.0225, 0.0161 |
| take_profit | 0.0248, 0.0392 |
| cooldown_time | 0.0247, 0.0223 |
| total_amount_quote | -0.0001, 0.0372 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2554296569750578
- **Max CV**: 0.45862531636332915
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4586 | 0.016341554235632494 | 0.07460744085076872 | 0.03616955480707876 |
| take_profit | 0.2867 | 0.006368856706873707 | 0.014286601461225897 | 0.008144682496818626 |
| cooldown_time | 0.1282 | 53981.0 | 84521.0 | 70921.0 |
| total_amount_quote | 0.1482 | 652.8223462235169 | 990.2327654057973 | 818.3990159201493 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.46153846153846156 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.31753058631148445 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.46153846153846156 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2554296569750578 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51898 |  |
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

- **Full bars**: 51898
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8064
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T12:45:34.595878+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 4114
- **validation_status**: validated_fail
