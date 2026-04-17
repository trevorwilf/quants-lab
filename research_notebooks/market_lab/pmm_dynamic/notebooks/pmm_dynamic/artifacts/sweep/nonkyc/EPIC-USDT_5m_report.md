# PMM Dynamic Optimization Report: nonkyc_EPIC-USDT_5m_sweep_v1

Generated: 2026-04-09 19:38:05 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T19:38:05.887683+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 14479 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: EPIC-USDT
- **interval**: 5m
- **n_candles**: 35947
- **dataset_hash**: 3730db383564abd0f37c5e9aeb18e1b420896a0f255290c46ec7281c9e4bf7fa
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 101.57890899142507
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 1.602380014371322 |
| buy_n_levels | 7 |
| buy_side_weight | 0.7340449012392778 |
| buy_spread_base | 3.2393916835686323 |
| buy_spread_ratio | 1.3634895818008959 |
| cooldown_time | 2043 |
| executor_refresh_time | 5104 |
| macd_fast | 31 |
| macd_signal | 28 |
| macd_slow | 65 |
| natr_length | 39 |
| sell_n_levels | 2 |
| sell_spread_base | 3.428099152667101 |
| sell_spread_ratio | 1.9661735781898817 |
| stop_loss | 0.20600968977895948 |
| take_profit | 0.013192376163710834 |
| time_limit | 134775 |
| total_amount_quote | 101.57890899142507 |
| trailing_stop_activation | 0.01773392524994894 |
| trailing_stop_delta | 0.0015081992620705749 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 101.57890899142507 |
| Selected | 101.57890899142507 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: 132.4778
- **Net PnL (quote)**: 134.5695
- **Sharpe Ratio**: 5.8076
- **Max Drawdown %**: 14.1000
- **Profit Factor**: 3.294135865658399
- **Trade Count**: 562
- **Total Fees (quote)**: 13.5982
- **Maker Fees**: 5.8036
- **Taker Fees**: 7.7946
- **Fee Drag %**: 13.3868
- **TP Min-Notional Failures**: 497 :warning:
  > 497 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: 0.5741
- **PnL Component**: 0.8436
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.1057
- **Fee Drag Component**: -0.0669
- **Inventory Component**: -0.0941
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.1716**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | 5.03 | 5.61 | 1.52 | 54 | 0.0111 | n/a |
| 1 | 4.34 | 6.13 | 1.47 | 45 | 0.0046 | n/a |
| 2 | 1.01 | 0.82 | 8.81 | 77 | -0.1129 | n/a |
| 3 | -5.86 | -4.70 | 8.15 | 20 | -0.2870 | n/a |
| 4 | -1.82 | -3.20 | 3.71 | 35 | -0.2089 | n/a |

## Stress Test Results

Worst Scenario: **combined_adverse** (score: 0.4259)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | 125.66 | 5.59 | 13.70 | 0.5119 |
| fees_2x | 118.87 | 5.36 | 13.76 | 0.4458 |
| latency_plus1 | 132.94 | 5.85 | 14.10 | 0.5771 |
| latency_plus2 | 132.46 | 5.82 | 14.10 | 0.5748 |
| latency_plus3 | 133.37 | 5.82 | 14.10 | 0.5792 |
| low_liquidity | 124.27 | 5.63 | 14.22 | 0.5420 |
| very_low_liquidity | 101.67 | 5.00 | 12.62 | 0.4538 |
| high_slippage | 130.15 | 5.74 | 13.64 | 0.5661 |
| extreme_slippage | 126.62 | 5.64 | 13.65 | 0.5504 |
| combined_adverse | 107.37 | 5.06 | 14.31 | 0.4259 |
| spread_widen_10bps | 133.64 | 6.31 | 11.37 | 0.5953 |
| spread_widen_25bps | 136.88 | 6.36 | 11.46 | 0.6062 |
| thin_book | 104.06 | 5.65 | 12.08 | 0.4758 |
| very_thin_book | 82.61 | 4.07 | 7.17 | 0.4303 |
| entry_spread_stress | 137.93 | 6.42 | 11.40 | 0.6119 |
| combined_market_deterioration | 113.80 | 5.76 | 10.64 | 0.4892 |
| severe_adverse | 100.08 | 5.35 | 8.00 | 0.4449 |

## Holdout Validation

- **Holdout bars**: 5576
- **Regime**: low_vol_ranging
- **Volatility**: low_vol (NATR mean: 0.0092)
- **Trend**: ranging (efficiency: 0.0152)
- **Best holdout score**: -0.0788 (rank #0)
- **Collapse detected**: YES
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | 0.5000 | -0.0788 | 2.15 | 8.21 | 47 |
| 1 | 0.0482 | -0.0858 | 4.50 | 8.53 | 58 |
| 2 | 0.0445 | -0.1407 | 1.97 | 8.30 | 150 |
| 3 | 0.0402 | -0.1466 | 3.88 | 10.09 | 77 |
| 4 | 0.0395 | -0.2725 | -5.79 | 11.31 | 57 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 35947
- **Expected rows**: 35948
- **Missing rows**: 1
- **Forward-fill count**: 274
- **Forward-fill fraction**: 0.007622332878960692
- **Longest gap (seconds)**: 600

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.1498 <= 0; recent PnL -1.4215% < 0
- **Objective score**: -0.1498114211359598
- **PnL %**: -1.4214823977587083
- **Trade count**: 44

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1692 <= 0
- **Objective score**: -0.16915600598412536
- **PnL %**: 0.755912654196225
- **Trade count**: 11

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1901 <= 0
- **Objective score**: -0.19009691555547295
- **PnL %**: 0.3155717574075005
- **Trade count**: 8

## Sensitivity Analysis

- **Sensitivity penalty**: 0.0
- **Baseline score**: 0.5291951714500682
- **Sign flips**: 0
- **Collapse count**: 0
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | 0.6045, 0.6076 |
| sell_spread_base | 0.5446, 0.5694 |
| stop_loss | 0.5598, 0.5481 |
| take_profit | 0.5491, 0.5178 |
| executor_refresh_time | 0.5919, 0.5736 |
| cooldown_time | 0.6130, 0.5292 |
| total_amount_quote | 0.5353, 0.5520 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.34361623238346445
- **Max CV**: 0.7950101912028951
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, total_amount_quote
- **Scattered params**: sell_spread_base, executor_refresh_time, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0592 | 2.7239493364758154 | 3.29630253917741 | 3.1241638969928025 |
| buy_spread_ratio | 0.0502 | 1.207589245795049 | 1.3658549005922294 | 1.277200762959137 |
| sell_spread_base | 0.6001 | 0.683555471171841 | 5.6290667299427914 | 3.1034448076880903 |
| sell_spread_ratio | 0.1901 | 1.6978039518845875 | 2.975205182357768 | 2.4178326508273282 |
| buy_side_weight | 0.1104 | 0.5749295358313358 | 0.7996202028618218 | 0.7253418526561175 |
| amount_skew | 0.3741 | 1.2439814826651956 | 3.3244383124819517 | 1.8761229261027914 |
| stop_loss | 0.2778 | 0.08121706275396685 | 0.21984412953714122 | 0.17454752115394193 |
| take_profit | 0.4539 | 0.005868147986326452 | 0.025407133732366784 | 0.013172090137587597 |
| executor_refresh_time | 0.7950 | 389.0 | 6008.0 | 2850.6 |
| cooldown_time | 0.5887 | 501.0 | 3596.0 | 1821.2 |
| total_amount_quote | 0.2804 | 43.8092307192859 | 137.53482733960078 | 96.4426472664301 |

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
- walkforward_positive_majority: PASS
- holdout_passed: **FAIL**
- holdout_no_collapse: **FAIL**
- sensitivity_stable: PASS
- recent_28d_passed: **FAIL**
- frozen_parity: **FAIL**
- top_k_clustered: PASS
- taker_realism: PASS

> **WARNING**: One or more stop-ship checks FAILED.

### Gate Thresholds Detail

| Gate | Threshold | Actual | Status |
|---|---|---|---|
| recent_objective | > 0 | -0.1498114211359598 | FAIL |
| recent_pnl | >= 0 | -1.4214823977587083 | FAIL |
| recent_trades | >= 5 | 44 | PASS |
| worst_stress | > -10 | 0.42588572781729905 | PASS |
| sensitivity_penalty | < 0.50 | 0.0 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.0788141187738713 |
| walkforward | PASS | 5 folds |
| stress | PASS | worst=combined_adverse score=0.42588572781729905 |
| sensitivity | PASS | penalty=0.0 |
| recent_28d | FAIL | score=-0.1498114211359598, pnl=-1.4214823977587083, trades=44, reason=recent objective score -0.1498 <= 0; recent PnL -1.4215% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.16915600598412536, pnl=0.755912654196225, trades=11, reason=recent objective score -0.1692 <= 0 |
| recent_7d_info | FAIL | informational only; score=-0.19009691555547295, pnl=0.3155717574075005, trades=8, reason=recent objective score -0.1901 <= 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.34361623238346445 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 35947 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.1498 <= 0; recent PnL -1.4215% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.1692 <= 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1901 <= 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 35947
- **Pre-release bars**: 27883
- **Dev bars**: 22307
- **Holdout bars**: 5576
- **Recent 28d bars**: 8064
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T19:38:05.887683+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 14479
