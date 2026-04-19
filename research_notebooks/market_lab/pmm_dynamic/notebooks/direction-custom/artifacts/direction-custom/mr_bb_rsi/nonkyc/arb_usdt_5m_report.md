# PMM Dynamic Optimization Report: nonkyc_ARB-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 11:59:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T11:59:05.761579+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 7558 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ARB-USDT
- **interval**: 5m
- **n_candles**: 51898
- **dataset_hash**: 0ddb7c80b23e1cb135b1340caaf3f63cc172f2df96ebf4dc1413ef5bd5939c21
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 898.786663616042
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 26 |
| bb_length | 131 |
| bb_std | 2.6848875985034333 |
| bbp_entry_threshold | 0.11256064257014534 |
| cooldown_time | 36340 |
| max_atr_pct_for_entry | 0.037997852114332605 |
| min_volume_quantile | 0.31566595689646254 |
| rsi_entry_threshold | 46.05777807646122 |
| rsi_length | 9 |
| stop_loss | 0.06400892531011378 |
| take_profit | 0.006319296619522782 |
| take_profit_order_type | MARKET |
| time_limit | 105899 |
| total_amount_quote | 898.786663616042 |
| trailing_stop_activation | 0.004165826579722269 |
| trailing_stop_delta | 0.00024039478330992723 |
| trend_ema_length | 390 |
| use_trend_filter | True |
| volume_filter_window | 476 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 898.786663616042 |
| Selected | 898.786663616042 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 1.4172
- **Net PnL (quote)**: 12.7372
- **Sharpe Ratio**: 0.4276
- **Max Drawdown %**: 3.6540
- **Profit Factor**: 1.5202288464401883
- **Trade Count**: 343
- **Total Fees (quote)**: 27.8607
- **Maker Fees**: 10.0046
- **Taker Fees**: 17.8561
- **Fee Drag %**: 3.0998

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0292
- **PnL Component**: 0.0141
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0274
- **Fee Drag Component**: -0.0155
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0782**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -2.47 | -5.01 | 3.51 | 53 | -0.0552 | n/a |
| 1 | 0.21 | 0.72 | 1.72 | 51 | -0.0126 | n/a |
| 2 | 1.84 | 2.94 | 3.18 | 61 | -0.0088 | n/a |
| 3 | 0.22 | 1.93 | 0.24 | 25 | -0.1012 | n/a |
| 4 | 0.27 | 1.21 | 1.03 | 69 | -0.0068 | n/a |
| 5 | -1.80 | -5.22 | 2.48 | 40 | -0.2718 | n/a |
| 6 | -1.04 | -4.85 | 1.17 | 15 | -0.3207 | n/a |
| 7 | 0.07 | 0.46 | 0.61 | 28 | -0.0935 | n/a |
| 8 | -2.34 | -9.20 | 2.73 | 77 | -0.0465 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.13 | 0.02 | 3.74 | -0.0530 |
| fees_2x | -1.68 | -0.39 | 3.82 | -0.1025 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.72 | -0.38 | 5.29 | -0.0818 |
| very_low_liquidity | -3.42 | -1.36 | 4.04 | -0.0701 |
| high_slippage | 0.92 | 0.30 | 3.67 | -0.0343 |
| extreme_slippage | -0.07 | 0.04 | 3.70 | -0.0444 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 1.80 | 0.50 | 3.69 | -0.0258 |
| spread_widen_25bps | 1.33 | 0.38 | 3.74 | -0.0308 |
| thin_book | -1.28 | -0.48 | 4.28 | -0.0483 |
| very_thin_book | -2.99 | -3.04 | 3.18 | -0.0751 |
| entry_spread_stress | 1.70 | 0.47 | 3.69 | -0.0268 |
| combined_market_deterioration | -3.62 | -0.94 | 4.34 | -0.0828 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0033)
- **Trend**: ranging (efficiency: 0.0047)
- **Best holdout score**: -0.0459 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0146 | -0.3253 | -1.25 | 1.34 | 15 |
| 1 | -0.0082 | -0.3380 | -1.06 | 2.59 | 24 |
| 2 | -0.0083 | -0.2717 | -0.95 | 3.41 | 44 |
| 3 | -0.0087 | -0.0459 | 1.07 | 2.07 | 42 |
| 4 | -0.0098 | -0.0727 | -0.40 | 2.48 | 40 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51898
- **Expected rows**: 51899
- **Missing rows**: 1
- **Forward-fill count**: 146
- **Forward-fill fraction**: 0.0028132105283440595
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0458 <= 0; recent PnL -2.3388% < 0
- **Objective score**: -0.04578898966341832
- **PnL %**: -2.3388006529800367
- **Trade count**: 77

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2626 <= 0; recent PnL -2.7685% < 0
- **Objective score**: -0.2626472243890885
- **PnL %**: -2.7684551467940652
- **Trade count**: 33

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.7132 <= 0; recent PnL -3.1321% < 0
- **Objective score**: -0.7131925615655371
- **PnL %**: -3.1321109953591857
- **Trade count**: 11

## Sensitivity Analysis

- **Sensitivity penalty**: 0.11538461538461539
- **Baseline score**: -0.06918809576591609
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0774, -0.0982 |
| bb_std | -0.0809, -0.0996 |
| bbp_entry_threshold | -0.1338, -0.0692 |
| rsi_length | -0.0692, -0.0692 |
| rsi_entry_threshold | -0.0692, -0.0692 |
| trend_ema_length | -0.1391, -0.0782 |
| max_atr_pct_for_entry | -0.0692, -0.0692 |
| volume_filter_window | -0.0692, -0.0692 |
| min_volume_quantile | -0.0692, -0.0692 |
| stop_loss | -0.0698, -0.0686 |
| take_profit | -0.0692, -0.0692 |
| cooldown_time | -0.0692, -0.0692 |
| total_amount_quote | -0.0880, -0.1112 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3110324945939256
- **Max CV**: 0.5934517266445193
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2181 | 0.03659802608708265 | 0.07096223221972088 | 0.05362408867199551 |
| take_profit | 0.5935 | 0.005101640483174001 | 0.020892833968707603 | 0.008140691669428492 |
| cooldown_time | 0.3008 | 27862.0 | 71982.0 | 44807.2 |
| total_amount_quote | 0.1318 | 678.4489949225317 | 993.8751871484012 | 859.3002255724389 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.04578898966341832 | FAIL |
| recent_pnl | >= 0 | -2.3388006529800367 | FAIL |
| recent_trades | >= 5 | 77 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.11538461538461539 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.3253236986409376 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.11538461538461539 |
| recent_28d | FAIL | score=-0.04578898966341832, pnl=-2.3388006529800367, trades=77, reason=recent objective score -0.0458 <= 0; recent PnL -2.3388% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.2626472243890885, pnl=-2.7684551467940652, trades=33, reason=recent objective score -0.2626 <= 0; recent PnL -2.7685% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.7131925615655371, pnl=-3.1321109953591857, trades=11, reason=recent objective score -0.7132 <= 0; recent PnL -3.1321% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3110324945939256 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51898 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0458 <= 0; recent PnL -2.3388% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2626 <= 0; recent PnL -2.7685% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.7132 <= 0; recent PnL -3.1321% < 0 |
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
- **run_timestamp**: 2026-04-18T11:59:05.761579+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 7558
- **validation_status**: validated_fail
