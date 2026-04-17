# PMM Dynamic Optimization Report: nonkyc_LTC-USDT_5m_sweep_v1

Generated: 2026-04-09 21:45:25 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-04-09T21:45:25.994467+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| refresh_close_mode | market_close |
| initial_base_balance | 0.0 |
| taker_probability | 0.1 |
| trial_number | 12657 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: LTC-USDT
- **interval**: 5m
- **n_candles**: 52059
- **dataset_hash**: 1ab1831c956a269880ca42f20972c79355dd918153a02a1f4f6ced9e477c2d9d
- **n_trials_phase1**: 15000
- **n_candidates_stressed**: 100
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 905.5386320558259
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.129665027992263 |
| buy_n_levels | 7 |
| buy_side_weight | 0.29658564689344713 |
| buy_spread_base | 1.9014826989246445 |
| buy_spread_ratio | 2.9230167972002437 |
| cooldown_time | 2903 |
| executor_refresh_time | 12577 |
| macd_fast | 16 |
| macd_signal | 24 |
| macd_slow | 51 |
| natr_length | 34 |
| sell_n_levels | 8 |
| sell_spread_base | 4.0756558092254 |
| sell_spread_ratio | 1.7116809963189763 |
| stop_loss | 0.012519554697073007 |
| take_profit | 0.005029351644315427 |
| time_limit | 119908 |
| total_amount_quote | 905.5386320558259 |
| trailing_stop_activation | 0.019880104307585342 |
| trailing_stop_delta | 0.0015142941619593767 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 905.5386320558259 |
| Selected | 905.5386320558259 |

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -1.9091
- **Net PnL (quote)**: -17.2876
- **Sharpe Ratio**: -5.7440
- **Max Drawdown %**: 2.0148
- **Profit Factor**: 0.5761971481231559
- **Trade Count**: 957
- **Total Fees (quote)**: 19.7031
- **Maker Fees**: 15.2255
- **Taker Fees**: 4.4777
- **Fee Drag %**: 2.1758
- **TP Min-Notional Failures**: 1910 :warning:
  > 1910 take-profit exits were blocked by min-notional constraints. This mirrors live behavior where TP limit orders below min-notional are deferred.

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0505
- **PnL Component**: -0.0193
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0151
- **Fee Drag Component**: -0.0109
- **Inventory Component**: -0.0051
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0080**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.19 | -7.28 | 0.26 | 90 | -0.0066 | n/a |
| 1 | -0.33 | -10.15 | 0.36 | 84 | -0.0091 | n/a |
| 2 | -0.19 | -12.39 | 0.21 | 75 | -0.0061 | n/a |
| 3 | -0.31 | -11.71 | 0.33 | 83 | -0.0085 | n/a |
| 4 | 0.32 | 2.79 | 0.23 | 86 | -0.0018 | n/a |
| 5 | -0.34 | -10.41 | 0.35 | 80 | -0.0089 | n/a |
| 6 | -0.39 | -11.06 | 0.42 | 85 | -0.0137 | n/a |
| 7 | -0.25 | -10.36 | 0.26 | 69 | -0.0071 | n/a |
| 8 | -0.11 | -4.97 | 0.12 | 71 | -0.0045 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1454)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.00 | -8.91 | 3.05 | -0.0749 |
| fees_2x | -4.08 | -11.95 | 4.12 | -0.0996 |
| latency_plus1 | -2.02 | -6.07 | 2.13 | -0.0526 |
| latency_plus2 | -2.42 | -6.71 | 2.59 | -0.0606 |
| latency_plus3 | -2.60 | -7.15 | 2.78 | -0.0639 |
| low_liquidity | -2.28 | -6.09 | 2.46 | -0.0591 |
| very_low_liquidity | -2.30 | -6.58 | 2.46 | -0.0580 |
| high_slippage | -2.03 | -6.09 | 2.13 | -0.0526 |
| extreme_slippage | -2.28 | -6.78 | 2.36 | -0.0569 |
| combined_adverse | -3.63 | -9.55 | 3.75 | -0.0886 |
| spread_widen_10bps | -2.26 | -8.06 | 2.31 | -0.0557 |
| spread_widen_25bps | -3.56 | -7.10 | 3.72 | -0.0853 |
| thin_book | -3.58 | -10.68 | 3.60 | -0.0779 |
| very_thin_book | -2.66 | -7.94 | 2.67 | -0.0552 |
| entry_spread_stress | -3.36 | -7.69 | 3.55 | -0.0810 |
| combined_market_deterioration | -4.68 | -12.24 | 4.75 | -0.1049 |
| severe_adverse | -6.80 | -16.44 | 6.81 | -0.1454 |

## Holdout Validation

- **Holdout bars**: 8798
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0026)
- **Trend**: ranging (efficiency: 0.0003)
- **Best holdout score**: -0.0162 (rank #0)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0979 | -0.0162 | -0.67 | 0.68 | 173 |
| 1 | -0.0054 | -0.0223 | -0.83 | 0.86 | 316 |
| 2 | -0.0054 | -0.1024 | -2.17 | 2.31 | 542 |
| 3 | -0.0056 | -0.0241 | -0.86 | 0.88 | 364 |
| 4 | -0.0058 | -0.0335 | -1.39 | 1.43 | 322 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 52059
- **Expected rows**: 52059
- **Missing rows**: 0
- **Forward-fill count**: 689
- **Forward-fill fraction**: 0.013234983384237115
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0078 <= 0; recent PnL -0.2559% < 0
- **Objective score**: -0.007821314104422513
- **PnL %**: -0.25586748067496146
- **Trade count**: 128

## Recent 14-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0046 <= 0; recent PnL -0.1103% < 0
- **Objective score**: -0.004643179669050278
- **PnL %**: -0.11034127472889475
- **Trade count**: 61

## Recent 7-Day Window (Informational Only)

> **Informational only** — this section does not affect stop-ship gating, export eligibility, or validated YAML promotion.

- **Passed**: False
- **Reason**: recent objective score -0.0944 <= 0; recent PnL -0.0221% < 0
- **Objective score**: -0.09443084144616404
- **PnL %**: -0.022070917563046678
- **Trade count**: 27

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.07546117719292189
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.1865, -0.0942 |
| sell_spread_base | -0.0747, -0.0881 |
| stop_loss | -0.0899, -0.0984 |
| take_profit | -0.0777, -0.0665 |
| executor_refresh_time | -0.0759, -0.0738 |
| cooldown_time | -0.0776, -0.0909 |
| total_amount_quote | -0.0869, -0.1040 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.33295386763935725
- **Max CV**: 0.9354271385360172
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: sell_spread_base, cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.1513 | 1.9492442291857108 | 3.234416944312142 | 2.7611348703777816 |
| buy_spread_ratio | 0.0506 | 2.334866396457388 | 2.7640690181731604 | 2.48262354825164 |
| sell_spread_base | 0.8556 | 0.21578170192461807 | 3.5022023043934767 | 1.2088506475992098 |
| sell_spread_ratio | 0.3276 | 1.3118303556129034 | 2.973168726773242 | 1.8633072321475694 |
| buy_side_weight | 0.2155 | 0.20799804105258085 | 0.41021365167958374 | 0.32548714718298527 |
| amount_skew | 0.1548 | 2.5524183857584797 | 3.888956885521103 | 3.2040531365990157 |
| stop_loss | 0.3887 | 0.010357934475404874 | 0.02681420668340681 | 0.01492086813373499 |
| take_profit | 0.3606 | 0.005241357523123715 | 0.012603671032882048 | 0.0062742212135394205 |
| executor_refresh_time | 0.1228 | 9615.0 | 14347.0 | 12450.0 |
| cooldown_time | 0.9354 | 123.0 | 4133.0 | 1581.7 |
| total_amount_quote | 0.0994 | 712.0724319649623 | 995.0782268480594 | 904.9164915907447 |

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
| recent_objective | > 0 | -0.007821314104422513 | FAIL |
| recent_pnl | >= 0 | -0.25586748067496146 | FAIL |
| recent_trades | >= 5 | 128 | PASS |
| worst_stress | > -10 | -0.14536736077791365 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.016211246434780568 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.14536736077791365 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.007821314104422513, pnl=-0.25586748067496146, trades=128, reason=recent objective score -0.0078 <= 0; recent PnL -0.2559% < 0 |
| recent_14d_info | FAIL | informational only; score=-0.004643179669050278, pnl=-0.11034127472889475, trades=61, reason=recent objective score -0.0046 <= 0; recent PnL -0.1103% < 0 |
| recent_7d_info | FAIL | informational only; score=-0.09443084144616404, pnl=-0.022070917563046678, trades=27, reason=recent objective score -0.0944 <= 0; recent PnL -0.0221% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.33295386763935725 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 52059 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0078 <= 0; recent PnL -0.2559% < 0 |
| recent_14d_info | true | FAIL | recent_14d_info | — | — | recent objective score -0.0046 <= 0; recent PnL -0.1103% < 0 |
| recent_7d_info | true | FAIL | recent_7d_info | — | — | recent objective score -0.0944 <= 0; recent PnL -0.0221% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: 52059
- **Pre-release bars**: 43994
- **Dev bars**: 35196
- **Holdout bars**: 8798
- **Recent 28d bars**: 8065
- **Recent window start**: 1773338400

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-04-09T21:45:25.994467+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **refresh_close_mode**: market_close
- **initial_base_balance**: 0.0
- **taker_probability**: 0.1
- **trial_number**: 12657
