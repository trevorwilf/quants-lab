# PMM Dynamic Optimization Report: nonkyc_ZEC-XMR_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:42:19 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:42:19.271996+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 407 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZEC-XMR
- **interval**: 5m+4h
- **n_candles**: 65223
- **dataset_hash**: db7b852789c9d7ea09f1f8c2ddbcd324e176cf682582f28ab8bf4211c7b48297
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 398.9362265053522
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 79541 |
| min_volume_quantile | 0.2930348801020324 |
| regime_adx_length | 19 |
| regime_adx_threshold | 32.48268949911335 |
| regime_ema_fast | 74 |
| regime_ema_slow | 379 |
| stop_loss | 0.09963598454619244 |
| take_profit | 0.014972142329712841 |
| take_profit_order_type | MARKET |
| time_limit | 509298 |
| total_amount_quote | 398.9362265053522 |
| trailing_stop_activation | 0.003716664650171162 |
| trailing_stop_delta | 0.0023447974793311876 |
| volume_filter_window | 424 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 398.9362265053522 |
| Selected | 398.9362265053522 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.0432
- **Net PnL (quote)**: -4.1619
- **Sharpe Ratio**: -4.5909
- **Max Drawdown %**: 1.0573
- **Profit Factor**: 0.09939348414167826
- **Trade Count**: 11183
- **Total Fees (quote)**: 0.2268
- **Maker Fees**: 0.0834
- **Taker Fees**: 0.1434
- **Fee Drag %**: 0.0569

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1610
- **PnL Component**: -0.0105
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0079
- **Fee Drag Component**: -0.0003
- **Inventory Component**: -0.0018
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-1000.0000**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.15 | -13.12 | 0.19 | 2404 | -0.0041 | n/a |
| 1 | -0.53 | -51.40 | 0.53 | 2824 | -0.2781 | n/a |
| 2 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 3 | -0.01 | -1.13 | 0.06 | 1025 | -0.0014 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | -0.28 | -12.62 | 0.28 | 2894 | -0.1344 | n/a |
| 6 | -0.86 | -98.06 | 0.86 | 3899 | -0.3001 | n/a |
| 7 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 8 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 9 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 10 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 11 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 12 | -0.25 | -6.44 | 0.27 | 2354 | -0.2237 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.07 | -4.72 | 1.08 | -0.1622 |
| fees_2x | -1.10 | -4.86 | 1.11 | -0.1632 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -4.60 | -33.38 | 4.60 | -0.3380 |
| very_low_liquidity | -2.30 | -33.17 | 2.30 | -0.2961 |
| high_slippage | -1.05 | -4.63 | 1.07 | -0.1614 |
| extreme_slippage | -1.07 | -4.72 | 1.08 | -0.1621 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -1.05 | -4.57 | 1.06 | -0.1612 |
| spread_widen_25bps | -1.06 | -4.78 | 1.08 | -0.1670 |
| thin_book | -2.77 | -18.42 | 2.78 | -0.3063 |
| very_thin_book | -0.98 | -10.24 | 0.98 | -0.2663 |
| entry_spread_stress | -1.06 | -4.75 | 1.07 | -0.1669 |
| combined_market_deterioration | -4.83 | -21.85 | 4.84 | -0.3443 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 11437
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0073)
- **Trend**: ranging (efficiency: 0.0022)
- **Best holdout score**: -0.3276 (rank #4)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0805 | -1000.0000 | 0.00 | 0.00 | 0 |
| 1 | -0.0027 | -1000.0000 | 0.00 | 0.00 | 0 |
| 2 | -0.0030 | -1000.0000 | 0.00 | 0.00 | 0 |
| 3 | -0.0040 | -1000.0000 | 0.00 | 0.00 | 0 |
| 4 | -0.0043 | -0.3276 | -2.21 | 2.21 | 9106 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 65223
- **Expected rows**: 65254
- **Missing rows**: 31
- **Forward-fill count**: 2230
- **Forward-fill fraction**: 0.034190392959538816
- **Longest gap (seconds)**: 5100

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2332 <= 0; recent PnL -0.2806% < 0
- **Objective score**: -0.23322731603356686
- **PnL %**: -0.2805752715912093
- **Trade count**: 2531

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2338 <= 0; recent PnL -0.2806% < 0
- **Objective score**: -0.23378601565043045
- **PnL %**: -0.2805752715912093
- **Trade count**: 2531

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2955 <= 0; recent PnL -0.3273% < 0
- **Objective score**: -0.2954814976663108
- **PnL %**: -0.3272501666437523
- **Trade count**: 1928

## Sensitivity Analysis

- **Sensitivity penalty**: 0.2
- **Baseline score**: -0.16048077493455776
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.1605, -0.1605 |
| regime_ema_slow | -0.1605, -0.1605 |
| regime_adx_length | -0.2553, -0.1378 |
| regime_adx_threshold | -0.2553, -0.1378 |
| volume_filter_window | -0.1605, -0.1605 |
| min_volume_quantile | -0.1605, -0.1605 |
| stop_loss | -0.0887, -0.2455 |
| take_profit | -0.1605, -0.1605 |
| cooldown_time | -0.4648, -0.2108 |
| total_amount_quote | -0.1627, -0.1627 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.31659024556481796
- **Max CV**: 0.682458569596832
- **Clustered params**: stop_loss, cooldown_time, total_amount_quote
- **Scattered params**: take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.0434 | 0.08622338534372445 | 0.09856742480572933 | 0.09113684495961068 |
| take_profit | 0.6825 | 0.011302516347670174 | 0.07447517333482337 | 0.035087804002077824 |
| cooldown_time | 0.1456 | 53683.0 | 85333.0 | 71049.9 |
| total_amount_quote | 0.3949 | 206.20560912109605 | 835.2857293920569 | 543.7537295350085 |

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
| recent_objective | > 0 | -0.23322731603356686 | FAIL |
| recent_pnl | >= 0 | -0.2805752715912093 | FAIL |
| recent_trades | >= 5 | 2531 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.2 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-1000.0 |
| walkforward | PASS | 13 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.2 |
| recent_28d | FAIL | score=-0.23322731603356686, pnl=-0.2805752715912093, trades=2531, reason=recent objective score -0.2332 <= 0; recent PnL -0.2806% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.23378601565043045, pnl=-0.2805752715912093, trades=2531, reason=recent objective score -0.2338 <= 0; recent PnL -0.2806% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.2954814976663108, pnl=-0.3272501666437523, trades=1928, reason=recent objective score -0.2955 <= 0; recent PnL -0.3273% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.31659024556481796 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 65223 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2332 <= 0; recent PnL -0.2806% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.2338 <= 0; recent PnL -0.2806% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2955 <= 0; recent PnL -0.3273% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 65223
- **Pre-release bars**: 57189
- **Dev bars**: 45752
- **Holdout bars**: 11437
- **Recent 28d bars**: 8034
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:42:19.271996+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 407
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
