# PMM Dynamic Optimization Report: nonkyc_POL-USDT_5m_sweep_v1

Generated: 2026-03-29 11:18:32 UTC

## Run Provenance

| Key | Value |
|-----|-------|
| notebook | jupyter |
| run_timestamp | 2026-03-29T11:18:32.017678+00:00 |
| n_jobs | 8 |
| objective_version | 2 |
| search_controller_compat | False |
| validation_controller_compat | True |
| trial_number | 5165 |

## Dataset Summary

- **connector**: nonkyc
- **trading_pair**: POL-USDT
- **interval**: 5m
- **n_candles**: 51913
- **dataset_hash**: 2a3c5e9e43142ca7d3b982e6590e939e727b1496d3c50b1f578de7eecf4367a7
- **n_trials_phase1**: 12000
- **n_candidates_stressed**: 75
- **total_amount_quote_search_min**: 25.0
- **total_amount_quote_search_max**: 1000.0
- **total_amount_quote_ideal**: 981.9333996964892
- **search_controller_compat**: False

## Best Parameters

| Parameter | Value |
|-----------|-------|
| amount_skew | 3.6468474937830035 |
| buy_n_levels | 5 |
| buy_side_weight | 0.21554104655892314 |
| buy_spread_base | 3.2433893678749426 |
| buy_spread_ratio | 2.989225743611146 |
| cooldown_time | 96 |
| executor_refresh_time | 11566 |
| macd_fast | 40 |
| macd_signal | 19 |
| macd_slow | 69 |
| natr_length | 49 |
| sell_n_levels | 7 |
| sell_spread_base | 4.950770648614658 |
| sell_spread_ratio | 1.4221782935087315 |
| stop_loss | 0.013435755322992576 |
| take_profit | 0.005087343968191534 |
| time_limit | 23874 |
| total_amount_quote | 981.9333996964892 |
| trailing_stop_activation | 0.06991897334780145 |
| trailing_stop_delta | 0.049430856479513556 |

## Capital/Budget Analysis

| Metric | Value |
|--------|-------|
| Search Min | 25.0 |
| Search Max | 1000.0 |
| Ideal | 981.9333996964892 |
| Selected | 981.9333996964892 |

> **WARNING**: Selected quote is within 5% of search maximum.

## Selected Candidate Single-Run Diagnostics

- **PnL %**: -2.4168
- **Net PnL (quote)**: -23.7310
- **Sharpe Ratio**: -7.4751
- **Max Drawdown %**: 2.4329
- **Profit Factor**: 0.38262071290855965
- **Trade Count**: 525
- **Total Fees (quote)**: 16.5713
- **Maker Fees**: 11.9231
- **Taker Fees**: 4.6483
- **Fee Drag %**: 1.6876

## Selected Candidate Single-Run Objective

- **Raw Score**: -0.0543
- **PnL Component**: -0.0245
- **Sharpe Component**: 0.0000
- **Drawdown Component**: -0.0182
- **Fee Drag Component**: -0.0084
- **Inventory Component**: -0.0031
- **Trade Count Penalty**: -0.0000
- **Rejected**: False

## Walk-Forward Results

Aggregate Score: **-0.0093**

| Fold | PnL % | Sharpe | Max DD % | Trades | Objective | Regime |
|------|-------|--------|----------|--------|-----------|--------|
| 0 | -0.20 | -4.68 | 0.33 | 54 | -0.0084 | n/a |
| 1 | -0.12 | -4.77 | 0.17 | 65 | -0.0064 | n/a |
| 2 | -0.20 | -9.13 | 0.24 | 58 | -0.0077 | n/a |
| 3 | -0.03 | -1.61 | 0.08 | 49 | -0.0085 | n/a |
| 4 | -0.58 | -10.15 | 0.59 | 57 | -0.0144 | n/a |
| 5 | -0.26 | -8.52 | 0.27 | 87 | -0.0088 | n/a |
| 6 | -0.14 | -6.48 | 0.19 | 79 | -0.0068 | n/a |
| 7 | -0.46 | -12.29 | 0.54 | 89 | -0.0130 | n/a |
| 8 | -0.09 | -3.78 | 0.11 | 62 | -0.0056 | n/a |

## Stress Test Results

Worst Scenario: **severe_adverse** (score: -0.1294)

| Scenario | PnL % | Sharpe | Max DD % | Objective |
|----------|-------|--------|----------|-----------|
| fees_1.5x | -3.26 | -9.80 | 3.27 | -0.0734 |
| fees_2x | -4.10 | -11.95 | 4.11 | -0.0928 |
| latency_plus1 | -2.39 | -7.40 | 2.41 | -0.0538 |
| latency_plus2 | -2.40 | -7.41 | 2.41 | -0.0539 |
| latency_plus3 | -2.46 | -7.60 | 2.47 | -0.0549 |
| low_liquidity | -2.82 | -3.71 | 2.87 | -0.0660 |
| very_low_liquidity | -2.63 | -0.85 | 4.06 | -0.0682 |
| high_slippage | -2.53 | -7.74 | 2.55 | -0.0564 |
| extreme_slippage | -2.77 | -8.23 | 2.79 | -0.0605 |
| combined_adverse | -3.94 | -5.13 | 3.98 | -0.0910 |
| spread_widen_10bps | -2.64 | -8.08 | 2.66 | -0.0583 |
| spread_widen_25bps | -4.59 | -7.36 | 4.63 | -0.0984 |
| thin_book | -3.11 | -1.92 | 3.13 | -0.0655 |
| very_thin_book | -2.74 | -0.86 | 4.06 | -0.0663 |
| entry_spread_stress | -3.74 | -6.70 | 3.78 | -0.0815 |
| combined_market_deterioration | -3.57 | -10.15 | 3.59 | -0.0783 |
| severe_adverse | -6.15 | -1.72 | 6.17 | -0.1294 |

## Holdout Validation

- **Holdout bars**: 8769
- **Regime**: high_vol_ranging
- **Volatility**: high_vol (NATR mean: 0.0037)
- **Trend**: ranging (efficiency: 0.0028)
- **Best holdout score**: -0.0085 (rank #1)
- **Collapse detected**: No
- **Holdout passed**: **NO**

| Rank | Dev Score | Holdout Score | PnL % | Max DD % | Trades |
|------|-----------|---------------|-------|----------|--------|
| 0 | -0.0918 | -0.0193 | -0.80 | 0.82 | 846 |
| 1 | -0.0060 | -0.0085 | -0.18 | 0.25 | 194 |
| 2 | -0.0060 | -0.0133 | -0.45 | 0.45 | 232 |
| 3 | -0.0062 | -0.0108 | -0.25 | 0.51 | 166 |
| 4 | -0.0063 | -0.0160 | -0.67 | 0.68 | 200 |

## Dataset Audit

- **Passed strict**: True
- **Total rows**: 51913
- **Expected rows**: 51913
- **Missing rows**: 0
- **Forward-fill count**: 156
- **Forward-fill fraction**: 0.0030050276424017103
- **Longest gap (seconds)**: 300

## Recent 28-Day Window

- **Passed**: False
- **Reason**: recent objective score -0.0199 <= 0; recent PnL -0.5205% < 0
- **Objective score**: -0.019885927364367766
- **PnL %**: -0.5205256638346819
- **Trade count**: 213

## Sensitivity Analysis

- **Sensitivity penalty**: 0.07142857142857142
- **Baseline score**: -0.08324953330642418
- **Sign flips**: 0
- **Collapse count**: 1
- **Perturbations**: 14
- **Rejected**: 0

| Parameter | Scores |
|-----------|--------|
| buy_spread_base | -0.0969, -0.1137 |
| sell_spread_base | -0.0841, -0.0885 |
| stop_loss | -0.0796, -0.0764 |
| take_profit | -0.0894, -0.0725 |
| executor_refresh_time | -0.1020, -0.1401 |
| cooldown_time | -0.0832, -0.0832 |
| total_amount_quote | -0.0863, -0.0830 |

## Top-K Clustering

- **K**: 10
- **Is clustered**: True
- **Mean CV**: 0.22289274873892975
- **Max CV**: 0.5935709693871789
- **Clustered params**: buy_spread_base, buy_spread_ratio, sell_spread_base, sell_spread_ratio, buy_side_weight, amount_skew, stop_loss, take_profit, executor_refresh_time, total_amount_quote
- **Scattered params**: cooldown_time

| Parameter | CV | Min | Max | Mean |
|-----------|-----|-----|-----|------|
| buy_spread_base | 0.0889 | 2.5503572499526133 | 3.4576414445504824 | 2.9471437391266493 |
| buy_spread_ratio | 0.0431 | 2.293079765380788 | 2.6206449084946497 | 2.439796228339463 |
| sell_spread_base | 0.2596 | 2.4274584334327054 | 5.257149222817595 | 3.812563874674974 |
| sell_spread_ratio | 0.1218 | 1.558917997659835 | 2.372551422627564 | 2.1075623137392796 |
| buy_side_weight | 0.3402 | 0.2026686938155623 | 0.4811321101105789 | 0.30115609586843295 |
| amount_skew | 0.1472 | 2.3073524091820086 | 3.609582168054244 | 3.029174550582453 |
| stop_loss | 0.1660 | 0.01012337632938166 | 0.015198437553546948 | 0.012435067175432453 |
| take_profit | 0.0949 | 0.005415808719187829 | 0.007196233536031816 | 0.006280252450025861 |
| executor_refresh_time | 0.4909 | 454.0 | 12564.0 | 7694.5 |
| cooldown_time | 0.5936 | 314.0 | 5301.0 | 2806.3 |
| total_amount_quote | 0.1056 | 689.7733161898875 | 992.5707370209757 | 866.6777228527778 |

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
| recent_objective | > 0 | -0.019885927364367766 | FAIL |
| recent_pnl | >= 0 | -0.5205256638346819 | FAIL |
| recent_trades | >= 5 | 213 | PASS |
| worst_stress | > -10 | -0.1293572281206217 | PASS |
| sensitivity_penalty | < 0.50 | 0.07142857142857142 | PASS |

## Validation Coverage

| Validation | Status | Detail |
|---|---|---|
| dataset_audit | PASS | strict audit passed |
| yaml_validation | PASS | mirror mode, 0 errors, 0 warnings |
| holdout | FAIL | score=-0.019337355093979804 |
| walkforward | PASS | 9 folds |
| stress | PASS | worst=severe_adverse score=-0.1293572281206217 |
| sensitivity | PASS | penalty=0.07142857142857142 |
| recent_28d | FAIL | score=-0.019885927364367766, pnl=-0.5205256638346819, trades=213, reason=recent objective score -0.0199 <= 0; recent PnL -0.5205% < 0 |
| frozen_parity | SKIPPED |  |
| long_parity | SKIPPED |  |
| clustering | PASS | mean_cv=0.22289274873892975 |

## Validation Execution Manifest

| Validation | Ran | Status | Dataset | Obj Version | Bars | Reason |
|---|---|---|---|---|---|---|
| dataset_audit | true | PASS | full | — | 51913 |  |
| yaml_validation | true | PASS | — | — | — |  |
| holdout | true | FAIL | pre_release_holdout | — | — |  |
| recent_28d | true | FAIL | recent_28d | — | — | recent objective score -0.0199 <= 0; recent PnL -0.5205% < 0 |
| sensitivity | true | FAIL | full | — | — |  |
| clustering | true | PASS | — | — | — |  |
| frozen_parity | false | NOT_RUN | — | — | — | not executed |
| long_parity | false | NOT_RUN | — | — | — | not executed |
| walkforward | true | FAIL | full | — | — |  |
| stress | true | FAIL | full | — | — |  |

## Dataset Slice Lineage

- **Full bars**: N/A
- **Pre-release bars**: N/A
- **Dev bars**: 35079
- **Holdout bars**: 8769
- **Recent 28d bars**: 8065

## Run Provenance

- **notebook**: jupyter
- **run_timestamp**: 2026-03-29T11:18:32.017678+00:00
- **n_jobs**: 8
- **objective_version**: 2
- **search_controller_compat**: False
- **validation_controller_compat**: True
- **trial_number**: 5165
