# PMM Dynamic Optimization Report: nonkyc_BTC-USDT_5m_sweep_v1

Generated: 2026-04-08 21:49:20 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-08T21:49:20.190417+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| trial_number | 13685 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: BTC-USDT
- **interval**: 5m
- **n_candles**: 51869
- **dataset_hash**: c47e5f65e3239b53417d88d2ab00743c1baa20c5f1be54902724ed81e88b192a
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 985.2304219147804
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.0475308208158283 |
| buy_n_levels | 4 |
| buy_side_weight | 0.26294858942884014 |
| buy_spread_base | 2.6089422106576907 |
| buy_spread_ratio | 2.538604660878055 |
| cooldown_time | 6247 |
| executor_refresh_time | 13379 |
| macd_fast | 24 |
| macd_signal | 18 |
| macd_slow | 27 |
| natr_length | 25 |
| sell_n_levels | 3 |
| sell_spread_base | 5.804454968792692 |
| sell_spread_ratio | 2.9848455051447225 |
| stop_loss | 0.09118539452315674 |
| take_profit | 0.005029336665079602 |
| time_limit | 60769 |
| total_amount_quote | 985.2304219147804 |
| trailing_stop_activation | 0.07341393834688492 |
| trailing_stop_delta | 0.005492235483343292 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 985.2304219147804 |
| Selected | 985.2304219147804 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.1310
- **Net PnL (quote)**: -11.1432
- **Sharpe Ratio**: -1.2174
- **Max Drawdown %**: 2.5878
- **Profit Factor**: 0.8890921626491869
- **Trade Count**: 580
- **Total Fees (quote)**: 14.3456
- **Maker Fees**: 11.7096
- **Taker Fees**: 2.6360
- **Fee Drag %**: 1.4561
- **TP Min-Notional Failures**: 724 :warning:
  > 724 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0504
- **PnL Component**: -0.0114
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0194
- **Fee Drag Component**: -0.0073
- **Inventory Component**: -0.0122
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0094**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.17 | -5.69 | 0.24 | 57 | -0.0058 | n/a |
| 1 | -0.19 | -7.46 | 0.22 | 48 | -0.0139 | n/a |
| 2 | -0.02 | -2.07 | 0.07 | 53 | -0.0029 | n/a |
| 3 | -0.02 | -1.31 | 0.08 | 52 | -0.0030 | n/a |
| 4 | -0.23 | -5.34 | 0.27 | 66 | -0.0385 | n/a |
| 5 | -0.38 | -8.75 | 0.39 | 71 | -0.0138 | n/a |
| 6 | -0.31 | -6.29 | 0.39 | 54 | -0.0134 | n/a |
| 7 | 0.01 | 0.40 | 0.11 | 63 | -0.0031 | n/a |
| 8 | -0.09 | -4.71 | 0.11 | 63 | -0.0072 | n/a |

## Stress Test Results

Worst Scenario: **spread_widen_25bps** (score: -0.1099)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -1.86 | -2.02 | 3.17 | -0.0658 |
| fees_2x | -2.59 | -2.84 | 3.75 | -0.0813 |
| latency_plus1 | -1.13 | -1.22 | 2.59 | -0.0504 |
| latency_plus2 | -0.95 | -1.03 | 2.34 | -0.0454 |
| latency_plus3 | -0.87 | -0.97 | 2.15 | -0.0439 |
| low_liquidity | -1.13 | -1.22 | 2.59 | -0.0504 |
| very_low_liquidity | -1.13 | -1.22 | 2.59 | -0.0504 |
| high_slippage | -1.20 | -1.29 | 2.64 | -0.0514 |
| extreme_slippage | -1.33 | -1.44 | 2.76 | -0.0537 |
| combined_adverse | -1.93 | -2.10 | 3.22 | -0.0669 |
| spread_widen_10bps | -1.31 | -1.48 | 2.43 | -0.0505 |
| spread_widen_25bps | -3.64 | -2.75 | 5.34 | -0.1099 |
| thin_book | -2.90 | -2.49 | 4.57 | -0.0919 |
| very_thin_book | -1.06 | -1.25 | 2.41 | -0.0424 |
| entry_spread_stress | -1.46 | -1.40 | 2.93 | -0.0571 |
| combined_market_deterioration | -4.01 | -5.86 | 4.41 | -0.0995 |
| severe_adverse | -2.74 | -3.09 | 3.67 | -0.0792 |

## Holdout Validation

- **Holdout bars**: 8760
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0024)
- **Trend**: ranging (efficiency: 0.0000)
- **Best holdout score**: -0.0106 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0801 | -0.0106 | -0.37 | 0.44 | 141 |
| 1 | -0.0057 | -0.0816 | -1.90 | 2.19 | 363 |
| 2 | -0.0061 | -0.0668 | -1.41 | 1.84 | 279 |
| 3 | -0.0062 | -0.1496 | -3.25 | 3.78 | 430 |
| 4 | -0.0064 | -0.1208 | -1.54 | 2.99 | 324 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51869
- **Expected rows**: 51869
- **Missing rows**: 0
- **Forward-fill count**: 276
- **Forward-fill fraction**: 0.005321097379937921
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0050 <= 0; recent PnL -0.1037% < 0
- **Objective score**: -0.005011349017206987
- **PnL %**: -0.10369003643356614
- **Trade count**: 116

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0073 <= 0; recent PnL -0.0966% < 0
- **Objective score**: -0.007268862602242076
- **PnL %**: -0.09657123163418546
- **Trade count**: 55

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.1023 <= 0; recent PnL -0.0156% < 0
- **Objective score**: -0.1023002087211426
- **PnL %**: -0.015572744937597657
- **Trade count**: 25

## Sensitivity Analysis

- **Sensitivity penalty**: 0.21428571428571427
- **Baseline score**: -0.06803404752434122
- **Sign flips**: 0
- **Collapse count**: 3
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1245, -0.1269 |
| sell_spread_base | -0.0637, -0.1099 |
| stop_loss | -0.0672, -0.0679 |
| take_profit | -0.0630, -0.0685 |
| executor_refresh_time | -0.0432, -0.0524 |
| cooldown_time | -0.0543, -0.0398 |
| total_amount_quote | -0.0678, -0.0680 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.320460251080608
- **Max CV**: 1.1790853105600803
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, stop_loss, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0734 | 2.2344259832895816 | 2.950481076279716 | 2.552037701799093 |
| buy_spread_ratio | 0.0442 | 2.3864996448541067 | 2.7188328813033023 | 2.5534965421048113 |
| sell_spread_base | 1.1791 | 0.24994212605963195 | 5.97805115819134 | 1.8738737315930216 |
| sell_spread_ratio | 0.2372 | 1.6959350412772682 | 2.9848455051447225 | 2.084702715265733 |
| buy_side_weight | 0.1891 | 0.2011531994544362 | 0.33684886055151164 | 0.23578619620527244 |
| amount_skew | 0.0801 | 2.438390603546568 | 3.138966149815571 | 2.807588084534335 |
| stop_loss | 0.6817 | 0.01941640887394618 | 0.20667796375311018 | 0.08269197321748112 |
| take_profit | 0.0304 | 0.005022385917086981 | 0.005487174808036934 | 0.005172842506135434 |
| executor_refresh_time | 0.1656 | 9286.0 | 14181.0 | 12143.0 |
| cooldown_time | 0.6983 | 687.0 | 6963.0 | 3379.4 |
| total_amount_quote | 0.1460 | 584.5842923158323 | 985.2304219147804 | 823.6853308112011 |

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
| recent_objective | > 0 | -0.005011349017206987 | FAIL |
| recent_pnl | >= 0 | -0.10369003643356614 | FAIL |
| recent_trades | >= 5 | 116 | PASS |
| worst_stress | > -10 | -0.10989758295054103 | PASS |
| sensitivity_penalty | < 0.50 | 0.21428571428571427 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.010623845094985028 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=spread_widen_25bps score=-0.10989758295054103 |
| sensitivity | PASS | penalty=0.21428571428571427 |
| recent_28d | FAIL | score=-0.005011349017206987, pnl=-0.10369003643356614, trades=116, reason=recent objective score -0.0050 <= 0; recent PnL -0.1037% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.007268862602242076, pnl=-0.09657123163418546, trades=55, reason=recent objective score -0.0073 <= 0; recent PnL -0.0966% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.1023002087211426, pnl=-0.015572744937597657, trades=25, reason=recent objective score -0.1023 <= 0; recent PnL -0.0156% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.320460251080608 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51869 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0050 <= 0; recent PnL -0.1037% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0073 <= 0; recent PnL -0.0966% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.1023 <= 0; recent PnL -0.0156% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 51869
- **Pre-release bars**: 43804
- **Dev bars**: 35044
- **Holdout bars**: 8760
- **Recent 28d bars**: 8065
- **Recent window start**: 1773251100

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-08T21:49:20.190417+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **trial_number**: 13685
