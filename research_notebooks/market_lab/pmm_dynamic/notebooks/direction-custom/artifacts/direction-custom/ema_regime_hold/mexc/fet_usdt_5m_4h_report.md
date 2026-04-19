# PMM Dynamic Optimization Report: mexc_FET-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:04:42 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:04:42.123834+00:00 |
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
- **trading_pair**: FET-USDT
- **interval**: 5m+4h
- **n_candles**: 103803
- **dataset_hash**: 37aeb3da4ab19b2b3d8e0f44ec1cc9707f7cbea8c10e72eed6d998a7df27a275
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

- **PnL %**: 23.0270
- **Net PnL (quote)**: 7.0146
- **Sharpe Ratio**: 1.7032
- **Max Drawdown %**: 7.5742
- **Profit Factor**: 2.0656722260715026
- **Trade Count**: 20
- **Total Fees (quote)**: 0.2330
- **Maker Fees**: 0.1415
- **Taker Fees**: 0.0915
- **Fee Drag %**: 0.7648

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0261
- **PnL Component**: 0.2072
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0568
- **Fee Drag Component**: -0.0038
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.1200
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
| 11 | 20.32 | 9.40 | 4.47 | 9 | -0.2383 | n/a |
| 12 | 1.89 | 2.25 | 3.51 | 3 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | -1.21 | -0.22 | 12.27 | 9 | -0.5689 | n/a |
| 16 | -3.10 | -2.41 | 7.59 | 3 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | -3.71 | -5.62 | 5.04 | 2 | -1000.0000 | n/a |
| 21 | 6.60 | 4.99 | 3.81 | 4 | -0.3898 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 22.64 | 1.68 | 7.62 | 0.0207 |
| fees_2x | 22.26 | 1.65 | 7.67 | 0.0153 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 23.03 | 1.70 | 7.57 | 0.0261 |
| very_low_liquidity | 23.03 | 1.70 | 7.57 | 0.0261 |
| high_slippage | 22.28 | 1.65 | 7.68 | 0.0192 |
| extreme_slippage | 20.77 | 1.54 | 7.88 | 0.0053 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 21.92 | 1.63 | 7.60 | 0.0168 |
| spread_widen_25bps | 25.56 | 1.85 | 7.63 | 0.0460 |
| thin_book | -4.10 | -0.45 | 10.06 | -0.2877 |
| very_thin_book | -3.71 | -0.79 | 5.01 | -1000.0000 |
| entry_spread_stress | 21.69 | 1.62 | 7.61 | 0.0149 |
| combined_market_deterioration | -4.68 | -0.50 | 10.34 | -0.2981 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19147
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0067)
- **Best holdout score**: -1000.0000 (rank #-1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9870 | -1000.0000 | -2.26 | 5.11 | 3 |
| 1 | -1000.0000 | -1000.0000 | -2.38 | 2.70 | 2 |
| 2 | -1000.0000 | -1000.0000 | -1.78 | 2.75 | 1 |
| 3 | -1000.0000 | -1000.0000 | -1.23 | 2.75 | 1 |
| 4 | -1000.0000 | -1000.0000 | 0.00 | 0.00 | 0 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103803
- **Expected rows**: 103803
- **Missing rows**: 0
- **Forward-fill count**: 64
- **Forward-fill fraction**: 0.0006165525081163357
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.4292 <= 0; recent PnL -1.8175% < 0; recent trades 4 < 5
- **Objective score**: -0.42921217458611705
- **PnL %**: -1.8175108663206447
- **Trade count**: 4

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -3.7109% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -3.71089684573807
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 1.0
- **Baseline score**: 0.05103993175064242
- **Sign flips**: 9
- **Collapse count**: 9
- **Perturbations**: 20
- **Rejected**: 2

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -1000.0000, -1000.0000 |
| regime_ema_slow | -1000.0000, -1000.0000 |
| regime_adx_length | -0.0484, -0.3022 |
| regime_adx_threshold | 0.0889, -0.2912 |
| volume_filter_window | 0.0510, 0.0510 |
| min_volume_quantile | 0.0510, 0.0510 |
| stop_loss | -0.0118, 0.1296 |
| take_profit | 0.0378, -0.2619 |
| cooldown_time | -0.0606, -0.0293 |
| total_amount_quote | 0.0510, 0.0510 |

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
| recent_objective | > 0 | -0.42921217458611705 | FAIL |
| recent_pnl | >= 0 | -1.8175108663206447 | FAIL |
| recent_trades | >= 5 | 4 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 1.0 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=1.0 |
| recent_28d | FAIL | score=-0.42921217458611705, pnl=-1.8175108663206447, trades=4, reason=recent objective score -0.4292 <= 0; recent PnL -1.8175% < 0; recent trades 4 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-3.71089684573807, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -3.7109% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103803 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.4292 <= 0; recent PnL -1.8175% < 0; recent trades 4 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -3.7109% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103803
- **Pre-release bars**: 95738
- **Dev bars**: 76591
- **Holdout bars**: 19147
- **Recent 28d bars**: 8065
- **Recent window start**: 1774012200

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:04:42.123834+00:00
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
