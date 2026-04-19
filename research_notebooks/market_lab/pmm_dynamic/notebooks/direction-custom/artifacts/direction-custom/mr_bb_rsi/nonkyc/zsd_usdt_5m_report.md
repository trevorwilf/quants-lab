# PMM Dynamic Optimization Report: nonkyc_ZSD-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 17:02:59 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T17:02:59.672718+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 3198 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: ZSD-USDT
- **interval**: 5m
- **n_candles**: 51872
- **dataset_hash**: 531e67cf0cccfae32a7695d87c5af3d99f781e70a6aee4031bbd3884b322be6e
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 35.01577820105729
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 23 |
| bb_length | 128 |
| bb_std | 2.240089373501977 |
| bbp_entry_threshold | 0.09516358783988013 |
| cooldown_time | 34709 |
| max_atr_pct_for_entry | 0.019003083729133452 |
| min_volume_quantile | 0.15728010336126813 |
| rsi_entry_threshold | 29.664560573274393 |
| rsi_length | 7 |
| stop_loss | 0.01851750909827124 |
| take_profit | 0.007010499495042208 |
| take_profit_order_type | LIMIT |
| time_limit | 271278 |
| total_amount_quote | 35.01577820105729 |
| trailing_stop_activation | 0.009692900065624102 |
| trailing_stop_delta | 0.0017806255715181012 |
| trend_ema_length | 337 |
| use_trend_filter | False |
| volume_filter_window | 483 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 35.01577820105729 |
| Selected | 35.01577820105729 |

> **WARNING**: Selected quote is within 5% of search minimum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 32.5124
- **Net PnL (quote)**: 11.3845
- **Sharpe Ratio**: 2.9676
- **Max Drawdown %**: 3.2246
- **Profit Factor**: 3.1852580406879882
- **Trade Count**: 605
- **Total Fees (quote)**: 5.0173
- **Maker Fees**: 1.8797
- **Taker Fees**: 3.1376
- **Fee Drag %**: 14.3286
- **TP Min-Notional Failures**: 2285 :warning:
  > 2285 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0577
- **PnL Component**: 0.2815
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0242
- **Fee Drag Component**: -0.0716
- **Inventory Component**: -0.1264
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1400**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.73 | -2.78 | 2.18 | 41 | -0.0649 | n/a |
| 1 | 2.53 | 7.36 | 0.47 | 50 | 0.0157 | n/a |
| 2 | 3.53 | 4.41 | 2.13 | 65 | 0.0105 | n/a |
| 3 | 3.13 | 2.61 | 1.78 | 67 | -0.2367 | n/a |
| 4 | 4.44 | 5.53 | 2.51 | 78 | 0.0156 | n/a |
| 5 | 2.14 | 2.46 | 2.04 | 72 | -0.0881 | n/a |
| 6 | -2.21 | -4.00 | 2.21 | 19 | -0.3888 | n/a |
| 7 | 1.45 | 1.38 | 1.23 | 65 | -0.2503 | n/a |
| 8 | 0.06 | 0.44 | 0.28 | 21 | -0.2741 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.03 | -0.16 | 2.89 | -0.0871 |
| fees_2x | -1.48 | -0.25 | 3.00 | -0.0946 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 26.65 | 2.54 | 3.03 | 0.0260 |
| very_low_liquidity | 17.64 | 1.91 | 3.18 | -0.0158 |
| high_slippage | 30.28 | 2.79 | 3.28 | 0.0394 |
| extreme_slippage | -1.01 | -0.15 | 2.94 | -0.0850 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 33.84 | 3.03 | 3.23 | 0.0508 |
| spread_widen_25bps | 29.34 | 2.51 | 3.91 | -0.0006 |
| thin_book | 25.80 | 3.03 | 2.26 | 0.1449 |
| very_thin_book | 3.92 | 0.68 | 2.48 | 0.0043 |
| entry_spread_stress | 31.69 | 2.74 | 3.89 | 0.0236 |
| combined_market_deterioration | -1.92 | -0.42 | 2.92 | -0.1460 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0057)
- **Trend**: ranging (efficiency: 0.0007)
- **Best holdout score**: -0.0012 (rank #4)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9712 | -0.1742 | -3.07 | 4.28 | 49 |
| 1 | 0.0015 | -0.1525 | -1.67 | 3.02 | 222 |
| 2 | 0.0014 | -0.3326 | -1.94 | 2.17 | 127 |
| 3 | 0.0013 | -0.3351 | -1.10 | 1.78 | 109 |
| 4 | 0.0010 | -0.0012 | 1.15 | 1.13 | 268 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51872
- **Expected rows**: 51899
- **Missing rows**: 27
- **Forward-fill count**: 1041
- **Forward-fill fraction**: 0.020068630475015423
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1446 <= 0; recent PnL -1.4648% < 0
- **Objective score**: -0.1446074904206595
- **PnL %**: -1.4647617961189563
- **Trade count**: 47

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.5509 <= 0; recent PnL -2.1619% < 0
- **Objective score**: -0.5509056404843815
- **PnL %**: -2.1618740073976355
- **Trade count**: 17

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4805 <= 0; recent PnL -0.2345% < 0
- **Objective score**: -0.4805468890006689
- **PnL %**: -0.23452682781189388
- **Trade count**: 23

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.0723524658585801
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0880, -0.0916 |
| bb_std | -0.0639, -0.0881 |
| bbp_entry_threshold | -0.0601, -0.0724 |
| rsi_length | -0.0516, -0.0712 |
| rsi_entry_threshold | -0.1544, -0.0065 |
| trend_ema_length | -0.0724, -0.0724 |
| max_atr_pct_for_entry | -0.0821, -0.0735 |
| volume_filter_window | -0.0724, -0.0665 |
| min_volume_quantile | -0.0724, -0.0698 |
| stop_loss | -0.0678, -0.0596 |
| take_profit | -0.0782, -0.0857 |
| cooldown_time | -0.0798, -0.0777 |
| total_amount_quote | -0.0840, -0.0420 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.44936848587800776
- **Max CV**: 0.7562091071551859
- **Clustered params**: stop_loss, total_amount_quote
- **Scattered params**: take_profit, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.2069 | 0.03506941881240658 | 0.07993323349076577 | 0.06622497849249662 |
| take_profit | 0.6273 | 0.007415688800660586 | 0.041047624347970726 | 0.015290993895880322 |
| cooldown_time | 0.7562 | 1524.0 | 19795.0 | 8915.4 |
| total_amount_quote | 0.2071 | 387.6610241025803 | 923.2532678356974 | 634.9153146816976 |

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
| recent_objective | > 0 | -0.1446074904206595 | FAIL |
| recent_pnl | >= 0 | -1.4647617961189563 | FAIL |
| recent_trades | >= 5 | 47 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1741561229559707 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.1446074904206595, pnl=-1.4647617961189563, trades=47, reason=recent objective score -0.1446 <= 0; recent PnL -1.4648% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.5509056404843815, pnl=-2.1618740073976355, trades=17, reason=recent objective score -0.5509 <= 0; recent PnL -2.1619% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.4805468890006689, pnl=-0.23452682781189388, trades=23, reason=recent objective score -0.4805 <= 0; recent PnL -0.2345% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.44936848587800776 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51872 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1446 <= 0; recent PnL -1.4648% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.5509 <= 0; recent PnL -2.1619% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.4805 <= 0; recent PnL -0.2345% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51872
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8038
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T17:02:59.672718+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 3198
- **validation_status**: validated_fail
