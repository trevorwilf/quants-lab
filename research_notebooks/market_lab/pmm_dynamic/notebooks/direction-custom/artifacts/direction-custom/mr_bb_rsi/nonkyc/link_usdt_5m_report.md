# PMM Dynamic Optimization Report: nonkyc_LINK-USDT_5m_mr_bb_rsi_v1

Generated: 2026-04-18 14:17:09 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | direction-custom/mr_bb_rsi |
| run_timestamp | 2026-04-18T14:17:09.653264+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 1170 |
| validation_status | validated_fail |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LINK-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: 38d6eda3b70529cf39c596e01e0d4bce230023ca07485976f12d5063dced462f
- **n_trials_phase1**: 9000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 50.0
- **total_amount_quote_search_max**: 500.0
- **total_amount_quote_ideal**: 971.2810140588186
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| atr_length | 14 |
| bb_length | 141 |
| bb_std | 1.6419545772451962 |
| bbp_entry_threshold | 0.254708357161873 |
| cooldown_time | 57481 |
| max_atr_pct_for_entry | 0.021892616619623228 |
| min_volume_quantile | 0.23319591837529907 |
| rsi_entry_threshold | 39.291496190956444 |
| rsi_length | 18 |
| stop_loss | 0.03301453594161497 |
| take_profit | 0.010332522128060235 |
| take_profit_order_type | LIMIT |
| time_limit | 199899 |
| total_amount_quote | 971.2810140588186 |
| trailing_stop_activation | 0.010831229823662818 |
| trailing_stop_delta | 0.011706426521859952 |
| trend_ema_length | 275 |
| use_trend_filter | True |
| volume_filter_window | 436 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 50.0 |
| Search Max | 500.0 |
| Ideal | 971.2810140588186 |
| Selected | 971.2810140588186 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 9.4825
- **Net PnL (quote)**: 92.1016
- **Sharpe Ratio**: 2.2710
- **Max Drawdown %**: 2.7870
- **Profit Factor**: inf
- **Trade Count**: 56
- **Total Fees (quote)**: 40.4575
- **Maker Fees**: 21.7457
- **Taker Fees**: 18.7118
- **Fee Drag %**: 4.1654
- **TP Min-Notional Failures**: 3 :warning:
  > 3 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.0484
- **PnL Component**: 0.0906
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0209
- **Fee Drag Component**: -0.0208
- **Inventory Component**: -0.0000
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1754**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 1.25 | 4.36 | 0.62 | 6 | -0.1712 | n/a |
| 1 | 0.88 | 5.99 | 0.37 | 7 | -0.1676 | n/a |
| 2 | -0.17 | -0.36 | 1.83 | 6 | -0.5915 | n/a |
| 3 | 1.12 | 3.24 | 1.01 | 12 | -0.1521 | n/a |
| 4 | 0.69 | 1.52 | 2.49 | 2 | -1000.0000 | n/a |
| 5 | -1.28 | -3.71 | 2.00 | 50 | -0.1910 | n/a |
| 6 | 2.46 | 4.31 | 1.70 | 18 | -0.1235 | n/a |
| 7 | 1.83 | 4.86 | 0.98 | 8 | -0.1611 | n/a |
| 8 | -1.57 | -2.99 | 2.29 | 2 | -1000.0000 | n/a |

## Stress Test Results

Worst Scenario: **latency_plus1** (score: -1000.0000)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 7.40 | 1.78 | 2.80 | 0.0187 |
| fees_2x | 5.32 | 1.29 | 2.85 | -0.0117 |
| latency_plus1 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus2 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| latency_plus3 | 0.00 | 0.00 | 0.00 | -1000.0000 |
| low_liquidity | 8.10 | 1.97 | 2.79 | 0.0353 |
| very_low_liquidity | 5.57 | 1.38 | 2.79 | 0.0117 |
| high_slippage | 9.00 | 2.16 | 2.79 | 0.0440 |
| extreme_slippage | 8.04 | 1.94 | 2.80 | 0.0351 |
| combined_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |
| spread_widen_10bps | 9.01 | 2.12 | 2.79 | 0.0440 |
| spread_widen_25bps | 8.28 | 1.94 | 2.80 | 0.0373 |
| thin_book | 3.13 | 0.98 | 2.57 | -0.0262 |
| very_thin_book | -1.47 | -0.68 | 2.95 | -0.4251 |
| entry_spread_stress | 8.77 | 2.06 | 2.79 | 0.0418 |
| combined_market_deterioration | 4.70 | 1.33 | 2.81 | -0.0246 |
| severe_adverse | 0.00 | 0.00 | 0.00 | -1000.0000 |

## Holdout Validation

- **Holdout bars**: 8766
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0025)
- **Trend**: ranging (efficiency: 0.0043)
- **Best holdout score**: -0.1281 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -499.9758 | -0.1281 | -1.55 | 2.00 | 35 |
| 1 | -0.1291 | -0.4252 | -2.21 | 2.56 | 6 |
| 2 | -0.1303 | -0.4517 | -2.41 | 2.54 | 7 |
| 3 | -0.1323 | -0.2102 | -2.98 | 2.98 | 23 |
| 4 | -0.1362 | -0.4112 | -1.51 | 1.64 | 6 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51899
- **Missing rows**: 58
- **Forward-fill count**: 584
- **Forward-fill fraction**: 0.01126521479138134
- **Longest gap (seconds)**: 5700

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2067 <= 0; recent PnL -1.3735% < 0
- **Objective score**: -0.20670378788805682
- **PnL %**: -1.3735059912639391
- **Trade count**: 7

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.4156 <= 0; recent PnL -3.6703% < 0
- **Objective score**: -0.4155624158897957
- **PnL %**: -3.6702891023391095
- **Trade count**: 11

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.6492 <= 0; recent PnL -1.6576% < 0
- **Objective score**: -0.6492399107084006
- **PnL %**: -1.6575554542588868
- **Trade count**: 16

## Sensitivity Analysis

- **Sensitivity penalty**: 0.15384615384615385
- **Baseline score**: -0.13563076973483765
- **Sign flips**: 0
- **Collapse count**: 4
- **Perturbations**: 26
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| bb_length | -0.0589, -0.1841 |
| bb_std | -0.1076, -0.1402 |
| bbp_entry_threshold | -0.1402, -0.1076 |
| rsi_length | -0.2244, -0.3228 |
| rsi_entry_threshold | -1000.0000, -0.0081 |
| trend_ema_length | -0.3468, -0.0658 |
| max_atr_pct_for_entry | -0.1356, -0.1356 |
| volume_filter_window | -0.1364, -0.1356 |
| min_volume_quantile | -0.1356, -0.1364 |
| stop_loss | -0.0825, -0.1278 |
| take_profit | -0.1376, -0.1008 |
| cooldown_time | -0.1356, -0.1300 |
| total_amount_quote | -0.1360, -0.1204 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.18560667741662262
- **Max CV**: 0.3289861654458698
- **Clustered params**: stop_loss, take_profit, cooldown_time, total_amount_quote

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| stop_loss | 0.3290 | 0.0181612476313551 | 0.041106937214479736 | 0.025687296354750228 |
| take_profit | 0.0614 | 0.005118413115209441 | 0.0061376181297805804 | 0.0054599539489848335 |
| cooldown_time | 0.3009 | 2464.0 | 8783.0 | 6242.9 |
| total_amount_quote | 0.0511 | 847.3049562312142 | 994.3541480525373 | 934.249555269075 |

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
| recent_objective | > 0 | -0.20670378788805682 | FAIL |
| recent_pnl | >= 0 | -1.3735059912639391 | FAIL |
| recent_trades | >= 5 | 7 | PASS |
| worst_stress | > -10 | -1000.0 | FAIL |
| sensitivity_penalty | < 0.50 | 0.15384615384615385 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | SKIPPED |  |
| holdout | FAIL | score=-0.12809727435317864 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=latency_plus1 score=-1000.0 |
| sensitivity | PASS | penalty=0.15384615384615385 |
| recent_28d | FAIL | score=-0.20670378788805682, pnl=-1.3735059912639391, trades=7, reason=recent objective score -0.2067 <= 0; recent PnL -1.3735% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.4155624158897957, pnl=-3.6702891023391095, trades=11, reason=recent objective score -0.4156 <= 0; recent PnL -3.6703% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.6492399107084006, pnl=-1.6575554542588868, trades=16, reason=recent objective score -0.6492 <= 0; recent PnL -1.6576% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.18560667741662262 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | false | NOT_RUN | — | — | — | not executed |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2067 <= 0; recent PnL -1.3735% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.4156 <= 0; recent PnL -3.6703% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.6492 <= 0; recent PnL -1.6576% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43834
- **Dev bars**: 35068
- **Holdout bars**: 8766
- **Recent 28d bars**: 8007
- **Recent window start**: 1774090500

## Run Provenance

- **notebook**: direction-custom/mr_bb_rsi
- **run_timestamp**: 2026-04-18T14:17:09.653264+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 1170
- **validation_status**: validated_fail
