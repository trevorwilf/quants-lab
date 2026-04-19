# PMM Dynamic Optimization Report: mexc_RENDER-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:11:24 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:11:24.158883+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 31 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: RENDER-USDT
- **interval**: 5m+4h
- **n_candles**: 103800
- **dataset_hash**: 7c3b0f4e1e19fad486d9dd04de38754d7c37125c10c6fe5837fc6751b494abed
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 30.462568020071913
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 45337 |
| min_volume_quantile | 0.2354281057237651 |
| regime_adx_length | 13 |
| regime_adx_threshold | 23.884158096596998 |
| regime_ema_fast | 66 |
| regime_ema_slow | 69 |
| stop_loss | 0.03623442956817806 |
| take_profit | 0.0564607361898114 |
| take_profit_order_type | LIMIT |
| time_limit | 89426 |
| total_amount_quote | 30.462568020071913 |
| trailing_stop_activation | 0.03408864840753661 |
| trailing_stop_delta | 0.019363745820859337 |
| volume_filter_window | 135 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 30.462568020071913 |
| Selected | 30.462568020071913 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 26.9681
- **Net PnL (quote)**: 8.2152
- **Sharpe Ratio**: 2.4801
- **Max Drawdown %**: 6.7066
- **Profit Factor**: 2.3228258494067675
- **Trade Count**: 18
- **Total Fees (quote)**: 0.2088
- **Maker Fees**: 0.1422
- **Taker Fees**: 0.0666
- **Fee Drag %**: 0.6855

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0567
- **PnL Component**: 0.2388
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0503
- **Fee Drag Component**: -0.0034
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1280
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 7.50 | 9.21 | 3.97 | 4 | -0.1426 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -3.71 | -9.04 | 4.80 | 2 | -1000.0000 | n/a |
| 16 | -3.25 | -2.50 | 5.76 | 2 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 13.59 | 6.12 | 9.56 | 16 | -0.3261 | n/a |
| 21 | -3.40 | -2.46 | 8.13 | 10 | -0.5927 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 26.62 | 2.45 | 6.73 | 0.0521 |
| fees_2x | 26.28 | 2.42 | 6.75 | 0.0475 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 26.97 | 2.48 | 6.71 | 0.0567 |
| very_low_liquidity | 26.97 | 2.48 | 6.71 | 0.0567 |
| high_slippage | 26.42 | 2.43 | 6.75 | 0.0521 |
| extreme_slippage | 25.33 | 2.33 | 6.85 | 0.0427 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 26.67 | 2.45 | 6.71 | 0.0544 |
| spread_widen_25bps | 25.19 | 2.31 | 6.38 | 0.0451 |
| thin_book | -1.82 | -0.43 | 7.03 | -0.4267 |
| very_thin_book | -1.82 | -0.45 | 7.03 | -0.4267 |
| entry_spread_stress | 26.52 | 2.42 | 6.71 | 0.0532 |
| combined_market_deterioration | 33.90 | 3.13 | 6.24 | 0.1117 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19147
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0047)
- **Trend**: ranging (efficiency: 0.0082)
- **Best holdout score**: -0.1813 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9716 | -0.2404 | -1.38 | 4.38 | 4 |
| 1 | -1000.0000 | -0.2743 | -3.25 | 9.23 | 23 |
| 2 | -1000.0000 | -0.2085 | -2.03 | 8.13 | 19 |
| 3 | -1000.0000 | -1000.0000 | -1.19 | 1.65 | 2 |
| 4 | -1000.0000 | -0.1813 | -1.20 | 4.71 | 17 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103800
- **Expected rows**: 103801
- **Missing rows**: 1
- **Forward-fill count**: 79
- **Forward-fill fraction**: 0.0007610789980732177
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.5268 <= 0; recent PnL -2.7364% < 0
- **Objective score**: -0.5267566396126194
- **PnL %**: -2.7364439493154906
- **Trade count**: 11

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.4145% < 0; recent trades 3 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.4145458799742587
- **Trade count**: 3

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.5508% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.550810047716194
- **Trade count**: 1

## Sensitivity Analysis

- **Sensitivity penalty**: 0.7777777777777778
- **Baseline score**: 0.0447970290000228
- **Sign flips**: 7
- **Collapse count**: 7
- **Perturbations**: 20
- **Rejected**: 2

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -1000.0000 |
| regime_ema_slow | -0.0036, -1000.0000 |
| regime_adx_length | 0.1030, 0.0529 |
| regime_adx_threshold | -0.4267, -0.0571 |
| volume_filter_window | 0.0424, 0.0448 |
| min_volume_quantile | 0.0424, 0.0448 |
| stop_loss | -0.0847, 0.2287 |
| take_profit | 0.0817, 0.0413 |
| cooldown_time | -0.4267, -0.0940 |
| total_amount_quote | 0.0488, 0.0448 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: False
- **Mean CV**: 0.5755714253901677
- **Max CV**: 0.7234175758948191
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4708 | 0.022961564713937427 | 0.0825158425491216 | 0.04414834791047861 |
| take_profit | 0.6187 | 0.01645477416780652 | 0.07948998901397729 | 0.037266436929498895 |
| cooldown_time | 0.7234 | 4806.0 | 83356.0 | 36402.3 |
| total_amount_quote | 0.4893 | 142.22499629651378 | 670.0304205910417 | 380.94402331641834 |

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
- sensitivity_stable: **FAIL**
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.5267566396126194 | FAIL |
| recent_pnl | >= 0 | -2.7364439493154906 | FAIL |
| recent_trades | >= 5 | 11 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.7777777777777778 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2404411484744598 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.7777777777777778 |
| recent_28d | FAIL | score=-0.5267566396126194, pnl=-2.7364439493154906, trades=11, reason=recent objective score -0.5268 <= 0; recent PnL -2.7364% < 0 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-2.4145458799742587, trades=3, reason=recent objective score -1000.0000 <= 0; recent PnL -2.4145% < 0; recent trades 3 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-2.550810047716194, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.5508% < 0; recent trades 1 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103800 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.5268 <= 0; recent PnL -2.7364% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.4145% < 0; recent trades 3 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.5508% < 0; recent trades 1 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103800
- **Pre-release bars**: 95736
- **Dev bars**: 76589
- **Holdout bars**: 19147
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:11:24.158883+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 31
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
