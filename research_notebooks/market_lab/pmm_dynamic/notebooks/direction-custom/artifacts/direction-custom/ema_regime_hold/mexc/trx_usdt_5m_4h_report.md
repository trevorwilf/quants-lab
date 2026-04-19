# PMM Dynamic Optimization Report: mexc_TRX-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:15:47 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:15:47.695995+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 437 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: TRX-USDT
- **interval**: 5m+4h
- **n_candles**: 103799
- **dataset_hash**: 274cbcd48f0920bfe41d595b8d42eda7ea94a43fa0c9a811293ffd9e2c32f07c
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 239.98298449718337
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 76525 |
| min_volume_quantile | 0.24495296043511416 |
| regime_adx_length | 13 |
| regime_adx_threshold | 12.852677181802635 |
| regime_ema_fast | 70 |
| regime_ema_slow | 263 |
| stop_loss | 0.025781736450909525 |
| take_profit | 0.08524029144567172 |
| take_profit_order_type | LIMIT |
| time_limit | 261981 |
| total_amount_quote | 239.98298449718337 |
| trailing_stop_activation | 0.0011595255632958546 |
| trailing_stop_delta | 0.009351678898957631 |
| volume_filter_window | 323 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 239.98298449718337 |
| Selected | 239.98298449718337 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 7.8631
- **Net PnL (quote)**: 18.8701
- **Sharpe Ratio**: 1.4099
- **Max Drawdown %**: 2.9427
- **Profit Factor**: 3.6228603192724824
- **Trade Count**: 86
- **Total Fees (quote)**: 8.1648
- **Maker Fees**: 4.0797
- **Taker Fees**: 4.0851
- **Fee Drag %**: 3.4023

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0364
- **PnL Component**: 0.0757
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0221
- **Fee Drag Component**: -0.0170
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1856**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 6.45 | 6.29 | 1.45 | 9 | -0.3611 | n/a |
| 1 | 0.68 | 3.17 | 1.29 | 6 | -0.1801 | n/a |
| 2 | 0.37 | 3.99 | 0.19 | 6 | -0.1749 | n/a |
| 3 | 0.27 | 2.05 | 0.76 | 11 | -0.1609 | n/a |
| 4 | 0.22 | 1.37 | 0.33 | 8 | -0.1699 | n/a |
| 5 | -2.43 | -6.22 | 2.70 | 9 | -0.4607 | n/a |
| 6 | 0.42 | 2.62 | 0.80 | 10 | -0.1636 | n/a |
| 7 | 0.46 | 2.74 | 0.58 | 10 | -0.1617 | n/a |
| 8 | -0.80 | -3.68 | 1.12 | 3 | -1000.0000 | n/a |
| 9 | 0.12 | 0.95 | 0.66 | 3 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -0.04 | -1.05 | 0.20 | 6 | -0.4806 | n/a |
| 16 | -2.66 | -10.71 | 2.73 | 7 | -0.2210 | n/a |
| 17 | -1.27 | -5.06 | 1.96 | 3 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.37 | 1.72 | 0.76 | 12 | -0.2183 | n/a |
| 21 | 0.76 | 3.64 | 0.68 | 6 | -0.1745 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 6.16 | 1.12 | 3.05 | 0.0112 |
| fees_2x | 4.46 | 0.82 | 3.51 | -0.0169 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 7.86 | 1.41 | 2.94 | 0.0364 |
| very_low_liquidity | 7.86 | 1.41 | 2.94 | 0.0364 |
| high_slippage | 3.61 | 0.68 | 3.95 | -0.0154 |
| extreme_slippage | -1.12 | -0.67 | 2.64 | -0.1203 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.67 | -2.34 | 2.72 | -0.2322 |
| spread_widen_25bps | 3.68 | 0.59 | 5.02 | -0.2497 |
| thin_book | -2.61 | -2.66 | 2.66 | -1000.0000 |
| very_thin_book | -1.63 | -1.01 | 2.64 | -0.1637 |
| entry_spread_stress | -2.69 | -2.34 | 2.69 | -0.2378 |
| combined_market_deterioration | -2.80 | -2.71 | 2.80 | -0.2495 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19160
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0011)
- **Trend**: ranging (efficiency: 0.0035)
- **Best holdout score**: -0.1481 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9818 | -0.2207 | -2.66 | 2.73 | 7 |
| 1 | -0.1621 | -0.2546 | -3.09 | 3.09 | 10 |
| 2 | -0.1637 | -0.1481 | -1.03 | 1.29 | 19 |
| 3 | -0.1648 | -0.2119 | -2.19 | 2.26 | 7 |
| 4 | -0.1657 | -0.2437 | -3.58 | 3.66 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103799
- **Expected rows**: 103866
- **Missing rows**: 67
- **Forward-fill count**: 50
- **Forward-fill fraction**: 0.00048170020905789074
- **Longest gap (seconds)**: 18900

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1353 <= 0
- **Objective score**: -0.13530507559870317
- **PnL %**: 0.8846666916382787
- **Trade count**: 16

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1772 <= 0
- **Objective score**: -0.17723257485339267
- **PnL %**: 0.0555370847705945
- **Trade count**: 6

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1843 <= 0; recent trades 4 < 5
- **Objective score**: -0.1842743117351752
- **PnL %**: 0.07865151322496204
- **Trade count**: 4

## Sensitivity Analysis

- **Sensitivity penalty**: 0.1
- **Baseline score**: -0.03302475579224144
- **Sign flips**: 0
- **Collapse count**: 2
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0347, -0.0330 |
| regime_ema_slow | -0.0347, -0.0300 |
| regime_adx_length | -0.0337, -0.0335 |
| regime_adx_threshold | -0.0314, -0.0335 |
| volume_filter_window | -0.0316, -0.0330 |
| min_volume_quantile | -0.0330, -0.0316 |
| stop_loss | -0.0482, -0.0203 |
| take_profit | -0.0330, -0.0330 |
| cooldown_time | -0.1924, -0.0711 |
| total_amount_quote | -0.0330, -0.0330 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5125498346952816
- **Max CV**: 0.6413416107584569
- **Clustered params**: cooldown_time, total_amount_quote
- **Scattered params**: stop_loss, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.6413 | 0.021156936091933393 | 0.09400665221649922 | 0.041254947957028096 |
| take_profit | 0.6081 | 0.011570727854135663 | 0.08524029144567172 | 0.045386037697484796 |
| cooldown_time | 0.3176 | 10300.0 | 83356.0 | 66242.2 |
| total_amount_quote | 0.4831 | 200.01034153739488 | 910.6619604689051 | 556.8140165366322 |

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
| recent_objective | > 0 | -0.13530507559870317 | FAIL |
| recent_pnl | >= 0 | 0.8846666916382787 | PASS |
| recent_trades | >= 5 | 16 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.1 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.22068124380255186 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.1 |
| recent_28d | FAIL | score=-0.13530507559870317, pnl=0.8846666916382787, trades=16, reason=recent objective score -0.1353 <= 0 |
| recent_14d_info | FAIL | informational only; score=-0.17723257485339267, pnl=0.0555370847705945, trades=6, reason=recent objective score -0.1772 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.1842743117351752, pnl=0.07865151322496204, trades=4, reason=recent objective score -0.1843 <= 0; recent trades 4 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5125498346952816 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103799 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1353 <= 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1772 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1843 <= 0; recent trades 4 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103799
- **Pre-release bars**: 95801
- **Dev bars**: 76641
- **Holdout bars**: 19160
- **Recent 28d bars**: 7998
- **Recent window start**: 1774032300

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:15:47.695995+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 437
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
