# PMM Dynamic Optimization Report: nonkyc_EPIC-XMR_5m_4h_ema_regime_hold_v1

Generated: 2026-04-18 17:30:18 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/ema_regime_hold |
| run_timestamp | 2026-04-18T17:30:18.085717+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 184 |
| signal_interval | 5m |
| regime_interval | 4h |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-XMR
- **interval**: 5m+4h
- **n_candles**: 38431
- **dataset_hash**: 918ba97e2b7638b5d12387fbe4e91a5544f5d53019fa05fbab915cb730d37435
- **n_trials_phase1**: 500
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 969.9257418113835
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| cooldown_time | 44614 |
| min_volume_quantile | 0.18347855470319638 |
| regime_adx_length | 9 |
| regime_adx_threshold | 34.9281586924101 |
| regime_ema_fast | 78 |
| regime_ema_slow | 289 |
| stop_loss | 0.07717806426788434 |
| take_profit | 0.0373413149971811 |
| take_profit_order_type | LIMIT |
| time_limit | 316986 |
| total_amount_quote | 969.9257418113835 |
| trailing_stop_activation | 0.016394128659231226 |
| trailing_stop_delta | 0.021055716625556248 |
| volume_filter_window | 372 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 969.9257418113835 |
| Selected | 969.9257418113835 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -0.4018
- **Net PnL (quote)**: -3.8973
- **Sharpe Ratio**: -4.5200
- **Max Drawdown %**: 0.5172
- **Profit Factor**: 0.22184303341374537
- **Trade Count**: 3647
- **Total Fees (quote)**: 0.3592
- **Maker Fees**: 0.1297
- **Taker Fees**: 0.2295
- **Fee Drag %**: 0.0370
- **TP Min-Notional Failures**: 1 :warning:
  > 1 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0090
- **PnL Component**: -0.0040
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0039
- **Fee Drag Component**: -0.0002
- **Inventory Component**: -0.0008
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.3093**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 1 | 0.04 | 1.29 | 0.09 | 1494 | -0.0031 | n/a |
| 2 | -0.56 | -29.09 | 0.64 | 2512 | -0.2679 | n/a |
| 3 | -0.88 | -197.27 | 0.88 | 3392 | -0.3082 | n/a |
| 4 | -0.89 | -15.19 | 0.89 | 3750 | -0.3142 | n/a |
| 5 | -0.47 | -29.24 | 0.47 | 1922 | -0.3044 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -0.42 | -4.74 | 0.53 | -0.0093 |
| fees_2x | -0.44 | -4.95 | 0.54 | -0.0096 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -0.20 | -4.52 | 0.26 | -0.0045 |
| very_low_liquidity | -0.10 | -4.52 | 0.13 | -0.0022 |
| high_slippage | -0.41 | -4.59 | 0.52 | -0.0090 |
| extreme_slippage | -0.42 | -4.73 | 0.53 | -0.0092 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -0.40 | -4.56 | 0.52 | -0.0090 |
| spread_widen_25bps | -0.41 | -4.61 | 0.52 | -0.0090 |
| thin_book | -0.16 | -6.48 | 0.18 | -0.1401 |
| very_thin_book | -0.06 | -5.29 | 0.06 | -0.1134 |
| entry_spread_stress | -0.41 | -4.57 | 0.52 | -0.0090 |
| combined_market_deterioration | -0.22 | -5.20 | 0.26 | -0.0612 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 6077
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0071)
- **Trend**: ranging (efficiency: 0.0018)
- **Best holdout score**: -0.2410 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0045 | -0.2410 | -0.86 | 0.86 | 5453 |
| 1 | 0.0001 | -0.2790 | -1.91 | 1.92 | 5452 |
| 2 | -0.0001 | -0.2749 | -2.89 | 2.89 | 5453 |
| 3 | -0.0025 | -0.2917 | -3.48 | 3.48 | 5453 |
| 4 | -0.0025 | -0.2843 | -2.03 | 2.03 | 5452 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 38431
- **Expected rows**: 38452
- **Missing rows**: 21
- **Forward-fill count**: 861
- **Forward-fill fraction**: 0.022403788608154875
- **Longest gap (seconds)**: 1500

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.3107 <= 0; recent PnL -0.9501% < 0
- **Objective score**: -0.31065410049578207
- **PnL %**: -0.9501466937087973
- **Trade count**: 3542

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3115 <= 0; recent PnL -0.9508% < 0
- **Objective score**: -0.31146023182827287
- **PnL %**: -0.9507726486195889
- **Trade count**: 3531

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -1000.0000 <= 0; recent trades 0 < 5
- **Objective score**: -1000.0
- **PnL %**: 0.0
- **Trade count**: 0

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.37310187610124956
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 20
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| regime_ema_fast | -0.3752, -0.3729 |
| regime_ema_slow | -0.3752, -0.3729 |
| regime_adx_length | -0.3731, -0.3777 |
| regime_adx_threshold | -0.3731, -0.3777 |
| volume_filter_window | -0.3731, -0.3731 |
| min_volume_quantile | -0.3731, -0.3731 |
| stop_loss | -0.3826, -0.3667 |
| take_profit | -0.3731, -0.3731 |
| cooldown_time | -0.3732, -0.3731 |
| total_amount_quote | -0.3646, -0.3835 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3076581173458268
- **Max CV**: 0.46324906301506746
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2659 | 0.045217259696199344 | 0.09690904822736213 | 0.07499690772753351 |
| take_profit | 0.4632 | 0.028370777125835765 | 0.08724134713799589 | 0.05107207971816734 |
| cooldown_time | 0.2919 | 22436.0 | 85855.0 | 55540.8 |
| total_amount_quote | 0.2096 | 422.9637832752745 | 997.9960091639858 | 871.8867890424848 |

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
| recent_objective | > 0 | -0.31065410049578207 | FAIL |
| recent_pnl | >= 0 | -0.9501466937087973 | FAIL |
| recent_trades | >= 5 | 3542 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.2409811075295733 |
| walkforward | PASS | 6 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.31065410049578207, pnl=-0.9501466937087973, trades=3542, reason=recent objective score -0.3107 <= 0; recent PnL -0.9501% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.31146023182827287, pnl=-0.9507726486195889, trades=3531, reason=recent objective score -0.3115 <= 0; recent PnL -0.9508% < 0 |
| recent_7d_info | FAIL | informational only; score=-1000.0, pnl=0.0, trades=0, reason=recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3076581173458268 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 38431 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.3107 <= 0; recent PnL -0.9501% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3115 <= 0; recent PnL -0.9508% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -1000.0000 <= 0; recent trades 0 < 5 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 38431
- **Pre-release bars**: 30387
- **Dev bars**: 24310
- **Holdout bars**: 6077
- **Recent 28d bars**: 8044
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/ema_regime_hold
- **run_timestamp**: 2026-04-18T17:30:18.085717+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 184
- **signal_interval**: 5m
- **regime_interval**: 4h
- **validation_status**: validated_fail
