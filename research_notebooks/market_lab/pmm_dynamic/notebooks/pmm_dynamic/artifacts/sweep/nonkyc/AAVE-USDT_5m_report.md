# PMM Dynamic Optimization Report: nonkyc_AAVE-USDT_5m_sweep_v1

Generated: 2026-04-08 18:02:14 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T18:02:14.255375+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 6121 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AAVE-USDT
- **interval**: 5m
- **n_candles**: 51841
- **dataset_hash**: d47661d3ae28011b9bf484210639c35a035884c5e09aca11a4ed1773c3f24cee
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 873.4908331480322
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 2.3923264930747594 |
| buy_n_levels | 8 |
| buy_side_weight | 0.2446305428581694 |
| buy_spread_base | 3.20827217295729 |
| buy_spread_ratio | 2.48221304609984 |
| cooldown_time | 7000 |
| executor_refresh_time | 10855 |
| macd_fast | 21 |
| macd_signal | 13 |
| macd_slow | 89 |
| natr_length | 41 |
| sell_n_levels | 7 |
| sell_spread_base | 1.4950628914513215 |
| sell_spread_ratio | 2.2259307455327013 |
| stop_loss | 0.022967383961662566 |
| take_profit | 0.005081328103237134 |
| time_limit | 87688 |
| total_amount_quote | 873.4908331480322 |
| trailing_stop_activation | 0.008491951080727322 |
| trailing_stop_delta | 0.010406092678387782 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 873.4908331480322 |
| Selected | 873.4908331480322 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -10.6992
- **Net PnL (quote)**: -93.4567
- **Sharpe Ratio**: -2.6005
- **Max Drawdown %**: 11.5033
- **Profit Factor**: 0.43380268628682755
- **Trade Count**: 1935
- **Total Fees (quote)**: 41.9789
- **Maker Fees**: 29.5998
- **Taker Fees**: 12.3791
- **Fee Drag %**: 4.8059
- **TP Min-Notional Failures**: 19717 :warning:
  > 19717 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.2415
- **PnL Component**: -0.1132
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0863
- **Fee Drag Component**: -0.0240
- **Inventory Component**: -0.0177
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0194**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.26 | -10.62 | 0.30 | 84 | -0.0434 | n/a |
| 1 | -0.64 | -16.00 | 0.66 | 60 | -0.0152 | n/a |
| 2 | -0.56 | -11.09 | 0.57 | 70 | -0.0257 | n/a |
| 3 | -0.16 | -6.05 | 0.20 | 71 | -0.0068 | n/a |
| 4 | -0.87 | -17.39 | 0.89 | 85 | -0.0377 | n/a |
| 5 | -0.41 | -8.86 | 0.43 | 76 | -0.0113 | n/a |
| 6 | -0.34 | -7.97 | 0.39 | 63 | -0.0103 | n/a |
| 7 | -0.34 | -10.22 | 0.38 | 71 | -0.0101 | n/a |
| 8 | -0.76 | -16.56 | 0.78 | 74 | -0.0907 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.3567)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -13.10 | -3.24 | 13.84 | -0.2987 |
| fees_2x | -15.51 | -3.89 | 16.17 | -0.3567 |
| latency_plus1 | -9.90 | -2.41 | 10.59 | -0.2252 |
| latency_plus2 | -11.02 | -2.68 | 11.82 | -0.2482 |
| latency_plus3 | -10.40 | -2.53 | 11.11 | -0.2350 |
| low_liquidity | -11.72 | -2.38 | 12.41 | -0.2631 |
| very_low_liquidity | -13.27 | -4.98 | 13.94 | -0.2916 |
| high_slippage | -11.05 | -2.69 | 11.85 | -0.2482 |
| extreme_slippage | -11.76 | -2.88 | 12.54 | -0.2615 |
| combined_adverse | -14.57 | -3.02 | 15.26 | -0.3305 |
| spread_widen_10bps | -11.49 | -2.82 | 12.18 | -0.2556 |
| spread_widen_25bps | -14.12 | -3.50 | 14.82 | -0.3077 |
| thin_book | -12.33 | -1.94 | 12.71 | -0.2650 |
| very_thin_book | -8.66 | -7.15 | 8.86 | -0.1817 |
| entry_spread_stress | -10.79 | -2.66 | 11.42 | -0.2402 |
| combined_market_deterioration | -14.50 | -2.31 | 14.96 | -0.3230 |
| severe_adverse | -15.42 | -6.97 | 15.48 | -0.3298 |

## Holdout Validation

- **Holdout bars**: 8755
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0011)
- **Best holdout score**: -0.0173 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.2991 | -0.0173 | -0.67 | 0.72 | 148 |
| 1 | -0.0092 | -0.2414 | -7.26 | 7.26 | 934 |
| 2 | -0.0094 | -0.1243 | -5.63 | 5.63 | 679 |
| 3 | -0.0097 | -0.2921 | -7.30 | 7.30 | 747 |
| 4 | -0.0099 | -0.1152 | -5.04 | 5.06 | 542 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51841
- **Expected rows**: 51841
- **Missing rows**: 0
- **Forward-fill count**: 169
- **Forward-fill fraction**: 0.0032599679790127505
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0574 <= 0; recent PnL -1.2553% < 0
- **Objective score**: -0.05738013962105757
- **PnL %**: -1.2553381281976652
- **Trade count**: 148

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0622 <= 0; recent PnL -0.6592% < 0
- **Objective score**: -0.06215711710201002
- **PnL %**: -0.6591800853257348
- **Trade count**: 82

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2499 <= 0; recent PnL -0.5014% < 0
- **Objective score**: -0.24986153370420744
- **PnL %**: -0.501442939564227
- **Trade count**: 35

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.3753087539419787
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.5550, -0.4076 |
| sell_spread_base | -0.3638, -0.3913 |
| stop_loss | -0.3575, -0.3426 |
| take_profit | -0.3635, -0.3730 |
| executor_refresh_time | -0.3941, -0.3817 |
| cooldown_time | -0.3499, -0.3446 |
| total_amount_quote | -0.3611, -0.3525 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2522651986630328
- **Max CV**: 0.903757185368657
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1723 | 2.5754188752484675 | 4.266404008530739 | 3.224081429550226 |
| buy_spread_ratio | 0.1141 | 1.8324720482979187 | 2.5794453504990686 | 2.248049293045595 |
| sell_spread_base | 0.9038 | 0.2464765505309586 | 2.45080261402202 | 0.725345294305235 |
| sell_spread_ratio | 0.2879 | 1.3052934670027194 | 2.6438727145410583 | 1.8116792488585396 |
| buy_side_weight | 0.3240 | 0.200768259773259 | 0.5108622768625086 | 0.2837115962570714 |
| amount_skew | 0.2183 | 1.805689849494171 | 3.663701421007352 | 2.867077918374364 |
| stop_loss | 0.2156 | 0.011690608681532596 | 0.024055049198408337 | 0.017553238876583235 |
| take_profit | 0.0903 | 0.005211030864707715 | 0.006740812039905229 | 0.005845270843841189 |
| executor_refresh_time | 0.1953 | 7731.0 | 13466.0 | 11095.7 |
| cooldown_time | 0.1220 | 4700.0 | 6863.0 | 5869.7 |
| total_amount_quote | 0.1313 | 592.8396313522175 | 980.7522810335377 | 871.2844748286668 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Stop-Ship Checks

- dataset_audit: PASS
- runtime_sanity: PASS
- objective_not_degenerate: PASS
- stress_not_collapsed: PASS
- yaml_validates: PASS
- walkforward_robust: PASS
- walkforward_positive_majority: **FAIL**
- holdout_passed: **FAIL**
- holdout_no_collapse: PASS
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.05738013962105757 | FAIL |
| recent_pnl | >= 0 | -1.2553381281976652 | FAIL |
| recent_trades | >= 5 | 148 | PASS |
| worst_stress | > -10 | -0.356664233540615 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.017304070288167793 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.356664233540615 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.05738013962105757, pnl=-1.2553381281976652, trades=148, reason=recent objective score -0.0574 <= 0; recent PnL -1.2553% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.06215711710201002, pnl=-0.6591800853257348, trades=82, reason=recent objective score -0.0622 <= 0; recent PnL -0.6592% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.24986153370420744, pnl=-0.501442939564227, trades=35, reason=recent objective score -0.2499 <= 0; recent PnL -0.5014% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2522651986630328 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51841 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0574 <= 0; recent PnL -1.2553% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0622 <= 0; recent PnL -0.6592% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2499 <= 0; recent PnL -0.5014% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51841
- **Pre-release bars**: 43776
- **Dev bars**: 35021
- **Holdout bars**: 8755
- **Recent 28d bars**: 8065
- **Recent window start**: 1773229500

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T18:02:14.255375+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 6121
