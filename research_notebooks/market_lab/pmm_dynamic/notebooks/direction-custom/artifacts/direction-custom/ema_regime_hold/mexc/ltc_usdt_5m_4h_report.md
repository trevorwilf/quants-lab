# PMM Dynamic Optimization Report: mexc_LTC-USDT_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:08:59 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:08:59.588805+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.0 |
| trial_number | 202 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: mexc
- **trading_pair**: LTC-USDT
- **interval**: 5m+4h
- **n_candles**: 103801
- **dataset_hash**: 1ff9c71b7f522376720a1325d3165546e9aacb8e98a917bd31d99d5578f565ac
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 136.4266872734263
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 63741 |
| min_volume_quantile | 0.030949914804117667 |
| regime_adx_length | 18 |
| regime_adx_threshold | 19.953475468066163 |
| regime_ema_fast | 15 |
| regime_ema_slow | 102 |
| stop_loss | 0.077551816657826 |
| take_profit | 0.09059301925173775 |
| take_profit_order_type | MARKET |
| time_limit | 553620 |
| total_amount_quote | 136.4266872734263 |
| trailing_stop_activation | 0.0011848813327344336 |
| trailing_stop_delta | 0.001259026015266214 |
| volume_filter_window | 455 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 136.4266872734263 |
| Selected | 136.4266872734263 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 5.0675
- **Net PnL (quote)**: 6.9134
- **Sharpe Ratio**: 0.6636
- **Max Drawdown %**: 8.1304
- **Profit Factor**: 1.625220721170805
- **Trade Count**: 91
- **Total Fees (quote)**: 4.9137
- **Maker Fees**: 2.4557
- **Taker Fees**: 2.4580
- **Fee Drag %**: 3.6017

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0300
- **PnL Component**: 0.0494
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0610
- **Fee Drag Component**: -0.0180
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1807**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.03 | 0.70 | 0.13 | 4 | -0.1850 | n/a |
| 1 | 0.00 | 0.03 | 0.47 | 2 | -1000.0000 | n/a |
| 2 | 0.78 | 2.07 | 1.26 | 10 | -0.1637 | n/a |
| 3 | 2.69 | 3.62 | 2.53 | 13 | -0.1437 | n/a |
| 4 | 2.81 | 6.89 | 0.64 | 15 | -0.1203 | n/a |
| 5 | 0.58 | 4.16 | 0.37 | 5 | -0.1778 | n/a |
| 6 | 0.03 | 0.27 | 0.92 | 2 | -1000.0000 | n/a |
| 7 | 0.00 | 0.03 | 0.60 | 8 | -0.1735 | n/a |
| 8 | 1.84 | 6.11 | 0.72 | 10 | -0.1494 | n/a |
| 9 | 0.53 | 1.60 | 1.14 | 4 | -0.1879 | n/a |
| 10 | 0.27 | 5.17 | 0.08 | 3 | -1000.0000 | n/a |
| 11 | -2.78 | -3.73 | 3.60 | 6 | -0.4827 | n/a |
| 12 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 13 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 14 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 15 | 0.50 | 1.86 | 1.05 | 9 | -0.1685 | n/a |
| 16 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 17 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 18 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 19 | 0.21 | 0.57 | 2.16 | 2 | -1000.0000 | n/a |
| 20 | -0.14 | -0.20 | 2.91 | 14 | -0.4191 | n/a |
| 21 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 3.27 | 0.45 | 8.72 | -0.0608 |
| fees_2x | 1.46 | 0.23 | 9.33 | -0.0916 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 5.07 | 0.66 | 8.13 | -0.0300 |
| very_low_liquidity | 5.07 | 0.66 | 8.13 | -0.0300 |
| high_slippage | -1.02 | -0.09 | 8.33 | -0.0850 |
| extreme_slippage | -7.27 | -1.03 | 8.18 | -0.1444 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -6.29 | -0.65 | 7.72 | -0.2623 |
| spread_widen_25bps | 13.13 | 1.18 | 5.48 | -0.1608 |
| thin_book | 3.20 | 0.39 | 9.12 | -0.0544 |
| very_thin_book | -1.68 | -0.11 | 11.71 | -0.1193 |
| entry_spread_stress | -6.53 | -0.68 | 7.74 | -0.2569 |
| combined_market_deterioration | 3.06 | 0.34 | 9.79 | -0.0695 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 19147
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0028)
- **Trend**: ranging (efficiency: 0.0123)
- **Best holdout score**: -0.1462 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0150 | -0.1912 | -0.58 | 2.91 | 12 |
| 1 | -0.1800 | -0.2677 | -3.85 | 5.83 | 4 |
| 2 | -0.1807 | -0.1462 | 0.73 | 0.51 | 13 |
| 3 | -0.1816 | -0.1716 | 0.67 | 0.78 | 10 |
| 4 | -0.1846 | -0.3057 | -1.69 | 1.69 | 4 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 103801
- **Expected rows**: 103803
- **Missing rows**: 2
- **Forward-fill count**: 54
- **Forward-fill fraction**: 0.0005202262020597104
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1971 <= 0; recent trades 4 < 5
- **Objective score**: -0.19707521321184243
- **PnL %**: 0.24833738788311355
- **Trade count**: 4

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.02532095407066443
- **Trade count**: 2

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5
- **Objective score**: -1000.0
- **PnL %**: -0.02532095407066443
- **Trade count**: 2

## Sensitivity Analysis

- **Sensitivity penalty**: 0.35
- **Baseline score**: -0.02694720817190812
- **Sign flips**: 2
- **Collapse count**: 5
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.0154, 0.0406 |
| regime_ema_slow | -0.0198, 0.0406 |
| regime_adx_length | -0.0396, -0.2339 |
| regime_adx_threshold | -0.1480, -0.1128 |
| volume_filter_window | -0.0236, -0.0269 |
| min_volume_quantile | -0.0236, -0.0269 |
| stop_loss | -0.0396, -0.0143 |
| take_profit | -0.0269, -0.0269 |
| cooldown_time | -0.1567, -0.0838 |
| total_amount_quote | -0.0269, -0.0269 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.48214216000535626
- **Max CV**: 0.6781366392378424
- **Clustered params**: take_profit
- **Scattered params**: stop_loss, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.5034 | 0.02123877829259515 | 0.08585700395068484 | 0.05450944110790803 |
| take_profit | 0.1985 | 0.04711663932397201 | 0.09059301925173775 | 0.06811060565914744 |
| cooldown_time | 0.6781 | 7551.0 | 81533.0 | 45506.9 |
| total_amount_quote | 0.5485 | 29.35465740361684 | 774.6295650221697 | 461.79231230432543 |

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
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.19707521321184243 | FAIL |
| recent_pnl | >= 0 | 0.24833738788311355 | PASS |
| recent_trades | >= 5 | 4 | FAIL |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.35 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.191179395982251 |
| walkforward | PASS | 22 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.35 |
| recent_28d | FAIL | score=-0.19707521321184243, pnl=0.24833738788311355, trades=4, reason=recent objective score -0.1971 <= 0; recent trades 4 < 5 |
| recent_14d_info | FAIL | informational only; score=-1000.0, pnl=-0.02532095407066443, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=-0.02532095407066443, trades=2, reason=recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.48214216000535626 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 103801 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1971 <= 0; recent trades 4 < 5 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent PnL -0.0253% < 0; recent trades 2 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 103801
- **Pre-release bars**: 95738
- **Dev bars**: 76591
- **Holdout bars**: 19147
- **Recent 28d bars**: 8063
- **Recent window start**: 1774012500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:08:59.588805+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.0
- **trial_number**: 202
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
