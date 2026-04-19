# PMM Dynamic Optimization Report: mexc_XLM-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 10:54:25 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T10:54:25.184300+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 8751 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XLM-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 88abb67a0750f78a02c4d0f9c4658cdece522195bad9a6d73e79e6d45394527e
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 859.541045601858
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 7 |
| bb_length | 32 |
| bb_std | 1.6646274419866025 |
| bbp_entry_threshold | 0.35624443310618714 |
| cooldown_time | 76376 |
| max_atr_pct_for_entry | 0.014794419251541359 |
| min_volume_quantile | 0.548333538116807 |
| rsi_entry_threshold | 43.35154458529193 |
| rsi_length | 9 |
| stop_loss | 0.028041022349561046 |
| take_profit | 0.013145109670990132 |
| take_profit_order_type | LIMIT |
| time_limit | 156950 |
| total_amount_quote | 859.541045601858 |
| trailing_stop_activation | 0.0014307304371364658 |
| trailing_stop_delta | 0.005472152247879697 |
| trend_ema_length | 196 |
| use_trend_filter | False |
| volume_filter_window | 51 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 859.541045601858 |
| Selected | 859.541045601858 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 8.3209
- **Net PnL (quote)**: 71.5214
- **Sharpe Ratio**: 3.6432
- **Max Drawdown %**: 1.5156
- **Profit Factor**: 4887.545298393624
- **Trade Count**: 51
- **Total Fees (quote)**: 13.4258
- **Maker Fees**: 6.7044
- **Taker Fees**: 6.7214
- **Fee Drag %**: 1.5620

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0606
- **PnL Component**: 0.0799
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0114
- **Fee Drag Component**: -0.0078
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -2.89 | -8.35 | 2.99 | 3 | -1000.0000 | n/a |
| 1 | 0.03 | 1.63 | 0.06 | 3 | -1000.0000 | n/a |
| 2 | 1.13 | 4.70 | 0.93 | 7 | -0.1689 | n/a |
| 3 | 0.08 | 0.76 | 0.59 | 3 | -1000.0000 | n/a |
| 4 | 2.10 | 4.53 | 0.80 | 7 | -0.1582 | n/a |
| 5 | 1.00 | 4.64 | 0.72 | 6 | -0.1721 | n/a |
| 6 | 1.14 | 7.84 | 0.00 | 3 | -1000.0000 | n/a |
| 7 | 0.09 | 0.48 | 0.96 | 2 | -1000.0000 | n/a |
| 8 | 0.07 | 0.62 | 0.61 | 3 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.54 | 3.32 | 1.53 | 0.0494 |
| fees_2x | 6.76 | 2.99 | 1.54 | 0.0381 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 8.72 | 3.12 | 1.92 | 0.0610 |
| very_low_liquidity | 8.40 | 2.63 | 1.93 | 0.0578 |
| high_slippage | 6.37 | 2.85 | 1.54 | 0.0422 |
| extreme_slippage | 2.86 | 1.30 | 1.67 | -0.0368 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 7.33 | 3.17 | 1.57 | 0.0511 |
| spread_widen_25bps | -1.50 | -0.75 | 2.86 | -0.1864 |
| thin_book | 3.49 | 1.71 | 2.06 | -0.1198 |
| very_thin_book | -2.89 | -2.06 | 2.91 | -1000.0000 |
| entry_spread_stress | 7.16 | 2.99 | 1.60 | 0.0492 |
| combined_market_deterioration | 2.95 | 1.36 | 2.18 | -0.0773 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0032)
- **Trend**: ranging (efficiency: 0.0001)
- **Best holdout score**: -0.1443 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9697 | -0.1534 | 1.31 | 0.22 | 9 |
| 1 | -0.1498 | -1000.0000 | -1.34 | 1.99 | 2 |
| 2 | -0.1500 | -0.1720 | 0.61 | 0.17 | 6 |
| 3 | -0.1500 | -0.1443 | 4.11 | 1.95 | 8 |
| 4 | -0.1512 | -1000.0000 | 0.56 | 1.62 | 1 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 29
- **Forward-fill fraction**: 0.0005594027892980459
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.1505689526948983
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.1505689526948983
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.38461538461538464
- **Baseline score**: 0.07311743247434113
- **Sign flips**: 3
- **Collapse count**: 7
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | 0.0405, 0.0525 |
| bb_std | 0.0683, 0.0413 |
| bbp_entry_threshold | 0.0560, 0.0196 |
| rsi_length | -0.0140, 0.0706 |
| rsi_entry_threshold | -0.0042, 0.0021 |
| trend_ema_length | 0.0731, 0.0731 |
| max_atr_pct_for_entry | 0.0731, 0.0731 |
| volume_filter_window | 0.0687, 0.0648 |
| min_volume_quantile | 0.0310, 0.0754 |
| stop_loss | 0.0731, 0.0731 |
| take_profit | 0.0731, 0.0731 |
| cooldown_time | 0.0124, -0.2176 |
| total_amount_quote | 0.0735, 0.0727 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2405852974924884
- **Max CV**: 0.4047234519882734
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3531 | 0.01693885936362645 | 0.03881892934783363 | 0.02502666210996498 |
| take_profit | 0.1267 | 0.005542024669638408 | 0.007821324977169858 | 0.00639915569033032 |
| cooldown_time | 0.4047 | 22898.0 | 84722.0 | 54225.9 |
| total_amount_quote | 0.0778 | 773.4014256030985 | 962.1050153583853 | 854.9563793525964 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.1505689526948983 | PASS |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.38461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1534122437735402 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.38461538461538464 |
| recent_28d | FAIL | score=-1000.0, pnl=0.1505689526948983, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.1505689526948983, trades=2, reason=recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2405852974924884 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T10:54:25.184300+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 8751
- **validation_status**: validated_fail
