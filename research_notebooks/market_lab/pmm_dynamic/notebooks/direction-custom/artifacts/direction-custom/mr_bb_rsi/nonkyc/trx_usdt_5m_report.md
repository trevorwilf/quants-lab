# PMM Dynamic Optimization Report: nonkyc_TRX-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:51:16 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:51:16.315501+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 8197 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: TRX-USDT
- **interval**: 5m
- **n_candles**: 51879
- **dataset_hash**: e318a4da8f43c1ccdcf9ff82a6961e8016fdf7c9598e54235abc29942e76cfcb
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 996.6525299009503
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 24 |
| bb_length | 57 |
| bb_std | 1.6040363165865457 |
| bbp_entry_threshold | 0.3511974270430317 |
| cooldown_time | 10918 |
| max_atr_pct_for_entry | 0.005330384749281072 |
| min_volume_quantile | 0.13203157989794423 |
| rsi_entry_threshold | 36.40992441413804 |
| rsi_length | 11 |
| stop_loss | 0.028032198878533178 |
| take_profit | 0.048172133016637884 |
| take_profit_order_type | LIMIT |
| time_limit | 158843 |
| total_amount_quote | 996.6525299009503 |
| trailing_stop_activation | 0.00363555050297698 |
| trailing_stop_delta | 0.00016655305971309943 |
| trend_ema_length | 133 |
| use_trend_filter | False |
| volume_filter_window | 312 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 996.6525299009503 |
| Selected | 996.6525299009503 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.6647
- **Net PnL (quote)**: -26.5578
- **Sharpe Ratio**: -2.7330
- **Max Drawdown %**: 3.3061
- **Profit Factor**: 0.15522477679912822
- **Trade Count**: 49
- **Total Fees (quote)**: 20.8590
- **Maker Fees**: 7.1299
- **Taker Fees**: 13.7291
- **Fee Drag %**: 2.0929

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0663
- **PnL Component**: -0.0270
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0248
- **Fee Drag Component**: -0.0105
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0040
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.2748**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -1.25 | -8.44 | 1.25 | 23 | -0.3840 | n/a |
| 1 | -1.40 | -9.26 | 1.52 | 45 | -0.1384 | n/a |
| 2 | -1.44 | -12.67 | 1.55 | 61 | -0.1545 | n/a |
| 3 | -1.10 | -11.33 | 1.10 | 20 | -0.2881 | n/a |
| 4 | -1.21 | -7.25 | 1.37 | 63 | -0.1741 | n/a |
| 5 | -1.54 | -15.11 | 1.54 | 24 | -0.3103 | n/a |
| 6 | -1.41 | -7.20 | 1.57 | 76 | -0.2237 | n/a |
| 7 | -1.30 | -7.48 | 1.44 | 95 | -0.3496 | n/a |
| 8 | -1.07 | -8.10 | 1.15 | 16 | -0.2392 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.62 | -3.68 | 3.80 | -0.1082 |
| fees_2x | -4.29 | -4.22 | 4.42 | -0.1875 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | -2.81 | -3.15 | 3.18 | -0.0602 |
| very_low_liquidity | -2.94 | -3.81 | 3.32 | -0.0609 |
| high_slippage | -3.03 | -3.12 | 3.41 | -0.0855 |
| extreme_slippage | -3.61 | -3.64 | 3.84 | -0.1038 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | -2.93 | -2.97 | 3.38 | -0.0656 |
| spread_widen_25bps | -3.11 | -2.19 | 3.34 | -0.1452 |
| thin_book | -2.75 | -2.78 | 2.98 | -0.1430 |
| very_thin_book | -1.21 | -3.37 | 1.21 | -1000.0000 |
| entry_spread_stress | -2.86 | -2.88 | 3.20 | -0.0636 |
| combined_market_deterioration | -3.82 | -3.17 | 3.93 | -0.1559 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0009)
- **Trend**: ranging (efficiency: 0.0263)
- **Best holdout score**: -0.1256 (rank #2)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -500.0332 | -0.1325 | -1.70 | 1.85 | 109 |
| 1 | -0.1118 | -0.1824 | -1.64 | 1.75 | 22 |
| 2 | -0.1154 | -0.1256 | -1.11 | 1.11 | 42 |
| 3 | -0.1160 | -0.2737 | -1.87 | 1.90 | 25 |
| 4 | -0.1250 | -0.1539 | -1.21 | 1.57 | 25 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51879
- **Expected rows**: 51913
- **Missing rows**: 34
- **Forward-fill count**: 133
- **Forward-fill fraction**: 0.0025636577420536247
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.4280 <= 0; recent PnL -1.2668% < 0
- **Objective score**: -0.4280353882369051
- **PnL %**: -1.2667556714035626
- **Trade count**: 13

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0789 <= 0; recent PnL -1.4917% < 0
- **Objective score**: -0.07886895265927032
- **PnL %**: -1.4917429837851575
- **Trade count**: 72

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3734 <= 0; recent PnL -1.2547% < 0
- **Objective score**: -0.37339809840505633
- **PnL %**: -1.2546778058369243
- **Trade count**: 37

## Sensitivity Analysis

- **Sensitivity penalty**: 0.038461538461538464
- **Baseline score**: -0.06585135939484894
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0659, -0.0659 |
| bb_std | -0.0659, -0.0659 |
| bbp_entry_threshold | -0.0659, -0.0659 |
| rsi_length | -0.0849, -0.0659 |
| rsi_entry_threshold | -0.0623, -0.0642 |
| trend_ema_length | -0.0619, -0.1019 |
| max_atr_pct_for_entry | -0.0659, -0.0659 |
| volume_filter_window | -0.0659, -0.0659 |
| min_volume_quantile | -0.0659, -0.0659 |
| stop_loss | -0.0708, -0.0609 |
| take_profit | -0.0659, -0.0659 |
| cooldown_time | -0.0682, -0.0771 |
| total_amount_quote | -0.0618, -0.0859 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.3192687248581881
- **Max CV**: 0.41442254470486306
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3554 | 0.029551478422846868 | 0.0709497183622074 | 0.048523220365063145 |
| take_profit | 0.4144 | 0.01079092342450515 | 0.0554395160919067 | 0.033833009042698266 |
| cooldown_time | 0.3755 | 4315.0 | 12653.0 | 7936.5 |
| total_amount_quote | 0.1318 | 687.0753316259031 | 998.574605075629 | 859.3543448827965 |

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
| recent_objective | > 0 | -0.4280353882369051 | FAIL |
| recent_pnl | >= 0 | -1.2667556714035626 | FAIL |
| recent_trades | >= 5 | 13 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.038461538461538464 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.1325482981844182 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.038461538461538464 |
| recent_28d | FAIL | score=-0.4280353882369051, pnl=-1.2667556714035626, trades=13, reason=recent objective score -0.4280 <= 0; recent PnL -1.2668% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.07886895265927032, pnl=-1.4917429837851575, trades=72, reason=recent objective score -0.0789 <= 0; recent PnL -1.4917% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.37339809840505633, pnl=-1.2546778058369243, trades=37, reason=recent objective score -0.3734 <= 0; recent PnL -1.2547% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.3192687248581881 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51879 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.4280 <= 0; recent PnL -1.2668% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0789 <= 0; recent PnL -1.4917% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.3734 <= 0; recent PnL -1.2547% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51879
- **Pre-release bars**: 43848
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8031
- **Recent window start**: 1774094700

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:51:16.315501+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 8197
- **validation_status**: validated_fail
