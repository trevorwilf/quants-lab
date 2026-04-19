# PMM Dynamic Optimization Report: nonkyc_INJ-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:31:15 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:31:15.359581+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 33 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: INJ-USDT
- **interval**: 5m+4h
- **n_candles**: 55279
- **dataset_hash**: 9fc38cf9debaa4f75c9fd0fd6cf24452974bd428a1b88eda6847f23676d45eea
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 269.90069778301563
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 60935 |
| min_volume_quantile | 0.265429383000454 |
| regime_adx_length | 7 |
| regime_adx_threshold | 16.822971426928895 |
| regime_ema_fast | 88 |
| regime_ema_slow | 103 |
| stop_loss | 0.04615033717035634 |
| take_profit | 0.038090756017081374 |
| take_profit_order_type | MARKET |
| time_limit | 289704 |
| total_amount_quote | 269.90069778301563 |
| trailing_stop_activation | 0.0024650641927280725 |
| trailing_stop_delta | 0.0033485217626621783 |
| volume_filter_window | 323 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 269.90069778301563 |
| Selected | 269.90069778301563 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.5117
- **Net PnL (quote)**: -4.0801
- **Sharpe Ratio**: -0.5061
- **Max Drawdown %**: 3.5834
- **Profit Factor**: 0.6108146299417522
- **Trade Count**: 87
- **Total Fees (quote)**: 5.8639
- **Maker Fees**: 2.0395
- **Taker Fees**: 3.8244
- **Fee Drag %**: 2.1726

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0532
- **PnL Component**: -0.0152
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0269
- **Fee Drag Component**: -0.0109
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -1.04 | -2.14 | 2.97 | 32 | -0.2878 | n/a |
| 4 | -3.77 | -9.24 | 4.01 | 16 | -0.4581 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.90 | -0.29 | 3.04 | -0.0954 |
| fees_2x | -1.13 | -0.40 | 3.12 | -0.1098 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.31 | -0.73 | 4.25 | -0.0678 |
| very_low_liquidity | -2.07 | -2.56 | 2.29 | -0.0396 |
| high_slippage | -1.87 | -0.64 | 3.63 | -0.0571 |
| extreme_slippage | -0.86 | -0.27 | 3.00 | -0.0867 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.83 | -0.62 | 3.56 | -0.0563 |
| spread_widen_25bps | -0.37 | -0.07 | 3.65 | -0.0925 |
| thin_book | -2.31 | -3.59 | 2.60 | -0.2093 |
| very_thin_book | -4.95 | -4.16 | 4.95 | -0.5093 |
| entry_spread_stress | -3.68 | -1.14 | 5.25 | -0.0945 |
| combined_market_deterioration | -1.04 | -0.35 | 3.53 | -0.1095 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 9449
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0019)
- **Trend**: ranging (efficiency: 0.0008)
- **Best holdout score**: -0.1111 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0266 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -0.2703 | -0.1111 | -1.52 | 3.27 | 34 |
| 2 | -0.2898 | -0.1668 | -2.51 | 3.16 | 22 |
| 3 | -0.3317 | -0.1480 | -4.29 | 7.33 | 51 |
| 4 | -0.3447 | -0.1782 | -1.03 | 3.21 | 17 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 55279
- **Expected rows**: 55311
- **Missing rows**: 32
- **Forward-fill count**: 2532
- **Forward-fill fraction**: 0.04580401237359576
- **Longest gap (seconds)**: 1200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1616 <= 0; recent PnL -0.2106% < 0
- **Objective score**: -0.16160666050446876
- **PnL %**: -0.2106464248259942
- **Trade count**: 37

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1776 <= 0; recent PnL -0.2106% < 0
- **Objective score**: -0.17757291285310073
- **PnL %**: -0.2106464248259942
- **Trade count**: 37

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2093 <= 0; recent PnL -0.2106% < 0
- **Objective score**: -0.20934388756707117
- **PnL %**: -0.2106464248259942
- **Trade count**: 37

## Sensitivity Analysis

- **Sensitivity penalty**: 0.3
- **Baseline score**: -0.05236970580613373
- **Sign flips**: 0
- **Collapse count**: 6
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.5494, -1000.0000 |
| regime_ema_slow | -0.5494, -1000.0000 |
| regime_adx_length | -0.0524, -0.0524 |
| regime_adx_threshold | -0.0524, -0.0524 |
| volume_filter_window | -0.0524, -0.0524 |
| min_volume_quantile | -0.0524, -0.0524 |
| stop_loss | -0.0582, -0.0465 |
| take_profit | -0.0524, -0.0524 |
| cooldown_time | -0.1121, -0.1163 |
| total_amount_quote | -0.0547, -0.0496 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3733812432867113
- **Max CV**: 0.6758241287097172
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.1497 | 0.024470777852210274 | 0.038816698459502745 | 0.030934722353889117 |
| take_profit | 0.6758 | 0.01214187560351559 | 0.07958269347811936 | 0.0325806208032242 |
| cooldown_time | 0.4019 | 16288.0 | 83307.0 | 55719.7 |
| total_amount_quote | 0.2661 | 461.75290698207925 | 908.0633455210922 | 620.7076774371751 |

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
| recent_objective | > 0 | -0.16160666050446876 | FAIL |
| recent_pnl | >= 0 | -0.2106464248259942 | FAIL |
| recent_trades | >= 5 | 37 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.3 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 10 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.3 |
| recent_28d | FAIL | score=-0.16160666050446876, pnl=-0.2106464248259942, trades=37, reason=recent objective score -0.1616 <= 0; recent PnL -0.2106% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.17757291285310073, pnl=-0.2106464248259942, trades=37, reason=recent objective score -0.1776 <= 0; recent PnL -0.2106% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.20934388756707117, pnl=-0.2106464248259942, trades=37, reason=recent objective score -0.2093 <= 0; recent PnL -0.2106% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3733812432867113 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 55279 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1616 <= 0; recent PnL -0.2106% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1776 <= 0; recent PnL -0.2106% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2093 <= 0; recent PnL -0.2106% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 55279
- **Pre-release bars**: 47246
- **Dev bars**: 37797
- **Holdout bars**: 9449
- **Recent 28d bars**: 8033
- **Recent window start**: 1774111800

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:31:15.359581+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 33
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
