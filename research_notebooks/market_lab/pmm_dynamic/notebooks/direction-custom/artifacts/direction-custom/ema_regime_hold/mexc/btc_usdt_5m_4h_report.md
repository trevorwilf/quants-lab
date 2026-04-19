# PMM Dynamic Optimization Report: mexc_BTC-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 16:56:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T16:56:34.771355+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 318 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BTC-USDT
- **interval**: 5m+4h
- **n_candles**: 103831
- **dataset_hash**: 7c8989067cb7f78c625db49f73b4c5c61a604ab716c66d122aba5bf5def21d56
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 859.0951251730227
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 17019 |
| min_volume_quantile | 0.1428217510373259 |
| regime_adx_length | 17 |
| regime_adx_threshold | 25.644024630531003 |
| regime_ema_fast | 19 |
| regime_ema_slow | 99 |
| stop_loss | 0.054245132735726106 |
| take_profit | 0.020220553249335818 |
| take_profit_order_type | MARKET |
| time_limit | 8084 |
| total_amount_quote | 859.0951251730227 |
| trailing_stop_activation | 0.0001897746124564962 |
| trailing_stop_delta | 0.024608551213318175 |
| volume_filter_window | 111 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 859.0951251730227 |
| Selected | 859.0951251730227 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1158
- **Net PnL (quote)**: -9.5855
- **Sharpe Ratio**: -0.9336
- **Max Drawdown %**: 1.5523
- **Profit Factor**: 0.5062509949150917
- **Trade Count**: 51
- **Total Fees (quote)**: 9.6145
- **Maker Fees**: 4.8072
- **Taker Fees**: 4.8072
- **Fee Drag %**: 1.1191

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0285
- **PnL Component**: -0.0112
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0116
- **Fee Drag Component**: -0.0056
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1863**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.85 | -5.78 | 0.85 | 11 | -0.1825 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | -1.15 | -5.40 | 1.15 | 28 | -0.1132 | n/a |
| 3 | -1.74 | -8.01 | 2.01 | 16 | -0.1711 | n/a |
| 4 | -0.56 | -4.48 | 0.75 | 17 | -0.1460 | n/a |
| 5 | -0.52 | -3.29 | 1.51 | 13 | -0.1666 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | -1.27 | -9.90 | 1.33 | 13 | -0.2513 | n/a |
| 8 | -1.20 | -7.69 | 1.20 | 30 | -0.1056 | n/a |
| 9 | -1.48 | -7.76 | 1.97 | 17 | -0.1654 | n/a |
| 10 | -2.60 | -11.31 | 2.60 | 9 | -0.2240 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -1.33 | -6.01 | 1.61 | 17 | -0.1599 | n/a |
| 16 | -1.70 | -10.35 | 1.70 | 9 | -0.2158 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | -1.80 | -6.16 | 2.07 | 12 | -0.2245 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.03 | -0.97 | 1.71 | -0.0774 |
| fees_2x | -1.03 | -1.53 | 1.50 | -0.1476 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -1.12 | -0.93 | 1.55 | -0.0285 |
| very_low_liquidity | -1.12 | -0.93 | 1.55 | -0.0285 |
| high_slippage | -1.01 | -1.70 | 1.34 | -0.1663 |
| extreme_slippage | -1.87 | -1.30 | 2.37 | -0.1986 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.34 | -1.52 | 2.17 | -0.1764 |
| spread_widen_25bps | -1.66 | -1.72 | 2.34 | -0.1916 |
| thin_book | -1.26 | -1.24 | 1.60 | -0.0815 |
| very_thin_book | -1.03 | -1.41 | 1.70 | -0.2858 |
| entry_spread_stress | -1.61 | -1.72 | 1.89 | -0.1996 |
| combined_market_deterioration | -1.12 | -1.94 | 1.26 | -0.2452 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19210
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0022)
- **Trend**: ranging (efficiency: 0.0152)
- **Best holdout score**: -0.1270 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0142 | -0.2157 | -1.70 | 1.70 | 9 |
| 1 | -0.1445 | -0.2332 | -1.14 | 1.36 | 8 |
| 2 | -0.1747 | -0.2046 | -1.15 | 1.16 | 8 |
| 3 | -0.1801 | -0.1270 | -1.29 | 2.71 | 29 |
| 4 | -0.1801 | -0.1916 | -1.03 | 1.35 | 13 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103831
- **Expected rows**: 104119
- **Missing rows**: 288
- **Forward-fill count**: 787
- **Forward-fill fraction**: 0.007579624582253855
- **Longest gap (seconds)**: 8400

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.0408539972098914
- **Trade count**: 2

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.0408539972098914
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1972 <= 0; recent PnL -1.0252% < 0
- **Objective score**: -0.19721908865456955
- **PnL %**: -1.025237145520873
- **Trade count**: 15

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35
- **Baseline score**: -0.028472202720012024
- **Sign flips**: 0
- **Collapse count**: 7
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0285, -0.0285 |
| regime_ema_slow | -0.0285, -0.0285 |
| regime_adx_length | -0.1968, -0.1004 |
| regime_adx_threshold | -0.1968, -0.1539 |
| volume_filter_window | -0.0285, -0.0315 |
| min_volume_quantile | -0.0285, -0.1553 |
| stop_loss | -0.0285, -0.0285 |
| take_profit | -0.0285, -0.0285 |
| cooldown_time | -0.0961, -0.0632 |
| total_amount_quote | -0.0285, -0.0294 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.4906017560225254
- **Max CV**: 0.7789491550456684
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2257 | 0.0485899625597581 | 0.09099928791179088 | 0.07216303815437297 |
| take_profit | 0.7789 | 0.01352627656233505 | 0.0940956612522387 | 0.0314351165761347 |
| cooldown_time | 0.7203 | 1089.0 | 22975.0 | 10028.7 |
| total_amount_quote | 0.2375 | 433.8730073619321 | 956.3323960763223 | 772.3208519814466 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -2.0408539972098914 | FAIL |
| recent_trades | >= 5 | 2 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.35 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.21568252797761986 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.35 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.0408539972098914, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-2.0408539972098914, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-0.19721908865456955, pnl=-1.025237145520873, trades=15, reason=recent objective score -0.1972 <= 0; recent PnL -1.0252% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.4906017560225254 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103831 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.0409% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1972 <= 0; recent PnL -1.0252% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103831
- **Pre-release bars**: 96054
- **Dev bars**: 76844
- **Holdout bars**: 19210
- **Recent 28d bars**: 7777
- **Recent window start**: 1774106700

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T16:56:34.771355+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 318
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
