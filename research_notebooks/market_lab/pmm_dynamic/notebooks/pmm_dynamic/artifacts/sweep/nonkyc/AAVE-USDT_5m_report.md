# PMM Dynamic Optimization Report: nonkyc_AAVE-USDT_5m_sweep_v1

Generated: 2026-04-09 14:08:12 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T14:08:12.924411+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 13058 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: AAVE-USDT
- **interval**: 5m
- **n_candles**: 52002
- **dataset_hash**: 76ece0c9e5d6a36abc70db47a14731532e6f7c2ace9f5fb1b471fbc4fda4f9c6
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 885.9805598772806
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.6255645577255322 |
| buy_n_levels | 8 |
| buy_side_weight | 0.24963354482525085 |
| buy_spread_base | 4.953269868952142 |
| buy_spread_ratio | 1.6817554282703513 |
| cooldown_time | 5253 |
| executor_refresh_time | 7272 |
| macd_fast | 27 |
| macd_signal | 29 |
| macd_slow | 29 |
| natr_length | 21 |
| sell_n_levels | 5 |
| sell_spread_base | 5.066214538992549 |
| sell_spread_ratio | 1.3470211059331136 |
| stop_loss | 0.012323927385056008 |
| take_profit | 0.005218536853374384 |
| time_limit | 59640 |
| total_amount_quote | 885.9805598772806 |
| trailing_stop_activation | 0.009367767806121016 |
| trailing_stop_delta | 0.0013966236030773084 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 885.9805598772806 |
| Selected | 885.9805598772806 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -6.1863
- **Net PnL (quote)**: -54.8090
- **Sharpe Ratio**: -7.2433
- **Max Drawdown %**: 6.5121
- **Profit Factor**: 0.4858370485312172
- **Trade Count**: 1061
- **Total Fees (quote)**: 32.4412
- **Maker Fees**: 20.2466
- **Taker Fees**: 12.1946
- **Fee Drag %**: 3.6616
- **TP Min-Notional Failures**: 1298 :warning:
  > 1298 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.1442
- **PnL Component**: -0.0639
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0488
- **Fee Drag Component**: -0.0183
- **Inventory Component**: -0.0130
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0144**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.29 | -10.30 | 0.34 | 57 | -0.0103 | n/a |
| 1 | -0.38 | -12.69 | 0.40 | 45 | -0.0318 | n/a |
| 2 | -0.68 | -6.79 | 0.69 | 49 | -0.1160 | n/a |
| 3 | -0.13 | -5.60 | 0.14 | 57 | -0.0073 | n/a |
| 4 | -0.38 | -10.71 | 0.43 | 62 | -0.0126 | n/a |
| 5 | -0.21 | -6.33 | 0.23 | 61 | -0.0090 | n/a |
| 6 | -0.41 | -9.97 | 0.47 | 57 | -0.0128 | n/a |
| 7 | -0.38 | -11.65 | 0.41 | 62 | -0.0121 | n/a |
| 8 | -1.11 | -23.02 | 1.13 | 57 | -0.2249 | n/a |

## Stress Test Results

Worst Scenario: **fees_2x** (score: -0.2287)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -8.02 | -9.27 | 8.25 | -0.1862 |
| fees_2x | -9.85 | -11.23 | 9.99 | -0.2287 |
| latency_plus1 | -6.52 | -7.64 | 6.84 | -0.1496 |
| latency_plus2 | -5.13 | -8.71 | 5.36 | -0.1169 |
| latency_plus3 | -5.09 | -8.41 | 5.32 | -0.1165 |
| low_liquidity | -4.71 | -11.02 | 4.76 | -0.1039 |
| very_low_liquidity | -5.11 | -9.99 | 5.27 | -0.1141 |
| high_slippage | -6.53 | -7.63 | 6.84 | -0.1503 |
| extreme_slippage | -7.22 | -8.39 | 7.49 | -0.1627 |
| combined_adverse | -6.32 | -14.30 | 6.35 | -0.1394 |
| spread_widen_10bps | -8.08 | -7.38 | 8.54 | -0.1876 |
| spread_widen_25bps | -4.01 | -10.31 | 4.36 | -0.0919 |
| thin_book | -4.16 | -10.83 | 4.29 | -0.0900 |
| very_thin_book | -3.58 | -9.79 | 3.63 | -0.1680 |
| entry_spread_stress | -3.74 | -10.02 | 3.79 | -0.0845 |
| combined_market_deterioration | -5.64 | -13.77 | 5.68 | -0.1231 |
| severe_adverse | -7.25 | -13.90 | 7.27 | -0.2206 |

## Holdout Validation

- **Holdout bars**: 8787
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0031)
- **Trend**: ranging (efficiency: 0.0010)
- **Best holdout score**: -0.0228 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.1864 | -0.0228 | -0.90 | 0.94 | 129 |
| 1 | -0.0084 | -0.0652 | -2.74 | 2.77 | 524 |
| 2 | -0.0104 | -0.0511 | -2.09 | 2.12 | 411 |
| 3 | -0.0110 | -0.1026 | -4.54 | 4.57 | 631 |
| 4 | -0.0110 | -0.1100 | -4.92 | 4.96 | 517 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52002
- **Expected rows**: 52002
- **Missing rows**: 0
- **Forward-fill count**: 169
- **Forward-fill fraction**: 0.0032498750048075074
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.2286 <= 0; recent PnL -1.7060% < 0
- **Objective score**: -0.22857709334189838
- **PnL %**: -1.7059508214200678
- **Trade count**: 116

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1420 <= 0; recent PnL -0.6608% < 0
- **Objective score**: -0.14197722875881083
- **PnL %**: -0.6607982986984723
- **Trade count**: 62

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.2722 <= 0; recent PnL -0.5431% < 0
- **Objective score**: -0.2722099094690222
- **PnL %**: -0.5431152358724393
- **Trade count**: 36

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: -0.26969065081296895
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1743, -0.2544 |
| sell_spread_base | -0.1732, -0.2469 |
| stop_loss | -0.2599, -0.2607 |
| take_profit | -0.2862, -0.2124 |
| executor_refresh_time | -0.1577, -0.1966 |
| cooldown_time | -0.2663, -0.1723 |
| total_amount_quote | -0.2628, -0.1530 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.2726462958812098
- **Max CV**: 0.7535177294425167
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, executor_refresh_time, cooldown_time, total_amount_quote
- **Scattered params**: sell_spread_base, take_profit

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1840 | 2.821044462937967 | 5.825865581692527 | 4.1225262394735065 |
| buy_spread_ratio | 0.1335 | 1.2690568367187833 | 2.229296652921844 | 1.8117730809533554 |
| sell_spread_base | 0.7535 | 0.6196281383667968 | 4.34509405742508 | 1.7272798311759385 |
| sell_spread_ratio | 0.3396 | 1.2391054831533908 | 2.7058232319234707 | 1.8516589626181812 |
| buy_side_weight | 0.0910 | 0.2085529012895348 | 0.2802318857201154 | 0.22755458880463308 |
| amount_skew | 0.1974 | 1.3408191550743036 | 2.724992947287576 | 2.064620378216905 |
| stop_loss | 0.3098 | 0.012022917475813716 | 0.029788899243112683 | 0.020083849262717023 |
| take_profit | 0.5955 | 0.005054419667790468 | 0.019825961806862556 | 0.007406762073036923 |
| executor_refresh_time | 0.2216 | 6449.0 | 14031.0 | 10866.2 |
| cooldown_time | 0.0840 | 5243.0 | 7076.0 | 6152.3 |
| total_amount_quote | 0.0894 | 731.4365942175694 | 998.5869502541208 | 915.0974135626 |

## YAML Validation

- **Valid**: True
- **Mode**: mirror
- **Errors**: 0
- **Warnings**: 0

## Execution Realism Assumptions

- **taker_probability**: 0.1
- **supports_post_only**: False
- **connector**: nonkyc
- **fill_participation_rate**: 0.1
- **latency_bars**: 1
- **slippage_bps**: 5.0
- **touch_through**: False
- **maker_fill_probability**: 1.0
- **refresh_close_mode**: market_close

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
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.22857709334189838 | FAIL |
| recent_pnl | >= 0 | -1.7059508214200678 | FAIL |
| recent_trades | >= 5 | 116 | PASS |
| worst_stress | > -10 | -0.22868068959700738 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.022823108793043948 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=fees_2x score=-0.22868068959700738 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.22857709334189838, pnl=-1.7059508214200678, trades=116, reason=recent objective score -0.2286 <= 0; recent PnL -1.7060% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.14197722875881083, pnl=-0.6607982986984723, trades=62, reason=recent objective score -0.1420 <= 0; recent PnL -0.6608% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.2722099094690222, pnl=-0.5431152358724393, trades=36, reason=recent objective score -0.2722 <= 0; recent PnL -0.5431% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.2726462958812098 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52002 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.2286 <= 0; recent PnL -1.7060% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1420 <= 0; recent PnL -0.6608% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.2722 <= 0; recent PnL -0.5431% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52002
- **Pre-release bars**: 43937
- **Dev bars**: 35150
- **Holdout bars**: 8787
- **Recent 28d bars**: 8065
- **Recent window start**: 1773321300

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T14:08:12.924411+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 13058
