# PMM Dynamic Optimization Report: mexc_BNB-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 16:53:56 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T16:53:56.158919+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 29 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: BNB-USDT
- **interval**: 5m+4h
- **n_candles**: 103810
- **dataset_hash**: e0ec08a12b190ba943121ea3968cdd271aa929b13151cb22aa1298f15b245208
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 165.68446337759
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 84260 |
| min_volume_quantile | 0.5803622672606 |
| regime_adx_length | 18 |
| regime_adx_threshold | 13.157885622106722 |
| regime_ema_fast | 76 |
| regime_ema_slow | 96 |
| stop_loss | 0.07813259749146038 |
| take_profit | 0.02692412656578914 |
| take_profit_order_type | LIMIT |
| time_limit | 265499 |
| total_amount_quote | 165.68446337759 |
| trailing_stop_activation | 0.006724490614758733 |
| trailing_stop_delta | 0.000549345626451439 |
| volume_filter_window | 556 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 165.68446337759 |
| Selected | 165.68446337759 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 19.8841
- **Net PnL (quote)**: 32.9448
- **Sharpe Ratio**: 2.9316
- **Max Drawdown %**: 4.2254
- **Profit Factor**: 11.375128364036318
- **Trade Count**: 30
- **Total Fees (quote)**: 1.9289
- **Maker Fees**: 0.9609
- **Taker Fees**: 0.9679
- **Fee Drag %**: 1.1642

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0635
- **PnL Component**: 0.1814
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0317
- **Fee Drag Component**: -0.0058
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0800
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
| 7 | 0.58 | 7.86 | 0.02 | 2 | -1000.0000 | n/a |
| 8 | 2.01 | 2.20 | 4.08 | 16 | -0.3986 | n/a |
| 9 | -7.31 | -8.45 | 8.02 | 3 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -1.74 | -3.83 | 4.40 | 4 | -0.4821 | n/a |
| 16 | -1.13 | -3.19 | 2.25 | 1 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.49 | 3.63 | 0.34 | 1 | -1000.0000 | n/a |
| 20 | -2.46 | -6.79 | 3.94 | 3 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 19.30 | 2.85 | 4.24 | 0.0557 |
| fees_2x | 18.72 | 2.77 | 4.25 | 0.0478 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 19.88 | 2.93 | 4.23 | 0.0635 |
| very_low_liquidity | 19.88 | 2.93 | 4.23 | 0.0635 |
| high_slippage | 18.42 | 2.74 | 4.25 | 0.0511 |
| extreme_slippage | 15.50 | 2.34 | 4.31 | 0.0257 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -3.66 | -0.45 | 12.20 | -0.2567 |
| spread_widen_25bps | -5.00 | -0.59 | 12.85 | -0.2832 |
| thin_book | -7.90 | -2.69 | 7.90 | -1000.0000 |
| very_thin_book | -7.90 | -2.69 | 7.90 | -1000.0000 |
| entry_spread_stress | -3.75 | -0.46 | 12.25 | -0.2580 |
| combined_market_deterioration | -7.96 | -2.70 | 7.96 | -1000.0000 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19203
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0021)
- **Trend**: ranging (efficiency: 0.0200)
- **Best holdout score**: -0.4267 (rank #3)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9682 | -1000.0000 | -1.18 | 2.69 | 3 |
| 1 | -1000.0000 | -1000.0000 | -1.20 | 2.44 | 1 |
| 2 | -1000.0000 | -1000.0000 | -1.64 | 2.41 | 2 |
| 3 | -1000.0000 | -0.4267 | -1.93 | 2.59 | 6 |
| 4 | -1000.0000 | -1000.0000 | -1.81 | 2.97 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103810
- **Expected rows**: 104082
- **Missing rows**: 272
- **Forward-fill count**: 192
- **Forward-fill fraction**: 0.0018495328003082555
- **Longest gap (seconds)**: 19200

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -2.6270% < 0; recent trades 1 < 5
- **Objective score**: -1000.0
- **PnL %**: -2.6270460323928173
- **Trade count**: 1

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

- **Sensitivity penalty**: 0.25
- **Baseline score**: -0.20446676249292783
- **Sign flips**: 0
- **Collapse count**: 5
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.1803, -0.1753 |
| regime_ema_slow | -0.3489, -1000.0000 |
| regime_adx_length | -0.2186, -0.1780 |
| regime_adx_threshold | -0.1250, -0.1853 |
| volume_filter_window | -0.4944, -0.2054 |
| min_volume_quantile | -0.3563, -0.4951 |
| stop_loss | -0.2175, -0.2263 |
| take_profit | -0.2045, -0.2045 |
| cooldown_time | -0.2802, -0.2369 |
| total_amount_quote | -0.2045, -0.2045 |

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
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: **FAIL**
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | -2.6270460323928173 | FAIL |
| recent_trades | >= 5 | 1 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.25 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.25 |
| recent_28d | FAIL | score=-1000.0, pnl=-2.6270460323928173, trades=1, reason=recent objective score -1000.0000 <= 0; recent PnL -2.6270% < 0; recent trades 1 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103810 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent PnL -2.6270% < 0; recent trades 1 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103810
- **Pre-release bars**: 96017
- **Dev bars**: 76814
- **Holdout bars**: 19203
- **Recent 28d bars**: 7793
- **Recent window start**: 1774095600

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T16:53:56.158919+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 29
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
