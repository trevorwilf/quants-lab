# PMM Dynamic Optimization Report: nonkyc_POL-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 15:02:34 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T15:02:34.371318+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 2585 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: POL-USDT
- **interval**: 5m
- **n_candles**: 51876
- **dataset_hash**: e1b48e25588ae3ac96002bf69551197a95e0f9e17be9065eacdfcc2f196caa98
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 967.2998584915126
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 10 |
| bb_length | 117 |
| bb_std | 1.1124394304508307 |
| bbp_entry_threshold | 0.20469139683139817 |
| cooldown_time | 71296 |
| max_atr_pct_for_entry | 0.006508908338744164 |
| min_volume_quantile | 0.5077975782350829 |
| rsi_entry_threshold | 20.68087965608322 |
| rsi_length | 9 |
| stop_loss | 0.02534259741009186 |
| take_profit | 0.006625428573795145 |
| take_profit_order_type | LIMIT |
| time_limit | 238828 |
| total_amount_quote | 967.2998584915126 |
| trailing_stop_activation | 0.022329143106474065 |
| trailing_stop_delta | 0.010410378038733384 |
| trend_ema_length | 356 |
| use_trend_filter | True |
| volume_filter_window | 346 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 967.2998584915126 |
| Selected | 967.2998584915126 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 2.6959
- **Net PnL (quote)**: 26.0779
- **Sharpe Ratio**: 1.3538
- **Max Drawdown %**: 1.6954
- **Profit Factor**: 66.54481730118891
- **Trade Count**: 192
- **Total Fees (quote)**: 12.1143
- **Maker Fees**: 12.0851
- **Taker Fees**: 0.0292
- **Fee Drag %**: 1.2524
- **TP Min-Notional Failures**: 268 :warning:
  > 268 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0075
- **PnL Component**: 0.0266
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0127
- **Fee Drag Component**: -0.0063
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0996**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 0.45 | 4.25 | 0.39 | 28 | -0.0876 | n/a |
| 1 | 0.43 | 2.49 | 0.55 | 47 | -0.0149 | n/a |
| 2 | 0.92 | 1.81 | 1.73 | 58 | -0.0066 | n/a |
| 3 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 4 | 0.00 | 0.00 | 0.00 | 0 | -1000.0000 | n/a |
| 5 | 0.01 | 6.61 | 0.01 | 1 | -1000.0000 | n/a |
| 6 | 0.49 | 1.98 | 1.15 | 34 | -0.0690 | n/a |
| 7 | 0.46 | 3.03 | 0.64 | 18 | -0.1293 | n/a |
| 8 | -2.57 | -9.06 | 3.01 | 118 | -0.1123 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 2.07 | 1.05 | 1.70 | -0.0018 |
| fees_2x | 1.44 | 0.74 | 1.71 | -0.0112 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 2.51 | 1.50 | 1.58 | 0.0067 |
| very_low_liquidity | -1.08 | -3.04 | 1.36 | -0.0224 |
| high_slippage | 2.70 | 1.35 | 1.70 | 0.0075 |
| extreme_slippage | 2.69 | 1.35 | 1.70 | 0.0075 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 2.70 | 1.35 | 1.70 | 0.0075 |
| spread_widen_25bps | 2.70 | 1.34 | 1.70 | 0.0075 |
| thin_book | -1.49 | -1.48 | 1.78 | -0.3858 |
| very_thin_book | 0.01 | 0.88 | 0.01 | -1000.0000 |
| entry_spread_stress | 2.70 | 1.34 | 1.70 | 0.0075 |
| combined_market_deterioration | -1.18 | -1.40 | 1.41 | -0.1562 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0027)
- **Trend**: ranging (efficiency: 0.0075)
- **Best holdout score**: -0.0014 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9963 | -0.0014 | 0.96 | 1.15 | 52 |
| 1 | -0.0094 | -0.2142 | -2.28 | 2.65 | 8 |
| 2 | -0.0104 | -0.3756 | -3.53 | 3.53 | 5 |
| 3 | -0.0124 | -0.4840 | -1.92 | 1.92 | 4 |
| 4 | -0.0126 | -1000.0000 | -1.91 | 1.91 | 3 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51876
- **Expected rows**: 51899
- **Missing rows**: 23
- **Forward-fill count**: 206
- **Forward-fill fraction**: 0.003971007787801681
- **Longest gap (seconds)**: 6600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1029 <= 0; recent PnL -2.5683% < 0
- **Objective score**: -0.10287015305748595
- **PnL %**: -2.568283401473823
- **Trade count**: 118

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.3127 <= 0; recent PnL -2.8852% < 0
- **Objective score**: -0.31270983178715095
- **PnL %**: -2.8851720327334722
- **Trade count**: 46

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1203 <= 0; recent PnL -0.3124% < 0
- **Objective score**: -0.12028584568861732
- **PnL %**: -0.3123672380716028
- **Trade count**: 77

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.0649944141079883
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0345, -0.0633 |
| bb_std | -0.0686, -0.0650 |
| bbp_entry_threshold | -0.0650, -0.0686 |
| rsi_length | -0.0270, -0.0451 |
| rsi_entry_threshold | -0.0801, -0.0270 |
| trend_ema_length | -0.0599, -0.0650 |
| max_atr_pct_for_entry | -0.0650, -0.0650 |
| volume_filter_window | -0.0650, -0.0650 |
| min_volume_quantile | -0.0653, -0.0710 |
| stop_loss | -0.0714, -0.0621 |
| take_profit | -0.0635, -0.0727 |
| cooldown_time | -0.0650, -0.0650 |
| total_amount_quote | -0.0652, -0.0653 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2375650298332126
- **Max CV**: 0.4094949518579131
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.4095 | 0.01567677063703946 | 0.04291549728838764 | 0.02175128516182904 |
| take_profit | 0.2799 | 0.00521113406688742 | 0.011369172488900573 | 0.00861997517111936 |
| cooldown_time | 0.2086 | 43314.0 | 84846.0 | 65303.4 |
| total_amount_quote | 0.0523 | 873.1366673104833 | 999.1389486771867 | 945.3602552354623 |

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
| recent_objective | > 0 | -0.10287015305748595 | FAIL |
| recent_pnl | >= 0 | -2.568283401473823 | FAIL |
| recent_trades | >= 5 | 118 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.0013629217176116797 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.10287015305748595, pnl=-2.568283401473823, trades=118, reason=recent objective score -0.1029 <= 0; recent PnL -2.5683% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.31270983178715095, pnl=-2.8851720327334722, trades=46, reason=recent objective score -0.3127 <= 0; recent PnL -2.8852% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.12028584568861732, pnl=-0.3123672380716028, trades=77, reason=recent objective score -0.1203 <= 0; recent PnL -0.3124% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2375650298332126 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51876 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1029 <= 0; recent PnL -2.5683% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.3127 <= 0; recent PnL -2.8852% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1203 <= 0; recent PnL -0.3124% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51876
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8042
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T15:02:34.371318+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 2585
- **validation_status**: validated_fail
