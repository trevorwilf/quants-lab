# PMM Dynamic Optimization Report: mexc_XMR-USDC_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:17:46 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:17:46.898783+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 83 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: XMR-USDC
- **interval**: 5m+4h
- **n_candles**: 103798
- **dataset_hash**: deec9d693a20b8e936ccee7a0a82789da2a12b8bafee99e8cb788d5db068fd8d
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 191.44998331500238
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 80830 |
| min_volume_quantile | 0.36625018406359894 |
| regime_adx_length | 9 |
| regime_adx_threshold | 14.698192911150578 |
| regime_ema_fast | 96 |
| regime_ema_slow | 382 |
| stop_loss | 0.05637765032962335 |
| take_profit | 0.0544643028260991 |
| take_profit_order_type | LIMIT |
| time_limit | 483604 |
| total_amount_quote | 191.44998331500238 |
| trailing_stop_activation | 0.0017941655739997767 |
| trailing_stop_delta | 0.0113335466941888 |
| volume_filter_window | 473 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 191.44998331500238 |
| Selected | 191.44998331500238 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 6.9148
- **Net PnL (quote)**: 13.2384
- **Sharpe Ratio**: 0.8322
- **Max Drawdown %**: 4.5889
- **Profit Factor**: 6.368632334911425
- **Trade Count**: 95
- **Total Fees (quote)**: 4.5217
- **Maker Fees**: 2.2591
- **Taker Fees**: 2.2626
- **Fee Drag %**: 2.3618

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0202
- **PnL Component**: 0.0669
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0344
- **Fee Drag Component**: -0.0118
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
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 6 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 2.20 | 2.08 | 3.18 | 16 | -0.1416 | n/a |
| 12 | -5.72 | -7.89 | 5.72 | 2 | -1000.0000 | n/a |
| 13 | 2.52 | 4.63 | 1.91 | 28 | -0.2147 | n/a |
| 14 | 0.00 | 0.12 | 3.38 | 29 | -0.3615 | n/a |
| 15 | 0.29 | 0.43 | 3.50 | 34 | -0.3417 | n/a |
| 16 | -5.22 | -5.42 | 5.70 | 4 | -0.3573 | n/a |
| 17 | 2.37 | 5.76 | 1.39 | 11 | -0.1446 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 20 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 5.73 | 0.70 | 4.65 | 0.0027 |
| fees_2x | 4.55 | 0.57 | 4.72 | -0.0149 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 5.64 | 0.71 | 6.57 | -0.0068 |
| very_low_liquidity | -3.39 | -0.69 | 5.59 | -0.1749 |
| high_slippage | 3.96 | 0.50 | 4.75 | -0.0090 |
| extreme_slippage | -1.02 | -0.09 | 5.60 | -0.0791 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 4.42 | 0.58 | 9.06 | -0.0375 |
| spread_widen_25bps | -3.65 | -0.63 | 5.68 | -0.2065 |
| thin_book | -3.06 | -0.49 | 5.58 | -0.2268 |
| very_thin_book | -3.99 | -0.62 | 5.70 | -0.2334 |
| entry_spread_stress | -5.34 | -1.45 | 5.71 | -0.2786 |
| combined_market_deterioration | -2.68 | -0.30 | 5.71 | -0.1144 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19146
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0042)
- **Trend**: ranging (efficiency: 0.0141)
- **Best holdout score**: -0.2216 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9899 | -0.2657 | -3.81 | 5.62 | 4 |
| 1 | -1000.0000 | -0.3404 | -3.00 | 9.44 | 12 |
| 2 | -1000.0000 | -1000.0000 | -1.96 | 4.35 | 2 |
| 3 | -1000.0000 | -0.2509 | -2.31 | 7.18 | 7 |
| 4 | -1000.0000 | -0.2216 | -2.16 | 7.09 | 14 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103798
- **Expected rows**: 103799
- **Missing rows**: 1
- **Forward-fill count**: 163
- **Forward-fill fraction**: 0.0015703578103624348
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

- **Sensitivity penalty**: 0.6
- **Baseline score**: -0.012965068623807204
- **Sign flips**: 3
- **Collapse count**: 9
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0130, -0.0172 |
| regime_ema_slow | -0.0247, -0.2218 |
| regime_adx_length | -0.2185, -0.0152 |
| regime_adx_threshold | -0.2185, -0.0152 |
| volume_filter_window | -0.1320, 0.0957 |
| min_volume_quantile | 0.0278, -0.0192 |
| stop_loss | -0.0653, -0.0946 |
| take_profit | -0.0130, -0.0130 |
| cooldown_time | -0.2134, -0.2756 |
| total_amount_quote | -0.0169, 0.0038 |

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
| recent_objective | > 0 | -1000.0 | FAIL |
| recent_pnl | >= 0 | 0.0 | PASS |
| recent_trades | >= 5 | 0 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.6 | FAIL |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.26573889197625583 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | FAIL | penalty=0.6 |
| recent_28d | FAIL | score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | FAIL | mean_cv=0.5755714253901677 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103798 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | FAIL | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103798
- **Pre-release bars**: 95734
- **Dev bars**: 76588
- **Holdout bars**: 19146
- **Recent 28d bars**: 8064
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:17:46.898783+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 83
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
